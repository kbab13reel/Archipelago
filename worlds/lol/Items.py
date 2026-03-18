from typing import Dict, NamedTuple, Optional
from .Data import champions

from BaseClasses import Item, ItemClassification


class LOLItem(Item):
    game: str = "League of Legends"


class LOLItemData(NamedTuple):
    category: str
    sub: str = "None"
    code: Optional[int] = None
    classification: ItemClassification = ItemClassification.filler
    max_quantity: int = 1
    weight: int = 1


def get_items_by_category(category: str, disclude: list) -> Dict[str, LOLItemData]:
    item_dict: Dict[str, LOLItemData] = {}
    for name, data in item_table.items():
        if data.category == category and all(x not in name for x in disclude):
            item_dict.setdefault(name, data)

    return item_dict


item_table: Dict[str, LOLItemData] = {}
for champion_id in champions:
    item_table[champions[champion_id]["name"]] = LOLItemData("Champion", code = 565_000000 + int(champion_id), classification = ItemClassification.progression, max_quantity = 1, weight = 1)
item_table["LP"] = LOLItemData("Win Condition", code = 565_000000, classification = ItemClassification.progression, max_quantity = -1, weight = 1)

filler_item_names = [
    "Black Spear",
    "Cull",
    "Dark Seal",
    "Doran's Blade",
    "Doran's Ring",
    "Doran's Shield",
    "Guardian's Amulet",
    "Guardian's Blade",
    "Guardian's Dirk",
    "Guardian's Hammer",
    "Guardian's Horn",
    "Guardian's Orb",
    "Guardian's Shroud",
    "Gustwalker Hatchling",
    "Mosstomper Seedling",
    "Scorchclaw Pup",
    "Tear of the Goddess",
    "World Atlas",
    "Amplifying Tome",
    "B. F. Sword",
    "Blasting Wand",
    "Cloak of Agility",
    "Cloth Armor",
    "Dagger",
    "Faerie Charm",
    "Glowing Mote",
    "Long Sword",
    "Needlessly Large Rod",
    "Null-Magic Mantle",
    "Pickaxe",
    "Rejuvenation Bead",
    "Ruby Crystal",
    "Sapphire Crystal",
]

for index, item_name in enumerate(filler_item_names, start=1):
    item_table[item_name] = LOLItemData(
        "Filler",
        code=565_100000 + index,
        classification=ItemClassification.filler,
        max_quantity=-1,
        weight=1,
    )


event_item_table: Dict[str, LOLItemData] = {
}