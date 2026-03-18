from typing import Dict, NamedTuple, Optional
from .Data import champions
import typing


from BaseClasses import Location


class LOLLocation(Location):
    game: str = "League of Legends"


class LOLLocationData(NamedTuple):
    category: str
    code: Optional[int] = None


def get_locations_by_category(category: str) -> Dict[str, LOLLocationData]:
    location_dict: Dict[str, LOLLocationData] = {}
    for name, data in location_table.items():
        if data.category == category:
            location_dict.setdefault(name, data)

    return location_dict


location_table: Dict[str, LOLLocationData] = {}
for champion_id in champions:
    champion_name = champions[champion_id]["name"]
    location_table[champion_name + " - Assist Taking Dragon"]      = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 1)
    location_table[champion_name + " - Assist Taking Rift Herald"] = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 2)
    location_table[champion_name + " - Assist Taking Baron"]       = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 3)
    location_table[champion_name + " - Assist Taking Tower"]       = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 4)
    location_table[champion_name + " - Assist Taking Inhibitor"]   = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 5)
    location_table[champion_name + " - Enemy Nexus Destroyed"]     = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 10)
    location_table[champion_name + " - Get X Assists"]             = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 6)
    if "Support" in champions[champion_id]["tags"]:
        location_table[champion_name + " - Get X Ward Score"]      = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 7)
    if "Support" not in champions[champion_id]["tags"]:
        location_table[champion_name + " - Get X Kills"]           = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 8)
        location_table[champion_name + " - Get X Creep Score"]     = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 9)

for index in range(1, 101):
    location_table[f"Starting Champion {index}"] = LOLLocationData("Starting", 566_000000 + index)

event_location_table: Dict[str, LOLLocationData] = {
}

lookup_id_to_name: typing.Dict[int, str] = {data.code: item_name for item_name, data in location_table.items() if data.code}