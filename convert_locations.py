import json
from tidal.tide_dto import TideLocation, AreaID, PortID
from tidal.utils.store import JSONStore
from pathlib import Path

# in view-source:https://www.bbc.co.uk/weather/coast-and-sea/tide-tables
# there is a json object containing all tide locations
# this script converts that json string into the TideLocation DTO jsonl file
# that is used by `collect_tides_info.py`

with open("bbc_tide_locations.json", "r") as f:
    data = json.load(f)
    tide_location_list = []

    for country in data.get("countries", []):
        if "regions" in country:
            for region in country.get("regions", []):
                region_id = region["id"]
                region_name = region["name"]
                for location in region.get("locations", []):
                    location_name = location["name"]
                    tide_location_list.append(TideLocation(region_name=region_name,
                                                             name=location_name,
                                                             area_id=AreaID(region_id),
                                                             port_id=PortID(location["id"]))
                                              )
        else:
            for location in country.get("locations", []):
                region_name = country.get("name")
                region_id = country.get("id")
                location_name = location["name"]
                tide_location_list.append(TideLocation(region_name=region_name,
                                                       name=location_name,
                                                       area_id=AreaID(region_id),
                                                       port_id=PortID(location["id"]))
                                          )

    json_store = JSONStore()
    json_store.save_lines(tide_location_list, Path("locations.jsonl.gz"))
