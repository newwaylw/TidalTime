from datetime import datetime, timedelta
from collections import namedtuple


class TideRecord:
    def __init__(self, year: int, month: int, day: int, day_offset: int, timezone: str, area_id: str, port_id: str):
        self.record_datetime = datetime.strptime(f'{year} {month} {day}', '%Y %m %d')
        self.record_datetime += timedelta(days=day_offset)
        self.area_id = area_id
        self.port_id = port_id
        self.timezone = timezone
        self.data = []

    def get_date(self):
        return self.record_datetime

    def get_measurements(self):
        return self.data

    def add_record(self, type=str, time=str, height=float):
        self.data.append((type, time, height))

    def __key(self):
        return self.record_datetime, self.timezone, self.port_id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, TideRecord):
            return self.__key() == other.__key()
        return NotImplemented
