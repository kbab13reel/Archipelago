from typing import Dict, List, NamedTuple, Optional

from BaseClasses import MultiWorld, Region, Entrance
from .Locations import LOLLocation, location_table, get_locations_by_category
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
    
    aram = bool(options.aram_mode)
    for champion_id in champions:
        champion_name = champions[champion_id]["name"]
        if champion_name in possible_champions:
            if not aram:
                regions["Match"].locations.append(champion_name + " - Assist Taking Dragon")
                regions["Match"].locations.append(champion_name + " - Assist Taking Rift Herald")
                regions["Match"].locations.append(champion_name + " - Assist Taking Baron")
            regions["Match"].locations.append(champion_name + " - Assist Taking Tower")
            regions["Match"].locations.append(champion_name + " - Assist Taking Inhibitor")
            regions["Match"].locations.append(champion_name + " - Enemy Nexus Destroyed")
            regions["Match"].locations.append(champion_name + " - Get X Assists")
            if not aram and "Support" in champions[champion_id]["tags"]:
                regions["Match"].locations.append(champion_name + " - Get X Ward Score")
            if "Support" not in champions[champion_id]["tags"]:
                regions["Match"].locations.append(champion_name + " - Get X Kills")
                if not aram:
                    regions["Match"].locations.append(champion_name + " - Get X Creep Score")
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
