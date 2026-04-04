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


# Maps enabled check option names to their location name suffix
CHECK_TO_LOCATION: Dict[str, str] = {
    "Dragon":       " - Assist Taking Dragon",
    "Herald":       " - Assist Taking Rift Herald",
    "Baron":        " - Assist Taking Baron",
    "Tower":        " - Assist Taking Tower",
    "Inhibitor":    " - Assist Taking Inhibitor",
    "Game Win":     " - Enemy Nexus Destroyed",
    "Assists":      " - Get X Assists",
    "Vision Score": " - Get X Ward Score",
    "Kills":        " - Get X Kills",
    "Creep Score":  " - Get X Creep Score",
}

_SUPPORT_ONLY_CHECKS = frozenset({"Vision Score"})
_NON_SUPPORT_CHECKS  = frozenset({"Kills", "Creep Score"})


def get_champion_location_suffixes(champion_id, enabled_checks, support_special_treatment: bool) -> list:
    """Return the list of active location suffixes for a champion given the current options."""
    is_support = "Support" in champions[champion_id]["tags"]
    result = []
    for check, suffix in CHECK_TO_LOCATION.items():
        if check not in enabled_checks:
            continue
        if support_special_treatment:
            if check in _SUPPORT_ONLY_CHECKS and not is_support:
                continue
            if check in _NON_SUPPORT_CHECKS and is_support:
                continue
        result.append(suffix)
    return result


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
    location_table[champion_name + " - Get X Ward Score"]          = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 7)
    location_table[champion_name + " - Get X Kills"]               = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 8)
    location_table[champion_name + " - Get X Creep Score"]         = LOLLocationData("Objective", 566_000000 + (int(champion_id) * 100) + 9)

for index in range(1, 101):
    location_table[f"Starting Champion {index}"] = LOLLocationData("Starting", 566_000000 + index)

event_location_table: Dict[str, LOLLocationData] = {
}

lookup_id_to_name: typing.Dict[int, str] = {data.code: item_name for item_name, data in location_table.items() if data.code}