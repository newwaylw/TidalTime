import asyncio
import configparser
import datetime as dt
import json
import logging
from pathlib import Path
from typing import Dict, List

import aiohttp
import click
import tqdm.asyncio

from tidal.db import TidalDatabase
from tidal.scraper import URL, BBCTideScraper
from tidal.tide_dto import AreaID, PortID, TideLocation


def load_locations_map(tide_location_file: Path) -> Dict[PortID, TideLocation]:
    """Load tide locations from the nested ``locations_raw.json`` schema.

    The file is structured as ``countries`` -> optionally ``regions`` ->
    ``locations``. Countries without regions carry ``locations`` directly. Each
    location is keyed by its ``port_id`` (the location ``id``).
    """
    with open(tide_location_file) as f:
        data = json.load(f)

    def _areas(country: dict):
        # A country either groups its locations under regions or lists them
        # directly. Normalise both into (area_name, area_id, locations) tuples.
        if "regions" in country:
            for region in country["regions"]:
                yield region["name"], region["id"], region.get("locations", [])
        else:
            yield country["name"], country["id"], country.get("locations", [])

    locations_map: Dict[PortID, TideLocation] = {}
    for country in data.get("countries", []):
        for area_name, area_id, locations in _areas(country):
            for location in locations:
                port_id = PortID(location["id"])
                locations_map[port_id] = TideLocation(
                    region_name=area_name,
                    name=location["name"],
                    area_id=AreaID(area_id),
                    port_id=port_id,
                )
    return locations_map


async def run(
    locations: List[TideLocation],
    scraper: BBCTideScraper,
    tide_database: TidalDatabase,
    num_workers: int,
) -> List[TideLocation]:
    semaphore = asyncio.Semaphore(num_workers)
    today = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

    async def download(session: aiohttp.ClientSession, location: TideLocation):
        async with semaphore:
            return await scraper.download_tidal_info(session, location, today)

    error_locations = []
    async with aiohttp.ClientSession() as session:
        tasks = [download(session, loc) for loc in locations]
        for coro in tqdm.asyncio.tqdm.as_completed(tasks, total=len(tasks)):
            location, records = await coro
            if not records:
                error_locations.append(location)
            else:
                tide_database.insert(records)

    return error_locations


@click.command()
@click.option(
    "-c",
    "--config-file",
    type=Path,
    default="config.cfg",
    help="path to config file",
)
@click.option(
    "-l",
    "--tide-location-file",
    type=Path,
    default="locations_raw.json",
    help="path to tide location file, default locations_raw.json",
)
@click.option(
    "-p",
    "--port-ids",
    multiple=True,
    type=PortID,
    help="port-ids to scrape, if not specified all ports will be scraped.",
)
@click.option(
    "-n",
    "--num-workers",
    type=int,
    default=10,
    help="number of concurrent requests, default 10",
)
@click.option("-v", "--verbose", is_flag=True, help="increase output verbosity")
def main(
    config_file: str,
    tide_location_file: Path,
    port_ids: List[PortID],
    num_workers: int,
    verbose: bool,
):
    logging.basicConfig(
        format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%d-%m-%Y:%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )

    config = configparser.ConfigParser()
    try:
        with open(config_file) as f:
            config.read_file(f)
    except IOError:
        logging.error(f"config file {config_file} not found!")
        exit(-1)

    tide_location_map = load_locations_map(tide_location_file)

    if not port_ids:
        locations_to_download = list(tide_location_map.values())
    else:
        locations_to_download = []
        for port_id in port_ids:
            if port_id in tide_location_map:
                locations_to_download.append(tide_location_map[port_id])
            else:
                logging.warning(
                    f"port_id {port_id} does not exist in the location file! Skipping"
                )

    scraper = BBCTideScraper(URL(config["DEFAULT"].get("BASE_URL")))
    tide_database = TidalDatabase(
        Path(config["DEFAULT"].get("DATABASE_NAME")),
        config["DEFAULT"].get("DATABASE_TIDE_TABLE_NAME"),
    )
    tide_database.create_table(drop_existing=False)

    error_locations = asyncio.run(
        run(locations_to_download, scraper, tide_database, num_workers)
    )

    num_success = len(locations_to_download) - len(error_locations)
    logging.info(f"{num_success}/{len(locations_to_download)} locations collected.")
    for i, location in enumerate(error_locations):
        logging.error(f"Failed location {i + 1}: {location}")

    tide_database.close()


if __name__ == "__main__":
    main()
