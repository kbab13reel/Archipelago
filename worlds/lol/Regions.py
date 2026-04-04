from typing import Dict, List, NamedTuple, Optional

from BaseClasses import MultiWorld, Region, Entrance
from .Locations import LOLLocation, location_table, get_locations_by_category, get_champion_location_suffixes
from .Data import champions


class LOLRegionData(NamedTuple):
    locations: Optional[List[str]]
    region_exits: Optional[List[str]]


def create_regions(multiworld: MultiWorld, player: int, options, possible_champions):
    regions: Dict[str, LOLRegionData] = {
        "Menu":  LOLRegionData(None, ["Match"]),
        "Match": LOLRegionData([],   []),
    }

    # Set up locations

    enabled_checks = options.enabled_checks.value
    sst = bool(options.support_special_treatment)
    for champion_id in champions:
        champion_name = champions[champion_id]["name"]
        if champion_name in possible_champions:
            for suffix in get_champion_location_suffixes(champion_id, enabled_checks, sst):
                regions["Match"].locations.append(champion_name + suffix)
    for i in range(min(options.starting_champions, len(possible_champions))):
        regions["Match"].locations.append("Starting Champion " + str(i+1))
    
    # Set up the regions correctly.
    for name, data in regions.items():
        multiworld.regions.append(create_region(multiworld, player, name, data))
    
    multiworld.get_entrance("Match", player).connect(multiworld.get_region("Match", player))


def create_region(multiworld: MultiWorld, player: int, name: str, data: LOLRegionData):
    region = Region(name, player, multiworld)
    if data.locations:
        for loc_name in data.locations:
            loc_data = location_table.get(loc_name)
            location = LOLLocation(player, loc_name, loc_data.code if loc_data else None, region)
            region.locations.append(location)

    if data.region_exits:
        for exit in data.region_exits:
            entrance = Entrance(player, exit, region)
            region.exits.append(entrance)

    return region
