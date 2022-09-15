from bs4 import BeautifulSoup
import urllib
import http
from urllib.request import urlopen
import urllib.request
import sqlite3
import click
from datetime import datetime
from tide_record import TideRecord
import logging
import random
from time import sleep
import json
import csv
from pathlib import Path
from multiprocessing import Pool, cpu_count

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y:%H:%M:%S', level=logging.DEBUG)


def read_config(config_file: Path):
    try:
        with config_file.open('r') as f:
            return json.load(f)
    except IOError as e:
        logging.error(f"config file {config_file} not found!")
        raise e


# load config.json, node that we need to locate the directory
# if the script is run elsewhere
p = Path(__file__).with_name('config.json')
config = read_config(p)


def get_db_connection():
    return sqlite3.connect(config['database'])


def get_tide_location_detail_to_map(db_connection) -> dict[str, tuple[str, int]]:
    sql = 'SELECT port_id, region_id, name FROM ' + config['location_table']
    port_id_2_detail_map = {}
    cursor = db_connection.cursor()
    cursor.execute(sql)
    for port_id, region_id, name in cursor.fetchall():
        port_id_2_detail_map[port_id] = (name, region_id)
    return port_id_2_detail_map


def create_tide_table_if_not_exist(db_connection):
    check_table_sql = "SELECT count(*) FROM sqlite_master " \
                      f"WHERE type='table' AND name='{config['tide_table']}' "

    cursor = db_connection.cursor()
    cursor.execute(check_table_sql)
    exists = cursor.fetchone()[0]

    if not exists:
        logging.info(f"{config['database']}: '{config['tide_table']}' table not found, creating..")
        sql = 'CREATE TABLE ' + config['tide_table'] + ' (' \
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


def fill_location_table_if_not_exist(db_connection):
    check_table_sql = "SELECT count(*) FROM sqlite_master " \
                      f"WHERE type='table' AND name='{config['location_table']}' "

    create_table_sql = 'CREATE TABLE ' + config['location_table'] + ' (' \
           'port_id TEXT UNIQUE,' + \
           'region_id INTEGER,' + \
           'name TEXT )'

    cursor = db_connection.cursor()
    cursor.execute(check_table_sql)
    exists = cursor.fetchone()[0]

    if not exists:
        logging.info(f"{config['database']}: '{config['location_table']}' table not found, populating..")
        cursor.execute(create_table_sql)
        db_connection.commit()

        insert_sql = f"INSERT INTO {config['location_table']} " \
                     f"(port_id, region_id, name) " \
                     f"VALUES(?,?,?) "

        p = Path(__file__).with_name(config['location_file'])
        with p.open('r') as csvfile:
            reader = csv.reader(csvfile)
            # ignore header
            next(reader)
            num = 0
            for pid, region_id, name in reader:
                cursor.execute(insert_sql, (pid, region_id, name))
                num += cursor.rowcount
        db_connection.commit()
        logging.debug(f"total {num} locations added")


def drop_table(db_connection, table_name: str):
    sql = f"DROP TABLE {table_name};"
    cursor = db_connection.cursor()
    cursor.execute(sql)
    db_connection.commit()


def insert(db_connection, tide_record: TideRecord):
    insert_sql = f"INSERT INTO {config['tide_table']} " \
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


def parse_record(region_id, port_id, port_name):
    logging.info(f'scraping tide prediction for {port_name}, (port id={port_id})')
    location_code = str(region_id) + '/' + port_id
    url = config['url'] + location_code
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_day = datetime.now().day
    daily_tide_record_list = list()
    retry = 0
    failed = True
    while retry < config['max_retry'] and failed:
        try:
            req = urllib.request.Request(
                url,
                data=None,
                headers={"Content-Type": "application/json; charset=utf-8",
                         "User-Agent": f"{random.choice(config['user_agents'])}"
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
                daily_tide_record_list.append(t_record)

        except urllib.error.HTTPError as e:
            logging.error(f"{url} not found")
            failed = True
            retry += 1
            sleep(retry**2)
            continue
        except http.client.IncompleteRead as ine:
            logging.error(str(ine))
            failed = True
            retry += 1
            sleep(retry**2)
            continue
        break
    return port_id, daily_tide_record_list


@click.command()
@click.option('-p', '--port-id', multiple=True,
              help='port-ids to scrape, if not specified all available ports will be scraped.')
@click.option('-n', '--num-workers', type=int, default=cpu_count(),
              help=f'num of concurrent workers, default {cpu_count()}')
def main(port_id: str, num_workers: int):
    conn = get_db_connection()
    fill_location_table_if_not_exist(conn)
    create_tide_table_if_not_exist(conn)
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
        successful_pid = 0
        failed_pids = list()
        logging.info(f"scrape using {num_workers} workers")
        for pid, tide_predictions in pool.starmap(parse_record, args):
            num_predictions = len(tide_predictions)
            if num_predictions > 0:
                successful_pid += 1
            else:
                failed_pids.append(pid)
            cnt += len(tide_predictions)
            for record in tide_predictions:
                insert(conn, record)

        logging.info(f"{successful_pid}/{len(port_id)} locations collected, total {cnt} records saved")
        if failed_pids:
            logging.warning(f"failed locations port ids: {failed_pids}")

    conn.close()


if __name__ == '__main__':
    main()

