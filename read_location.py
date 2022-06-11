import configparser
import sqlite3
import re

CONFIG_FILE = 'config.cfg'
TABLE_NAME = 'location'

create_table_sql = 'CREATE TABLE IF NOT EXISTS ' + TABLE_NAME + ' (' \
              'port_id TEXT UNIQUE,' + \
              'region_id INTEGER,' + \
              'name TEXT )'

insert_sql = f"INSERT OR REPLACE INTO {TABLE_NAME} " \
              f"(port_id, region_id, name) " \
              f"VALUES(?,?,?) "

config = configparser.ConfigParser()
config.read(CONFIG_FILE)
con = sqlite3.connect(config['DEFAULT']['Database'])
cursor = con.cursor()

cursor.execute(create_table_sql)
con.commit()

with open('port_data.csv', 'r') as f:
    for line in f:
        region, port_id, name = re.split(r'\t|/', line.strip())
        cursor.execute(insert_sql, (port_id, region, name))
    con.commit()