from typing import List, TYPE_CHECKING

from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld, World
from .Items import LOLItem, item_table, get_items_by_category
from .Locations import LOLLocation, location_table, get_locations_by_category
from .Options import LOLOptions
from .Regions import create_regions
from .Rules import set_rules
from .Data import champions
from worlds.LauncherComponents import Component, components, Type, launch_subprocess

if TYPE_CHECKING:
    from BaseClasses import MultiWorld



def launch_client():
    from .Client import launch
    launch_subprocess(launch, name="LOL Client")


components.append(Component("LOL Client", "LOLClient", func=launch_client, component_type=Type.CLIENT))

class LOLWeb(WebWorld):
    theme = "ocean"
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the League of Legends AP Randomizer software on your computer. This guide covers single-player, "
        "multiworld, and related software.",
        "English",
        "lol_en.md",
        "LOL/en",
        ["Gicu"]
    )]

class LOLWorld(World):
    """
    League of Legends (LoL), commonly referred to as League, is a 2009 multiplayer online battle arena video game developed and published by Riot Games.
    """
    game = "League of Legends"
    data_version = 1
    options_dataclass = LOLOptions
    options: LOLOptions
    topology_present = True
    required_client_version = (0, 3, 5)
    web = LOLWeb()

    item_name_to_id = {name: data.code for name, data in item_table.items()}
    location_name_to_id = {name: data.code for name, data in location_table.items()}
    
    def __init__(self, multiworld: "MultiWorld", player: int):
        super(LOLWorld, self).__init__(multiworld, player)
        self.possible_champions = []
        self.starting_champion_names = []
        self.added_lp = 0

    def create_items(self):
        item_pool: List[LOLItem] = []
        self.choose_possible_champions()
        self.choose_starting_champions()
        for index, champion_name in enumerate(self.starting_champion_names, start=1):
            self.multiworld.get_location("Starting Champion " + str(index), self.player).place_locked_item(self.create_item(champion_name))

        total_locations = len(self.multiworld.get_unfilled_locations(self.player))
        for name, data in item_table.items():
            if name in self.possible_champions and name not in self.starting_champion_names:
                item_pool += [self.create_item(name) for _ in range(0, 1)]

        remaining_slots = max(0, total_locations - len(item_pool))
        self.added_lp = min(int(self.options.total_lp_count), remaining_slots)
        for _ in range(self.added_lp):
            item_pool.append(self.create_item("LP"))

        filler_items = list(get_items_by_category("Filler", []).keys())
        while len(item_pool) < total_locations:
            item_pool.append(self.create_item(self.random.choice(filler_items)))

        self.multiworld.itempool += item_pool
        
    def create_item(self, name: str) -> LOLItem:
        data = item_table[name]
        return LOLItem(name, data.classification, data.code, self.player)

    def set_rules(self):
        self.choose_possible_champions()
        set_rules(self.multiworld, self.player, self.options, int(self.added_lp * (self.options.required_lp / 100)), self.possible_champions)

    def create_regions(self):
        self.choose_possible_champions()
        create_regions(self.multiworld, self.player, self.options, self.possible_champions)
    
    def fill_slot_data(self) -> dict:
        self.choose_possible_champions()
        self.choose_starting_champions()
        slot_data = {"Required CS":      int(self.options.required_creep_score)
                    ,"Required VS":      int(self.options.required_vision_score)
                    ,"Required Kills":   int(self.options.required_kills)
                    ,"Required Assists": int(self.options.required_assists)
                    ,"Configured Total LP": int(self.options.total_lp_count)
                    ,"Total LP":         int(self.added_lp)
                    ,"Required LP Percentage": int(self.options.required_lp)
                    ,"Required LP":      int(self.added_lp * (self.options.required_lp / 100))
                    ,"Starting Champion Count": int(self.options.starting_champions)
                    ,"Champion Subset Count": int(self.options.champion_subset_count)
                    ,"ARAM Mode":        int(self.options.aram_mode)
                    ,"Selected Champions": sorted(self.possible_champions)
                    ,"Starting Champions": list(self.starting_champion_names)
                    ,"Active Locations": self.get_active_location_names()}
        return slot_data
    
    def choose_possible_champions(self):
        if len(self.possible_champions) == 0:
            for champion_id in champions:
                champion_name = champions[champion_id]["name"]
                if champion_name in self.options.champions.value:
                    self.possible_champions.append(champion_name)
            if len(self.possible_champions) > self.options.champion_subset_count:
                self.possible_champions = self.random.sample(self.possible_champions, self.options.champion_subset_count)

    def choose_starting_champions(self):
        if len(self.starting_champion_names) == 0:
            self.choose_possible_champions()
            self.starting_champion_names = self.random.sample(
                self.possible_champions,
                min(self.options.starting_champions, len(self.possible_champions))
            )

    def get_active_location_names(self) -> List[str]:
        self.choose_possible_champions()
        active_locations: List[str] = []
        aram = bool(self.options.aram_mode)

        for champion_id in champions:
            champion_name = champions[champion_id]["name"]
            if champion_name not in self.possible_champions:
                continue
            if not aram:
                active_locations.append(champion_name + " - Assist Taking Dragon")
                active_locations.append(champion_name + " - Assist Taking Rift Herald")
                active_locations.append(champion_name + " - Assist Taking Baron")
            active_locations.append(champion_name + " - Assist Taking Tower")
            active_locations.append(champion_name + " - Assist Taking Inhibitor")
            active_locations.append(champion_name + " - Get X Assists")
            if not aram and "Support" in champions[champion_id]["tags"]:
                active_locations.append(champion_name + " - Get X Ward Score")
            if "Support" not in champions[champion_id]["tags"]:
                active_locations.append(champion_name + " - Get X Kills")
                if not aram:
                    active_locations.append(champion_name + " - Get X Creep Score")

        for index in range(1, min(int(self.options.starting_champions), len(self.possible_champions)) + 1):
            active_locations.append("Starting Champion " + str(index))

        active_locations.append("Game Win - Enemy Nexus Destroyed")

        return active_locations