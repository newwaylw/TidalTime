import configparser
import sqlite3
from datetime import datetime
import logging as log
import requests
import time

log.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%d-%m-%Y:%H:%M:%S', level=log.DEBUG)
class Notification:
    TABLE_NAME = 'tidal'
    port_id_map = {'103': 'Margate',
                   '104': 'Herne Bay'}

    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.con = sqlite3.connect(self.config['DEFAULT']['Database'])
        self.cursor = self.con.cursor()

    def query_low(self):
        today = datetime.now().strftime("%Y-%m-%d")
        sql = 'SELECT date, ' \
              'port_id, ' \
              'tide_type, ' \
              'tide_time, ' \
              'tide_timezone, ' \
              'height ' \
              f"FROM {Notification.TABLE_NAME} WHERE date > \'{today}\' " \
              f"AND tide_type = 'Low' " \
              f"AND height <= {self.config['DEFAULT']['Threshold']}"
        log.debug(f'query = {sql}')
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

    def send_msg(self, date, port_id, tide_type, tide_time, tide_timezone, height):
        location = Notification.port_id_map.get(port_id)
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


if __name__ == '__main__':
    n = Notification('slack.cfg')
    r = n.query_low()
    for record in r:
        d = record[0]
        port_id = record[1]
        tide_type = record[2]
        tide_time = record[3]
        tide_timezone = record[4]
        height = record[5]
        n.send_msg(d, port_id, tide_type, tide_time, tide_timezone, height)
