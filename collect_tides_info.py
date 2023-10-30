import configparser
import logging
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List

import click
import tqdm

from tidal.db import TidalDatabase
from tidal.scraper import URL, BBCTideScraper
from tidal.tide_dto import PortID, TideLocation
from tidal.utils.json_store import JSONStore


def load_locations_map(tide_location_file: Path) -> Dict[PortID, TideLocation]:
    json_store = JSONStore()
    location_map = dict()
    for location in json_store.load_lines(path=tide_location_file, dtype=TideLocation):
        location_map[location.port_id] = location
    return location_map


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
    default=cpu_count(),
    help=f"num of concurrent workers, default {cpu_count()}",
)
@click.option("-v", "--verbose", is_flag=True, help="increase output verbosity")
def main(
    config_file: str,
    port_ids: List[PortID],
    num_workers: int,
    verbose: bool,
):
    config = configparser.ConfigParser()
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%d-%m-%Y:%H:%M:%S",
        level=log_level,
    )
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
        locations_to_download = tide_location_map.values()
    else:
        locations_to_download = list()
        for port_id in port_ids:
            if port_id in tide_location_map:
                locations_to_download.append(tide_location_map[port_id])
            else:
                logging.warning(
                    f"port_id {port_id} does not exist in the location file! Skipping"
                )

    scrapper = BBCTideScraper(URL(config["DEFAULT"].get("BASE_URL")))
    tide_database = TidalDatabase(
        Path(config["DEFAULT"].get("DATABASE_NAME")),
        config["DEFAULT"].get("DATABASE_TIDE_TABLE_NAME"),
    )
    tide_database.create_table(drop_existing=False)

    with Pool(processes=num_workers) as pool:
        error_locations = list()
        for location, records in tqdm.tqdm(
            pool.imap(scrapper.download_tidal_info, locations_to_download),
            total=len(locations_to_download),
            position=0,
            leave=True,
        ):
            if not records:
                error_locations.append(location)
            else:
                tide_database.insert(records)
        num_success = len(locations_to_download) - len(error_locations)
        logging.info(f"{num_success}/{len(locations_to_download)} locations collected.")
        if len(error_locations) > 0:
            for i, location in enumerate(error_locations):
                logging.info(f"Failed location {i+1}: {location}")

    tide_database.close()


if __name__ == "__main__":
    main()
