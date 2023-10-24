import logging
import sqlite3
from pathlib import Path
from typing import Iterable

from tidal.tide_dto import DailyTideRecord

logger = logging.getLogger(__name__)


class TidalDatabase:
    def __init__(self, database_file: Path, table_name: str):
        self.con = sqlite3.connect(database_file)
        self.cursor = self.con.cursor()
        self.table_name = table_name

    def create_table(self) -> None:
        sql = (
            "CREATE TABLE IF NOT EXISTS " + self.table_name + " ("
            "date TEXT,"
            + "port_id TEXT,"
            + "tide_type TEXT,"
            + "tide_time TEXT,"
            + "tide_timezone TEXT,"
            + "height REAL,"
            + "UNIQUE (date, port_id, tide_time) ON CONFLICT REPLACE )"
        )

        self.cursor.execute(sql)
        if self.cursor.rowcount <= 0:
            logger.debug(
                f'Table "{self.table_name}" already existed. Skipping creation'
            )
        else:
            logger.info(f'Table "{self.table_name}" created.')
        self.con.commit()

    def drop_table(self):
        sql = f"DROP TABLE {self.table_name};"
        self.cursor.execute(sql)
        self.con.commit()

    def insert(self, tide_records: Iterable[DailyTideRecord]):
        insert_sql = (
            f"INSERT INTO {self.table_name} "
            f"(date, port_id, tide_type, tide_time, tide_timezone, height) "
            f"VALUES(?,?,?,?,?,?) "
        )
        for daily_tides in tide_records:
            for tide in daily_tides.tides:
                date_str = tide.utc_date_time.date().strftime("%Y-%m-%d")
                time_str = tide.utc_date_time.time().strftime("%H:%M")
                self.cursor.execute(
                    insert_sql,
                    (
                        date_str,
                        daily_tides.location.port_id,
                        tide.type.value,
                        time_str,
                        "UTC",
                        tide.height,
                    ),
                )
        self.con.commit()

    def close(self):
        self.con.close()
