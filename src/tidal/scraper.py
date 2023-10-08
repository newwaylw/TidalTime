import datetime as dt
import http
import logging
import random
import urllib
import urllib.request
from typing import Iterable
from urllib.request import urlopen

from bs4 import BeautifulSoup

from tidal.tide import AreaID, DailyTideRecord, PortID, Tide, TideLocation, TideType

USER_AGENT_LIST = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
]

logging.basicConfig(
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%d-%m-%Y:%H:%M:%S",
    level="DEBUG",
)


class BBCTideScraper:
    def __init__(self, url: str):
        self.url = url

    def get_tidal_info(self, location: TideLocation) -> Iterable[DailyTideRecord]:
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
            tables = soup.select("table.wr-c-tide-extremes")

            logging.info(f"{len(tables)} days predictions found for {location} ")

            # using system's date may cause problem due to time zones?
            today = dt.datetime.utcnow()

            # each table contains tide prediction for 1 day starting 'today'
            for day_offset, table in enumerate(tables):
                row_text = table.select_one("caption").text
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
                # BST or UTC ?
                time_offset = 1 if "BST" in time else 0
                tides = list()
                for tide_type, (time_str, height) in zip(high_low, data):
                    tide_time = dt.datetime.strptime(time_str, "%H:%M").time()
                    new_datetime = dt.datetime.combine(
                        today + dt.timedelta(days=day_offset), tide_time
                    ) - dt.timedelta(hours=time_offset)
                    tide = Tide(
                        TideType(tide_type),
                        utc_date_time=new_datetime.replace(),
                        height=float(height),
                    )
                    tides.append(tide)
                yield DailyTideRecord(location=location, tides=tides)
        except urllib.error.HTTPError as e:
            logging.error(f"{target_url} not found")
            raise e
        except http.client.IncompleteRead as ine:
            logging.error(str(ine))
            raise ine


if __name__ == "__main__":
    scrapper = BBCTideScraper(
        "https://www.bbc.co.uk/weather/coast-and-sea/tide-tables/"
    )
    location = TideLocation(name="Ramsgate", area_id=AreaID("9"), port_id=PortID("102"))
    # json_store = JSONStore()
    for record in scrapper.get_tidal_info(location):
        print(record)
