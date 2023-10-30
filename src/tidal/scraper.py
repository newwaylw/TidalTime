import datetime as dt
import http
import logging
import random
import re
import urllib
import urllib.request
from typing import Iterable, List, NewType, Optional, Tuple

from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from tidal.constant import USER_AGENT_LIST
from tidal.tide_dto import DailyTideRecord, Tide, TideLocation, TideType

logger = logging.getLogger(__name__)

URL = NewType("URL", str)


class BBCTideScraper:
    def __init__(self, url: URL):
        self.url = url

    @retry(
        stop=stop_after_attempt(1),
        wait=wait_exponential(multiplier=2, min=2, max=32),
    )
    def download_tidal_info(
        self, location: TideLocation
    ) -> Tuple[TideLocation, Optional[Iterable[DailyTideRecord]]]:
        target_url = self.url + location.area_id + "/" + location.port_id
        try:
            req = urllib.request.Request(
                target_url,
                data=None,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": f"{random.choice(USER_AGENT_LIST)}",
                },
            )
            html = urllib.request.urlopen(req)
            soup = BeautifulSoup(html, features="html.parser")
            table_tag = "table.wr-c-tide-extremes"
            tables = soup.select(table_tag)

            if len(tables) == 0:
                raise ValueError(
                    f"Unable to parse bbc tide table {table_tag},"
                    f"please check if {self.url} layout changed."
                )

            logging.info(f"{len(tables)} days predictions found for {location}")

            # TODO: using system's date may cause problem due to time zones?
            today = dt.datetime.utcnow()
            multiday_records: List[DailyTideRecord] = list()

            # each table contains tide prediction for 1 day starting 'today'
            for day_offset, table in enumerate(tables):
                row_text = table.select_one("caption").text
                logging.debug(f"{row_text}")

                types = [
                    [td.text for td in row.find_all("th")] for row in table.select("tr")
                ]
                data = [
                    [td.text for td in row.find_all("td")]
                    for row in table.select("tr")[1:]
                ]
                _, time, height = types.pop(0)
                high_low = [x[0] for x in types]
                logging.debug(f"{len(high_low)} {row_text}")
                # convert BST to UTC
                time_offset = 1 if "BST" in time else 0
                tides = list()
                for tide_type, (time_str, height) in zip(high_low, data):
                    # this could happen when tides within a day crosses BST/GMT
                    if "BST" in time_str:
                        time_offset = 1
                        time_str = re.sub(r"\s+BST", "", time_str)
                    elif "GMT" in time_str:
                        time_offset = 0
                        time_str = re.sub(r"\s+GMT", "", time_str)

                    tide_time = dt.datetime.strptime(time_str, "%H:%M").time()
                    new_datetime = dt.datetime.combine(
                        today + dt.timedelta(days=day_offset), tide_time
                    ) - dt.timedelta(hours=time_offset)
                    tide = Tide(
                        TideType(tide_type),
                        utc_datetime=new_datetime.replace(),
                        height=float(height),
                    )
                    tides.append(tide)

                multiday_records.append(DailyTideRecord(location=location, tides=tides))

            return location, multiday_records

        except urllib.error.HTTPError as e:
            logging.error(
                f"{target_url} not found, please check if the area/port id is correct"
            )
            return location, None
        except http.client.IncompleteRead as ine:
            logging.error(str(ine))
            return location, None
        except ValueError as ve:
            logging.error(str(ve))
            return location, None
