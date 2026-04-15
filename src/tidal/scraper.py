import asyncio
import datetime as dt
import logging
import random
import re
from typing import List, NewType, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from tidal.constant import USER_AGENT_LIST
from tidal.tide_dto import DailyTideRecord, Tide, TideLocation, TideType

logger = logging.getLogger(__name__)

URL = NewType("URL", str)

# Pre-compiled once at module level
_TIME_RE = re.compile(r".*(\d{2}:\d{2}).*")


class BBCTideScraper:
    def __init__(self, url: URL):
        self.url = url

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        retry=retry_if_exception_type(aiohttp.ClientError),
        reraise=True,
    )
    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        headers = {"User-Agent": random.choice(USER_AGENT_LIST)}
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    async def download_tidal_info(
        self,
        session: aiohttp.ClientSession,
        location: TideLocation,
        today: dt.datetime,
    ) -> Tuple[TideLocation, Optional[List[DailyTideRecord]]]:
        target_url = self.url + location.area_id + "/" + location.port_id
        try:
            html = await self._fetch(session, target_url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status} for {target_url}")
            return location, None
        except aiohttp.ClientError as e:
            logger.error(f"Network error for {target_url}: {e}")
            return location, None

        try:
            soup = BeautifulSoup(html, features="lxml")
            table_tag = "table.wr-c-tide-extremes"
            tables = soup.select(table_tag)

            if not tables:
                raise ValueError(
                    f"Unable to parse bbc tide table {table_tag}, "
                    f"please check if {self.url} layout changed."
                )

            logger.info(f"{len(tables)} days predictions found for {location}")

            multiday_records: List[DailyTideRecord] = []

            for day_offset, table in enumerate(tables):
                row_text = table.select_one("caption").text
                logger.debug(row_text)

                types = [
                    [td.text for td in row.find_all("th")] for row in table.select("tr")
                ]
                data = [
                    [td.text for td in row.find_all("td")]
                    for row in table.select("tr")[1:]
                ]
                _, time_header, _ = types.pop(0)
                high_low = [x[0] for x in types]

                time_offset = 1 if "BST" in time_header else 0
                tides = []

                for tide_type, (time_str, height) in zip(high_low, data):
                    current_time_offset = time_offset
                    clean_time_str = time_str.strip()

                    if "BST" in clean_time_str:
                        current_time_offset = 1
                    elif "GMT" in clean_time_str:
                        current_time_offset = 0

                    match = _TIME_RE.match(clean_time_str)
                    if not match:
                        logger.error(f"Failed to parse time: {clean_time_str}")
                        continue

                    try:
                        tide_time = dt.datetime.strptime(match.group(1), "%H:%M").time()
                        new_datetime = dt.datetime.combine(
                            today + dt.timedelta(days=day_offset), tide_time
                        ) - dt.timedelta(hours=current_time_offset)
                        tides.append(Tide(
                            TideType(tide_type),
                            utc_datetime=new_datetime,
                            height=float(height),
                        ))
                    except ValueError as e:
                        logger.error(f"Failed to parse time: {clean_time_str}, error: {e}")
                        continue

                multiday_records.append(DailyTideRecord(location=location, tides=tides))

            return location, multiday_records

        except ValueError as ve:
            logger.error(f"Value error for {target_url}: {ve}")
            return location, None
        except Exception as e:
            logger.error(f"Unexpected error for {target_url}: {e}")
            return location, None
