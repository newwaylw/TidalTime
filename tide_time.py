from bs4 import BeautifulSoup
import urllib
from urllib.request import urlopen
import urllib.request
import sqlite3
import click
from datetime import datetime
from tide_record import TideRecord
import logging as log
import random
import configparser
import time

log.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%d-%m-%Y:%H:%M:%S', level=log.DEBUG)


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

    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.con = sqlite3.connect(self.config['DEFAULT']['Database'])
        self.cursor = self.con.cursor()
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_day = datetime.now().day
        self.create_table()
        self.port_id_2_region_map = {item[0]: item[1] for item in self.load_locations()}

    def load_locations(self):
        sql = 'SELECT port_id, region_id FROM ' + Tidal.LOCATION_TABLE
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
            log.info(f'Table "{Tidal.TIDE_TABLE}" already existed. Skipping creation')
        else:
            log.info(f'Table "{Tidal.TIDE_TABLE}" created.')
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
        return self.port_id_2_region_map[port_id]

    def get_all_port_ids(self):
        return self.port_id_2_region_map.keys()

    def parse_record(self, area_id, port_id):
        location_code = str(area_id) + '/' + port_id
        url = Tidal.BASE_URL + location_code
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
            tide_record_list = list()
            log.info(f"{len(tables)} days record found")
            # each table contains tide prediction for 1 day starting 'today'
            for i, table in enumerate(tables):
                row_text = table.select_one("caption").text
                types = [[td.text for td in row.find_all("th")] for row in table.select("tr")]
                data = [[td.text for td in row.find_all("td")] for row in table.select("tr")[1:]]
                _, time, height = types.pop(0)
                high_low = [x[0] for x in types]
                log.debug(f"{len(high_low)} {row_text}")
                # BST or UTC ?
                timezone = 'BST' if 'BST' in time else 'UTC'
                t_record = TideRecord(self.current_year, self.current_month, self.current_day+i,
                                      timezone, area_id, port_id)
                for type, item in zip(high_low, data):
                    height = float(item[1])
                    t_record.add_record(type, item[0], height)
                    tide_record_list.append(t_record)
        except urllib.error.HTTPError:
            log.error(f"{url} not found")

        return tide_record_list

    def write(self, port_id):
        area_id = self.get_region(port_id)
        tide_list = self.parse_record(area_id, port_id)
        log.debug(f"inserting records, port_id={port_id}, region_id={area_id}, no. record={len(tide_list)}")
        for record in tide_list:
            self.insert(record)
        self.con.commit()

    def write_all(self):
        wait_interval = int(self.config['DEFAULT']['Interval'])
        for port_id in self.get_all_port_ids():
            self.write(port_id)
            time.sleep(wait_interval)


@click.command()
@click.option('-c', '--config-file', default='config.cfg',
              help='path to config file')
@click.option('-p', '--port-id', multiple=True, help='port-ids to monitor')
def main(config_file, port_id):
    t = Tidal(config_file)
    if port_id:
        for pid in port_id:
            t.write(pid)
    else:
        t.write_all()
    t.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

