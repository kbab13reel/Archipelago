from dataclasses import dataclass, asdict

from Options import Choice, Range, Option, Toggle, DeathLink, DefaultOnToggle, OptionSet, PerGameCommonOptions

from .Data import champions



class RequiredLPPercentage(Range):
    """
    What percentage of total LP available do you need to collect to win?
    """
    default = 50
    range_start = 30
    range_end = 100
    display_name = "Required LP Percentage"


class TotalLPCount(Range):
    """
    Total LP items to place in the world.
    """
    default = 80
    range_start = 1
    range_end = 500
    display_name = "Total LP Count"

class Champions(OptionSet):
    """
    Which champions are possibly included in the item pool?
    """
    display_name = "Champions"
    valid_keys = [champions[champion_id]["name"] for champion_id in champions]
    default = sorted(set([champions[champion_id]["name"] for champion_id in champions]))

class RequiredCreepScore(Range):
    """
    Required CS to complete CS checks
    """
    default = 100
    range_start = 50
    range_end = 400
    display_name = "Required Creep Score"

class RequiredVisionScore(Range):
    """
    Required VS to complete VS checks
    """
    default = 30
    range_start = 10
    range_end = 100
    display_name = "Required Vison Score"

class RequiredKills(Range):
    """
    Required Kills to complete Kill checks
    """
    default = 3
    range_start = 1
    range_end = 15
    display_name = "Required Kills"

class RequiredAssists(Range):
    """
    Required Assists to complete Assist checks
    """
    default = 5
    range_start = 3
    range_end = 30
    display_name = "Required Assists"

class StartingChampions(Range):
    """
    Number of champions in your starting inventory
    """
    default = 3
    range_start = 1
    range_end = 100
    display_name = "Starting Champions"

class ChampionSubsetCount(Range):
    """
    Number of champions to randomly select for the item pool of those listed provided.
    """
    default = 20
    range_start = 1
    range_end = 200
    display_name = "Champion Subset Count"

class ARAMMode(Toggle):
    """
    Enable ARAM mode. The only checks enabled are:
    Tower, Inhibitor, Assists, and Kills.
    """
    display_name = "ARAM Mode"

@dataclass
class LOLOptions(PerGameCommonOptions):
    champions: Champions
    required_creep_score: RequiredCreepScore
    required_vision_score: RequiredVisionScore
    required_kills: RequiredKills
    required_assists: RequiredAssists
    total_lp_count: TotalLPCount
    required_lp: RequiredLPPercentage
    starting_champions: StartingChampions
    champion_subset_count: ChampionSubsetCount
    aram_mode: ARAMMode