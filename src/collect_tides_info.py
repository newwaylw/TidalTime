import configparser
import datetime
import logging
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List

import click
import tqdm

from tidal.scraper import BBCTideScraper
from tidal.tide import PortID, TideLocation
from tidal.utils.json_store import JSONStore

logging.basicConfig(
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%d-%m-%Y:%H:%M:%S",
    level="INFO",
)

logger = logging.getLogger(__name__)


def load_locations_map(tide_location_file: Path) -> Dict[PortID, TideLocation]:
    json_store = JSONStore()
    location_map = dict()
    for location in json_store.load_lines(
        path=tide_location_file, dtype=TideLocation
    ):
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
    help="port-ids to scrape, if not specified all available ports will be scraped.",
)
@click.option(
    "-n",
    "--num-workers",
    type=int,
    default=cpu_count(),
    help=f"num of concurrent workers, default {cpu_count()}",
)
@click.option(
    "-o", "--output-dir", type=Path, required=True, help="output directory"
)
@click.option("-z", "--compress", is_flag=True, help="compress output file")
@click.option(
    "-v", "--verbose", is_flag=True, help="increase output verbosity"
)
def main(
    config_file: str,
    port_ids: List[PortID],
    output_dir: Path,
    compress: bool,
    num_workers: int,
    verbose: bool,
):
    config = configparser.ConfigParser()
    if verbose:
        logger.setLevel(logging.DEBUG)
    try:
        with open(config_file) as f:
            config.read_file(f)
    except IOError:
        logger.error(f"config file {config_file} not found!")
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
                    f"Location with port_id={port_id} "
                    f"will be skipped as it does not exist"
                )

    today_day = datetime.datetime.utcnow().strftime("%Y%m%d")
    output_dir.mkdir(exist_ok=True, parents=True)
    output_filename = today_day + ".jsonl"
    if compress:
        output_filename += ".gz"

    output_file = output_dir / Path(output_filename)
    # replace existing
    output_file.unlink(missing_ok=True)
    scrapper = BBCTideScraper(config["DEFAULT"].get("BASE_URL"))

    with Pool(processes=num_workers) as pool:
        error_locations = list()
        json_store = JSONStore()
        for location, record in tqdm.tqdm(
            pool.imap(scrapper.download_tidal_info, locations_to_download),
            total=len(locations_to_download),
        ):
            if not record:
                error_locations.append(location)
            else:
                json_store.save_lines(record, output_file, mode="a")

        num_success = len(locations_to_download) - len(error_locations)
        logger.info(
            f"{num_success}/{len(locations_to_download)} locations collected."
        )
        if len(error_locations) > 0:
            logger.info(f"Failed location details: {error_locations}")


if __name__ == "__main__":
    main()
