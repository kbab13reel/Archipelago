from BaseClasses import CollectionState, MultiWorld, LocationProgressType
from .Locations import get_locations_by_category
from .Data import champions

def has_item(state: CollectionState, player: int, item) -> bool:
    return state.has(item, player)

def has_at_least(state: CollectionState, player: int, item_name, item_qty_required) -> bool:
    return state.count(item_name, player) >= item_qty_required

def set_rules(multiworld: MultiWorld, player: int, options, required_lp, possible_champions):
    aram = bool(options.aram_mode)
    for champion_id in champions:
        champion_name = champions[champion_id]["name"]
        if champion_name in possible_champions:
            if not aram:
                multiworld.get_location(champion_name + " - Assist Taking Dragon"     , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
                multiworld.get_location(champion_name + " - Assist Taking Rift Herald", player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
                multiworld.get_location(champion_name + " - Assist Taking Baron"      , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
            multiworld.get_location(champion_name + " - Assist Taking Tower"      , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
            multiworld.get_location(champion_name + " - Assist Taking Inhibitor"  , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
            multiworld.get_location(champion_name + " - Get X Assists"            , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
            if not aram and "Support" in champions[champion_id]["tags"]:
                multiworld.get_location(champion_name + " - Get X Ward Score"     , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
            if "Support" not in champions[champion_id]["tags"]:
                multiworld.get_location(champion_name + " - Get X Kills"          , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
                if not aram:
                    multiworld.get_location(champion_name + " - Get X Creep Score"    , player).access_rule = lambda state, champion_name = champion_name: has_item(state, player, champion_name)
    
    # Win condition.
    multiworld.completion_condition[player] = lambda state: has_at_least(state, player, "LP", required_lp)
