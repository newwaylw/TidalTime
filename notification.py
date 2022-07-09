import configparser
import sqlite3
from datetime import datetime
import logging as log
import requests
import time
import click

log.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%d-%m-%Y:%H:%M:%S', level=log.DEBUG)


class Notification:
    TIDE_TABLE = 'tidal'
    LOCATION_TABLE = 'location'

    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.con = sqlite3.connect(self.config['DEFAULT']['Database'])
        self.cursor = self.con.cursor()
        self.port_id_2_name_map = {item[0]: item[1] for item in self.__load_locations__()}

    def __load_locations__(self):
        sql = 'SELECT port_id, name FROM ' + Notification.LOCATION_TABLE
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_location_name(self, port_id):
        return self.port_id_2_name_map.get(port_id)

    def query_low(self, port_id_list, threshold):
        today = datetime.now().strftime("%Y-%m-%d")
        sql = 'SELECT date, ' \
              'port_id, ' \
              'tide_type, ' \
              'tide_time, ' \
              'tide_timezone, ' \
              'height ' \
              f"FROM {Notification.TIDE_TABLE} WHERE date > \'{today}\' " \
              f"AND tide_type = 'Low' " \
              f"AND height <= {threshold} "
        if not port_id_list:
            log.debug(f'query = {sql}')
            self.cursor.execute(sql)
        else:
            sql += f"AND port_id in ({','.join(['?']*len(port_id_list))})"
            log.debug(f'query = {sql}, {port_id_list}')
            self.cursor.execute(sql, port_id_list)
        result = self.cursor.fetchall()
        return result

    def send_msg(self, date, port_id, tide_type, tide_time, tide_timezone, height):
        location = self.get_location_name(port_id)
        sent = False
        cnt = 0
        message = f'Spring {tide_type} tide {height}m at {location}: \n' + \
                  f'on: {date} at {tide_time} ({tide_timezone})'
        log.info(f"message = {message}")
        while not sent:
            r = requests.post(self.config['DEFAULT']['Webhook'],
                              json={'text': message})
            cnt += 1
            if not (r.status_code == 200 and r.reason == 'OK'):
                log.debug(f"HTTP POST failed: {r.status_code} {r.reason}")
                if cnt > 10:
                    log.debug(f"failed {cnt} times, quitting")
                    break
                time.sleep(min(300, 2**cnt))
            else:
                log.debug(f"HTTP POST successful: {r.status_code} {r.reason}")
                sent = True


@click.command()
@click.option('-c', '--config-file', default='config.cfg',
              help='path to config file')
@click.option('-p', '--port-id', multiple=True, help='port-ids to monitor')
@click.option('-t', '--threshold', type=float, default=0.5,
              help='send notification when tide is lower than this')
def main(config_file, port_id, threshold):
    n = Notification(config_file)
    r = n.query_low(port_id, threshold)
    log.debug(f"{len(r)} record(s) found")
    for record in r:
        d = record[0]
        port_id = record[1]
        tide_type = record[2]
        tide_time = record[3]
        tide_timezone = record[4]
        height = record[5]
        n.send_msg(d, port_id, tide_type, tide_time, tide_timezone, height)


if __name__ == '__main__':
    main()
