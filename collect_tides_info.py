import asyncio
import configparser
import datetime as dt
import logging
from pathlib import Path
from typing import Dict, List

import aiohttp
import click
import tqdm.asyncio

from tidal.db import TidalDatabase
from tidal.scraper import URL, BBCTideScraper
from tidal.tide_dto import PortID, TideLocation
from tidal.utils.store import JSONStore


def load_locations_map(tide_location_file: Path) -> Dict[PortID, TideLocation]:
    return {
        location.port_id: location
        for location in JSONStore.load_lines(path=tide_location_file, dtype=TideLocation)
    }


async def run(
    locations: List[TideLocation],
    scraper: BBCTideScraper,
    tide_database: TidalDatabase,
    num_workers: int,
) -> List[TideLocation]:
    semaphore = asyncio.Semaphore(num_workers)
    today = dt.datetime.utcnow()

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

    tide_location_map = load_locations_map(
        Path(config["DEFAULT"].get("TIDE_LOCATION_FILE"))
    )

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
