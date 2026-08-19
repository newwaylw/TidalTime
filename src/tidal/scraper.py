import asyncio
import datetime as dt
import logging
import random
import re
from typing import List, NewType, Optional, Tuple
from urllib.parse import urljoin

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

    def _parse_day_table(self, html: str, day: dt.date, page_url: str) -> List[Tide]:
        """Parse a single day's tide table out of one fetched page.

        Raises ValueError if the expected table markup isn't found, so the
        caller can decide whether to skip that one day or bail out entirely.
        """
        soup = BeautifulSoup(html, features="lxml")
        # BBC's page renders a single table (just the day the URL asked for),
        # not one <table> per day, and it no longer carries the old
        # "wr-c-tide-extremes" class. data-testid is the most stable hook
        # since the ssrcss-* class names are auto-hashed per deploy.
        table_tag = 'table[data-testid="sport-table"]'
        table = soup.select_one(table_tag)

        if table is None:
            raise ValueError(
                f"Unable to parse bbc tide table {table_tag}, "
                f"please check if {self.url} layout changed."
            )

        header_cells = table.select_one("thead tr").find_all("th")
        if len(header_cells) < 2:
            raise ValueError(f"Unexpected header row for {page_url}: {header_cells}")
        time_header = header_cells[1].get_text(strip=True)
        time_offset = 1 if "BST" in time_header else 0

        tides: List[Tide] = []

        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            # Each <td> wraps its value in a <div value="..."> - use that
            # instead of get_text(), which would also pick up the
            # accompanying visually-hidden accessibility text (e.g. "3 hours
            # 10 minutes") and mangle the value.
            cell_values = [c.find("div") for c in cells]
            if any(c is None or c.get("value") is None for c in cell_values):
                logger.error(f"Unexpected row structure for {page_url}: {row}")
                continue
            tide_type, time_str, height = (c["value"] for c in cell_values)

            # Skip the "Current tide" row - it's not a real extreme and
            # isn't a valid TideType.
            if tide_type not in ("High", "Low"):
                continue

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
                new_datetime = dt.datetime.combine(day, tide_time) - dt.timedelta(
                    hours=current_time_offset
                )
                tides.append(Tide(
                    TideType(tide_type),
                    utc_datetime=new_datetime,
                    height=float(height),
                ))
            except ValueError as e:
                logger.error(f"Failed to parse time: {clean_time_str}, error: {e}")
                continue

        return tides

    async def download_tidal_info(
        self,
        session: aiohttp.ClientSession,
        location: TideLocation,
        today: dt.datetime,
    ) -> Tuple[TideLocation, Optional[List[DailyTideRecord]]]:
        target_url = self.url + location.area_id + "/" + location.port_id
        try:
            today_html = await self._fetch(session, target_url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status} for {target_url}")
            return location, None
        except aiohttp.ClientError as e:
            logger.error(f"Network error for {target_url}: {e}")
            return location, None

        try:
            # The date picker at the top of the page links to today plus the
            # next 6 days via "?selectedDate=YYYY-MM-DD". Follow those to
            # pull the full 7-day forecast instead of just today's table.
            soup = BeautifulSoup(today_html, features="lxml")
            date_links = soup.select('a[class*="DateLink"]')
            if not date_links:
                raise ValueError(
                    f"Unable to find date picker links, please check if "
                    f"{self.url} layout changed."
                )

            day_urls: List[Tuple[dt.date, str]] = []
            for a in date_links:
                href = a.get("href")
                if not href:
                    continue
                match = re.search(r"selectedDate=(\d{4}-\d{2}-\d{2})", href)
                if not match:
                    continue
                day_date = dt.datetime.strptime(match.group(1), "%Y-%m-%d").date()
                day_urls.append((day_date, urljoin(target_url, href)))

            if not day_urls:
                raise ValueError(
                    f"Unable to parse date picker links, please check if "
                    f"{self.url} layout changed."
                )

        except ValueError as ve:
            logger.error(f"Value error for {target_url}: {ve}")
            return location, None

        # Reuse the page we already fetched for "today" instead of hitting
        # the network again for the same URL.
        today_date = today.date()
        day_htmls: List[Tuple[dt.date, str]] = []
        fetch_targets: List[Tuple[dt.date, str]] = []
        for day_date, day_url in day_urls:
            if day_date == today_date:
                day_htmls.append((day_date, today_html))
            else:
                fetch_targets.append((day_date, day_url))

        if fetch_targets:
            fetched = await asyncio.gather(
                *(self._fetch(session, day_url) for _, day_url in fetch_targets),
                return_exceptions=True,
            )
            for (day_date, day_url), result in zip(fetch_targets, fetched):
                if isinstance(result, BaseException):
                    logger.error(f"Failed to fetch tides for {day_date} at {day_url}: {result}")
                    continue
                day_htmls.append((day_date, result))

        # Keep chronological order regardless of which request finished first.
        day_htmls.sort(key=lambda pair: pair[0])

        multiday_records: List[DailyTideRecord] = []
        for day_date, day_html in day_htmls:
            day_url = self.url + location.area_id + "/" + location.port_id + f"?selectedDate={day_date}"
            try:
                tides = self._parse_day_table(day_html, day_date, day_url)
            except ValueError as ve:
                logger.error(f"Value error for {day_url}: {ve}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for {day_url}: {e}")
                continue
            multiday_records.append(DailyTideRecord(location=location, tides=tides))

        logger.info(f"{len(multiday_records)} days predictions found for {location}")

        if not multiday_records:
            return location, None

        return location, multiday_records
