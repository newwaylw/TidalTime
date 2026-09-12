import datetime as dt
import json
import logging
import random
import re
from typing import List, NewType, Optional, Tuple

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from tidal.constant import USER_AGENT_LIST
from tidal.tide_dto import DailyTideRecord, Tide, TideLocation, TideType

logger = logging.getLogger(__name__)

URL = NewType("URL", str)

# The full 7-day forecast is embedded in a window.__INITIAL_DATA__ JS assignment
# rather than the rendered HTML table (which only ever shows "today", even when
# the URL asks for another day via ?selectedDate=). The value is a JSON string
# literal, so it needs decoding twice: once to unescape the JS string, once to
# parse the JSON it holds.
_INITIAL_DATA_RE = re.compile(r'window\.__INITIAL_DATA__="(.*?)";</script>', re.S)


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

    def _extract_tide_days(self, html: str, page_url: str) -> List[dict]:
        """Pull the list of per-day tide dicts out of window.__INITIAL_DATA__.

        Raises ValueError if the blob or the expected nesting is missing, so the
        caller can bail out for that location.
        """
        match = _INITIAL_DATA_RE.search(html)
        if not match:
            raise ValueError(
                f"Unable to find window.__INITIAL_DATA__ for {page_url}, "
                f"please check if {self.url} layout changed."
            )

        try:
            # First json.loads unescapes the JS string literal, second parses it.
            data = json.loads(json.loads(f'"{match.group(1)}"'))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode __INITIAL_DATA__ for {page_url}: {e}")

        blocks = data.get("data", {})
        # The block key carries query params (e.g. "tide-tables?locationId=..."),
        # so match on the prefix rather than an exact key.
        tide_block = next(
            (v for k, v in blocks.items() if k.startswith("tide-tables?")), None
        )
        if tide_block is None:
            raise ValueError(f"No tide-tables block in __INITIAL_DATA__ for {page_url}")

        tides = tide_block.get("data", {}).get("tides")
        if not tides:
            raise ValueError(f"No tides in __INITIAL_DATA__ for {page_url}")
        return tides

    def _parse_day(self, day: dict, page_url: str) -> Tuple[Optional[dt.date], List[Tide]]:
        """Convert one embedded day dict into (date, tides)."""
        try:
            day_date = dt.datetime.strptime(day["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError) as e:
            logger.error(f"Unparseable day date for {page_url}: {day.get('date')} ({e})")
            return None, []

        tides: List[Tide] = []
        for extreme in day.get("extremeTides", []):
            tide_type = extreme.get("type")
            if tide_type not in ("High", "Low"):
                # Skips the "Current tide" pseudo-entry, which isn't an extreme.
                continue
            try:
                # Timestamps carry a UTC offset (e.g. +0100 for BST); normalise
                # to naive UTC to match how records are stored.
                aware = dt.datetime.strptime(
                    extreme["timestamp"], "%Y-%m-%dT%H:%M:%S%z"
                )
                utc_datetime = aware.astimezone(dt.timezone.utc).replace(tzinfo=None)
                tides.append(
                    Tide(
                        TideType(tide_type),
                        utc_datetime=utc_datetime,
                        height=float(extreme["height"]),
                    )
                )
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to parse tide {extreme} for {page_url}: {e}")
                continue

        return day_date, tides

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
            tide_days = self._extract_tide_days(html, target_url)
        except ValueError as ve:
            logger.error(f"Value error for {target_url}: {ve}")
            return location, None

        today_date = today.date()
        multiday_records: List[DailyTideRecord] = []
        for day in tide_days:
            day_date, tides = self._parse_day(day, target_url)
            # The blob also includes yesterday; only keep today onwards.
            if day_date is None or day_date < today_date:
                continue
            multiday_records.append(DailyTideRecord(location=location, tides=tides))

        logger.info(f"{len(multiday_records)} days predictions found for {location}")

        if not multiday_records:
            return location, None

        return location, multiday_records
