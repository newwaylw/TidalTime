from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, NewType

AreaID = NewType("AreaID", str)
PortID = NewType("PortID", str)


class TideType(Enum):
    LOW = "Low"
    HIGH = "High"


@dataclass
class TideLocation:
    name: str
    area_id: AreaID
    port_id: PortID


@dataclass
class Tide:
    type: TideType
    utc_datetime: datetime
    height: float


@dataclass
class DailyTideRecord:
    location: TideLocation
    tides: List[Tide]
