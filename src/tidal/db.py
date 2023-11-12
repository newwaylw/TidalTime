import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Iterable

from tidal.tide_dto import (AreaID, DailyTideRecord, PortID, Tide,
                            TideLocation, TideType)

logger = logging.getLogger(__name__)


class TidalDatabase:
    def __init__(self, database_file: Path, table_name: str):
        self.con = sqlite3.connect(database_file)
        self.cursor = self.con.cursor()
        self.table_name = table_name

    def create_table(self, drop_existing=False) -> None:
        if drop_existing:
            self.drop_table()

        sql = (
            "CREATE TABLE IF NOT EXISTS "
            + self.table_name
            + " ("
            + "location TEXT,"
            + "area_id TEXT,"
            + "port_id TEXT,"
            + "utc_datetime TEXT,"
            + "tide_type TEXT,"
            + "height REAL,"
            + "UNIQUE (port_id, utc_datetime) ON CONFLICT REPLACE )"
        )

        self.cursor.execute(sql)
        if self.cursor.rowcount <= 0:
            logger.debug(
                f'Table "{self.table_name}" already existed. Skipping creation'
            )
        else:
            logger.info(f'Table "{self.table_name}" created.')
        self.con.commit()

    def drop_table(self) -> None:
        sql = f"DROP TABLE {self.table_name};"
        self.cursor.execute(sql)
        self.con.commit()

    def insert(self, tide_records: Iterable[DailyTideRecord]) -> None:
        insert_sql = (
            f"INSERT INTO {self.table_name} "
            f"(location, area_id, port_id, utc_datetime, tide_type, height) "
            f"VALUES(?,?,?,?,?,?) "
        )
        for daily_tides in tide_records:
            for tide in daily_tides.tides:
                self.cursor.execute(
                    insert_sql,
                    (
                        daily_tides.location.name,
                        daily_tides.location.area_id,
                        daily_tides.location.port_id,
                        tide.utc_datetime.isoformat(),
                        tide.type.value,
                        tide.height,
                    ),
                )
        self.con.commit()

    def get_location_by_port_id(self, port_id: PortID) -> TideLocation:
        sql = (
            f"SELECT location, area_id "
            f"FROM {self.table_name} "
            f"WHERE port_id = {port_id} LIMIT 1"
        )
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        return TideLocation(
            name=result[0], area_id=AreaID(result[1]), port_id=PortID(port_id)
        )

    def query_tide(
        self,
        port_id: PortID,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> Iterable[Tide]:
        sql = (
            f"SELECT utc_datetime, tide_type, height "
            f"FROM {self.table_name} "
            f"WHERE port_id = {port_id} AND "
            f"unixepoch(utc_datetime) >= {start_date.timestamp()} AND "
            f"unixepoch(utc_datetime) <={end_date.timestamp()}"
        )
        self.cursor.execute(sql)
        for record in self.cursor.fetchall():
            yield Tide(
                type=TideType(record[1]),
                utc_datetime=datetime.datetime.fromisoformat(record[0]),
                height=float(record[2]),
            )

    def close(self):
        self.con.close()
