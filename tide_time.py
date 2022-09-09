from bs4 import BeautifulSoup
import urllib
import http
from tenacity import retry
from tenacity import stop_after_attempt, wait_exponential
from urllib.request import urlopen
import urllib.request
import sqlite3
import click
from datetime import datetime
from tide_record import TideRecord
import logging
import random
import configparser
import time
from multiprocessing import Pool, cpu_count

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y:%H:%M:%S', level=logging.DEBUG)

BASE_URL = "https://www.bbc.co.uk/weather/coast-and-sea/tide-tables/"
TIDE_TABLE = 'tidal'
LOCATION_TABLE = 'location'
USER_AGENT_LIST = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (iPad; CPU OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.0 Mobile/14G60 Safari/602.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0'
]


def read_config(config_file: str):
    config = configparser.ConfigParser()
    try:
        with open(config_file) as f:
            config.read_file(f)
        return config
    except IOError as e:
        logging.error(f"config file {config_file} not found!")
        raise e


def get_db_connection(config):
    return sqlite3.connect(config['DEFAULT']['Database'])


def get_tide_location_detail_to_map(db_connection) -> dict[str, tuple[str, int]]:
    sql = 'SELECT port_id, region_id, name FROM ' + LOCATION_TABLE
    port_id_2_detail_map = {}
    cursor = db_connection.cursor()
    cursor.execute(sql)
    for port_id, region_id, name in cursor.fetchall():
        port_id_2_detail_map[port_id] = (name, region_id)
    return port_id_2_detail_map


def create_tide_table_if_not_exist(db_connection, tide_table_name):
    sql = 'CREATE TABLE IF NOT EXISTS ' + tide_table_name + ' (' \
          'date TEXT,' + \
          'port_id TEXT,' + \
          'tide_type TEXT,' + \
          'tide_time TEXT,' + \
          'tide_timezone TEXT,' + \
          'height REAL,' + \
          'UNIQUE (date, port_id, tide_time) ON CONFLICT REPLACE )'
    cursor = db_connection.cursor()
    cursor.execute(sql)
    db_connection.commit()


def create_location_table_if_not_exist(db_connection, location_table_name):
    sql = 'CREATE TABLE IF NOT EXISTS ' + location_table_name + ' (' \
           'port_id TEXT UNIQUE,' + \
           'region_id INTEGER,' + \
           'name TEXT )'

    cursor = db_connection.cursor()
    cursor.execute(sql)
    db_connection.commit()

def drop_table(db_connection, table_name: str):
    sql = f"DROP TABLE {table_name};"
    cursor = db_connection.cursor()
    cursor.execute(sql)
    db_connection.commit()


def insert(db_connection, table_name, tide_record: TideRecord):
    insert_sql = f"INSERT INTO {table_name} " \
          f"(date, port_id, tide_type, tide_time, tide_timezone, height) " \
          f"VALUES(?,?,?,?,?,?) "
    cursor = db_connection.cursor()
    for tide_type, tide_time, tide_height in tide_record.get_measurements():
        cursor.execute(insert_sql, (tide_record.get_date().strftime('%Y-%m-%d'),
                                    tide_record.port_id,
                                    tide_type,
                                    tide_time,
                                    tide_record.timezone,
                                    tide_height))
    db_connection.commit()

# retry 5 times in case of bad network connection
# https://github.com/jd/tenacity/issues/147 doesn't work with multiprocessing pool
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=32))
def parse_record(region_id, port_id, port_name):
    location_code = str(region_id) + '/' + port_id
    url = BASE_URL + location_code
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_day = datetime.now().day
    tide_record_list = list()
    try:
        req = urllib.request.Request(
            url,
            data=None,
            headers={"Content-Type": "application/json; charset=utf-8",
                     "User-Agent": f"{random.choice(USER_AGENT_LIST)}"
                     }
        )

        html = urllib.request.urlopen(req)
        soup = BeautifulSoup(html, features="html.parser")
        tables = soup.select("table.wr-c-tide-extremes")
        logging.info(f"{len(tables)} days predictions found for {port_name} (port_id={port_id})")
        # each table contains tide prediction for 1 day starting 'today'
        for offset, table in enumerate(tables):
            row_text = table.select_one("caption").text
            types = [[td.text for td in row.find_all("th")] for row in table.select("tr")]
            data = [[td.text for td in row.find_all("td")] for row in table.select("tr")[1:]]
            _, time, height = types.pop(0)
            high_low = [x[0] for x in types]
            logging.debug(f"{len(high_low)} {row_text}")
            # BST or UTC ?
            # TODO handle timezone consistency
            timezone = 'BST' if 'BST' in time else 'UTC'
            t_record = TideRecord(current_year, current_month, current_day, offset,
                                  timezone, region_id, port_id)
            for type, item in zip(high_low, data):
                height = float(item[1])
                t_record.add_record(type, item[0], height)
            tide_record_list.append(t_record)

    except urllib.error.HTTPError as e:
        logging.error(f"{url} not found")
        raise e
    except http.client.IncompleteRead as ine:
        logging.error(str(ine))
        raise ine
    finally:
        # logging.debug(f"{parse_record.retry.statistics['attempt_number']}")
        return tide_record_list


@click.command()
@click.option('-c', '--config-file', default='config.cfg',
              help='path to config file')
@click.option('-p', '--port-id', multiple=True,
              help='port-ids to scrape, if not specified all available ports will be scraped.')
@click.option('-n', '--num-workers', type=int, default=cpu_count(),
              help=f'num of concurrent workers, default {cpu_count()}')

# @click.option('-s', '--sleep', type=int, default=0, help="sleep this many seconds between each location each worker")
def main(config_file: str, port_id: str, num_workers: int):

    config = read_config(config_file)
    conn = get_db_connection(config)
    create_tide_table_if_not_exist(conn, config.get('DEFAULT', 'Tide_table'))
    create_location_table_if_not_exist(conn, config.get('DEFAULT', 'Location_table'))
    port_id_2_detail_map = get_tide_location_detail_to_map(conn)

    # if port_id is not set, fetch all available port_ids from db
    if not port_id:
        port_id = port_id_2_detail_map.keys()

    args = list()
    for pid in port_id:
        name, region_id = port_id_2_detail_map.get(pid, (None, None))
        args.append((region_id, pid, name))

    with Pool(processes=num_workers) as pool:
        cnt = 0
        logging.debug(f"{num_workers} workers/processes")
        for records in pool.starmap(parse_record, args):
            cnt += len(records)
            for record in records:
                insert(conn, config.get('DEFAULT', 'Tide_table'), record)

        logging.info(f"Total {cnt} records saved")
    conn.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

