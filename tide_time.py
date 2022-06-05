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

log.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%d-%m-%Y:%H:%M:%S', level=log.DEBUG)


class Tidal:
    BASE_URL = "https://www.bbc.co.uk/weather/coast-and-sea/tide-tables/"
    TABLE_NAME = 'tidal'
    USER_AGENT_LIST = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    ]

    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cursor = self.con.cursor()

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_day = datetime.now().day
        self.create_table()

        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": f"{random.choice(Tidal.USER_AGENT_LIST)}"
        }

    def create_table(self):
        sql = 'CREATE TABLE IF NOT EXISTS ' + Tidal.TABLE_NAME + ' (' \
              'date TEXT,' + \
              'port_id TEXT,' + \
              'tide_type TEXT,' + \
              'tide_time TEXT,' + \
              'tide_timezone TEXT,' + \
              'height REAL,' + \
              'UNIQUE (date, port_id, tide_time) ON CONFLICT REPLACE )'

        self.cursor.execute(sql)
        if self.cursor.rowcount <= 0:
            log.info(f'Table "{Tidal.TABLE_NAME}" already existed. Skipping creation')
        else:
            log.info(f'Table "{Tidal.TABLE_NAME}" created.')
        self.con.commit()

    def drop_table(self):
        sql = f"DROP TABLE {Tidal.TABLE_NAME};"
        self.cursor.execute(sql)
        self.con.commit()

    def insert(self, tide_record: TideRecord):
        insert_sql = f"INSERT INTO {Tidal.TABLE_NAME} " \
              f"(date, port_id, tide_type, tide_time, tide_timezone, height) " \
              f"VALUES(?,?,?,?,?,?) "

        for item in tide_record.get_measurements():
            self.cursor.execute(insert_sql, (tide_record.get_date().strftime('%Y-%m-%d'),
                                             tide_record.port_id,
                                             item.type,
                                             item.time,
                                             tide_record.timezone,
                                             item.height))
        self.con.commit()

    def parse_record(self, area_id, port_id):
        location_code = area_id + '/' + port_id
        url = Tidal.BASE_URL + location_code
        try:
            req = urllib.request.Request(
                url,
                data=None,
                headers=self.headers
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


@click.command()
@click.option('-a', '--area-id', default='9',
              help='area id')
@click.option('-p', '--port-id', default='103',
              help='port id')
def main(area_id, port_id):
    t = Tidal("tidal.db")
    tide_list = t.parse_record(area_id, port_id)
    for record in tide_list:
        t.insert(record)
    t.cursor.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

