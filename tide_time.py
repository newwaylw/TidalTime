from bs4 import BeautifulSoup
import urllib
import http
from tenacity import retry
from tenacity import stop_after_attempt, wait_exponential
from urllib.request import urlopen
import urllib.request
import sqlite3
import click
from click_loglevel import LogLevel
from datetime import datetime
from tide_record import TideRecord
import logging
import random
import configparser
import time


class Tidal:
    BASE_URL = "https://www.bbc.co.uk/weather/coast-and-sea/tide-tables/"
    TIDE_TABLE = 'tidal'
    LOCATION_TABLE = 'location'
    USER_AGENT_LIST = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    ]

    def __init__(self, config_file, loging):
        self.config = configparser.ConfigParser()
        self.logging = loging
        try:
            with open(config_file) as f:
                self.config.read_file(f)
        except IOError as e:
            self.logging.error(f"config file {config_file} not found!")
            raise e
        self.con = sqlite3.connect(self.config['DEFAULT']['Database'])
        self.cursor = self.con.cursor()
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_day = datetime.now().day
        self.create_table()

        self._port_id_2_region_map = {}
        self._port_id_2_location_name = {}

        for port_id, region, name in self.load_locations():
            self._port_id_2_region_map[port_id] = region
            self._port_id_2_location_name[port_id] = name

    def load_locations(self):
        sql = 'SELECT port_id, region_id, name FROM ' + Tidal.LOCATION_TABLE
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def create_table(self):
        sql = 'CREATE TABLE IF NOT EXISTS ' + Tidal.TIDE_TABLE + ' (' \
              'date TEXT,' + \
              'port_id TEXT,' + \
              'tide_type TEXT,' + \
              'tide_time TEXT,' + \
              'tide_timezone TEXT,' + \
              'height REAL,' + \
              'UNIQUE (date, port_id, tide_time) ON CONFLICT REPLACE )'

        self.cursor.execute(sql)
        if self.cursor.rowcount <= 0:
            self.logging.debug(f'Table "{Tidal.TIDE_TABLE}" already existed. Skipping creation')
        else:
            self.logging.info(f'Table "{Tidal.TIDE_TABLE}" created.')
        self.con.commit()

    def drop_table(self):
        sql = f"DROP TABLE {Tidal.TIDE_TABLE};"
        self.cursor.execute(sql)
        self.con.commit()

    def insert(self, tide_record: TideRecord):
        insert_sql = f"INSERT INTO {Tidal.TIDE_TABLE} " \
              f"(date, port_id, tide_type, tide_time, tide_timezone, height) " \
              f"VALUES(?,?,?,?,?,?) "

        for item in tide_record.get_measurements():
            self.cursor.execute(insert_sql, (tide_record.get_date().strftime('%Y-%m-%d'),
                                             tide_record.port_id,
                                             item.type,
                                             item.time,
                                             tide_record.timezone,
                                             item.height))

    def close(self):
        self.con.close()

    def get_region(self, port_id):
        return self._port_id_2_region_map[port_id]

    def get_all_port_ids(self):
        return self._port_id_2_region_map.keys()

    def get_location_name(self, port_id):
        return self._port_id_2_location_name[port_id]

    # retry 5 times in case of bad network connection
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=32))
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=32))
    def parse_record(self, area_id, port_id):
        location_code = str(area_id) + '/' + port_id
        url = Tidal.BASE_URL + location_code
        tide_record_list = list()
        try:
            req = urllib.request.Request(
                url,
                data=None,
                headers={"Content-Type": "application/json; charset=utf-8",
                         "User-Agent": f"{random.choice(Tidal.USER_AGENT_LIST)}"
                         }
            )

            html = urllib.request.urlopen(req)
            soup = BeautifulSoup(html, features="html.parser")
            tables = soup.select("table.wr-c-tide-extremes")
            self.logging.info(f"{len(tables)} days predictions found for {self.get_location_name(port_id)} (port_id={port_id})")
            # each table contains tide prediction for 1 day starting 'today'
            for offset, table in enumerate(tables):
                row_text = table.select_one("caption").text
                types = [[td.text for td in row.find_all("th")] for row in table.select("tr")]
                data = [[td.text for td in row.find_all("td")] for row in table.select("tr")[1:]]
                _, time, height = types.pop(0)
                high_low = [x[0] for x in types]
                self.logging.debug(f"{len(high_low)} {row_text}")
                # BST or UTC ?
                # TODO handle timezone consistency
                timezone = 'BST' if 'BST' in time else 'UTC'
                t_record = TideRecord(self.current_year, self.current_month, self.current_day, offset,
                                      timezone, area_id, port_id)
                for type, item in zip(high_low, data):
                    height = float(item[1])
                    t_record.add_record(type, item[0], height)
                    tide_record_list.append(t_record)
        except urllib.error.HTTPError as e:
            self.logging.error(f"{url} not found")
            raise e
        except http.client.IncompleteRead as ine:
            self.logging.error(str(ine))
            raise ine
        return tide_record_list

    def write(self, port_id):
        try:
            area_id = self.get_region(port_id)
            tide_list = self.parse_record(area_id, port_id)
            if len(tide_list) == 0:
                self.logging.warning("No record found, something is wrong with the url?")
            else:
                self.logging.debug(f"inserting records, port_id={port_id}, region_id={area_id}, "
                                   f"no. record={len(tide_list)} to db")
            
            for record in tide_list:
                self.insert(record)
            self.con.commit()
            self.logging.info(f"{len(tide_list)} tide records for {self._port_id_2_location_name[port_id]} saved.")
            return True
        except (urllib.error.HTTPError, http.client.IncompleteRead) as e:
            msg = f"parsing record for {port_id} tried {self.parse_record.retry.statistics['attempt_number']} " \
                  f"times but failed, usually this is caused by unstable network connections."
            self.logging.error(msg)
            return False

    def write_all(self):
        count = 0
        wait_interval = int(self.config['DEFAULT']['Interval'])
        for port_id in self.get_all_port_ids():
            success = self.write(port_id)
            if success:
                count += 1
                self.logging.info(f"tide info for port id {port_id} saved.")
            time.sleep(wait_interval)
        self.logging.info(f"{count}/{len(self.get_all_port_ids())} saved.")


@click.command()
@click.option('-c', '--config-file', default='config.cfg',
              help='path to config file')
@click.option('-p', '--port-id', multiple=True,
              help='port-ids to scrape, if not specified all available ports will be scraped.')
@click.option("-l", "--log-level", type=LogLevel(), default=logging.INFO)
def main(config_file, port_id, log_level):
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%d-%m-%Y:%H:%M:%S', level=log_level)

    t = Tidal(config_file, logging)
    if port_id:
        for pid in port_id:
            if pid not in t.get_all_port_ids():
                logging.error(f"{pid} is not a valid port id!")
                exit(1)
            t.write(pid)
    else:
        t.write_all()
    t.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

