from datetime import datetime
from collections import namedtuple

class TideRecord:
    def __init__(self, year: str, month: str, day: str, timezone: str, area_id:str, port_id: str):
        self.datetime = datetime.strptime(f'{year} {month} {day}', '%Y %m %d')
        self.area_id = area_id
        self.port_id = port_id
        self.timezone = timezone
        self.data = []

    def get_date(self):
        return self.datetime

    def get_measurements(self):
        return self.data

    def add_record(self, type=str, time=str, height=float):
        Tide = namedtuple("Tide", "type time height")
        self.data.append(Tide(type, time, height))

    def __key(self):
        return (self.datetime, self.timezone, self.port_id)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, TideRecord):
            return self.__key() == other.__key()
        return NotImplemented


# a = TideRecord('2022', 'June', '1', 'BST', '103')
# b = TideRecord('2022', 'June', '1', 'UTC', '103')
#
# print(a==b)