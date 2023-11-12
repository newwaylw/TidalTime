import configparser
import datetime
import logging
import time
from pathlib import Path

import click
import requests

from tidal.db import TidalDatabase
from tidal.tide_dto import Tide, TideLocation, TideType


def send_msg(url: str, tide_location: TideLocation, tide_info: Tide):
    sent = False
    cnt = 0
    message = (
        f'Spring {tide_info.type} tide {tide_info.height}m at "{tide_location.name}"'
        + f" at: {tide_info.utc_datetime} UTC "
    )
    logging.info(f"Sending message = {message}")

    while not sent:
        r = requests.post(url, json={"text": message})
        cnt += 1
        if not (r.status_code == 200 and r.reason == "OK"):
            logging.debug(f"HTTP POST failed: {r.status_code} {r.reason}")
            if cnt > 10:
                logging.debug(f"failed {cnt} times, quitting")
                break
            time.sleep(min(300, 2**cnt))
        else:
            logging.debug(f"HTTP POST successful: {r.status_code} {r.reason}")
            sent = True


@click.command()
@click.option("-c", "--config-file", default="config.cfg", help="path to config file")
@click.option("-p", "--port-id", required=True, help="port-id to monitor")
@click.option(
    "-t",
    "--low-threshold",
    type=float,
    default=0.5,
    help="send notification when tide is lower than this",
)
@click.option("-v", "--verbose", is_flag=True, help="increase output verbosity")
def main(config_file, port_id, low_threshold, verbose):
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

    tide_database = TidalDatabase(
        Path(config["DEFAULT"].get("DATABASE_NAME")),
        config["DEFAULT"].get("DATABASE_TIDE_TABLE_NAME"),
    )

    tide_location = tide_database.get_location_by_port_id(port_id=port_id)

    n_match = 0
    for tide in tide_database.query_tide(
        port_id=tide_location.port_id,
        start_date=datetime.datetime.utcnow(),
        end_date=datetime.datetime.utcnow() + datetime.timedelta(days=7),
    ):
        if tide.type == TideType.LOW and tide.height <= low_threshold:
            n_match += 1
            send_msg(config["DEFAULT"]["WEBHOOK"], tide_location, tide)

    logging.info(f"{n_match} matching tide records found.")


if __name__ == "__main__":
    main()
