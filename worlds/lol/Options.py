from dataclasses import dataclass, asdict

from Options import Choice, Range, Option, Toggle, DeathLink, DefaultOnToggle, OptionSet, PerGameCommonOptions, OptionGroup

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
    Higher then the total number of champions will just use all champions listed.
    """
    default = 20
    range_start = 1
    range_end = 200
    display_name = "Champion Subset Count"

class EnabledChecks(OptionSet):
    """
    Which check types are active for each champion?
    All check types are enabled by default: "Dragon", "Herald", "Baron", "Tower", "Inhibitor", 
    "Game Win", "Assists", "Kills", "Creep Score", "Vision Score"
    To recreate the old ARAM mode, use: "Tower", "Inhibitor", "Game Win", "Assists", "Kills"
    """
    display_name = "Enabled Checks"
    valid_keys = ["Dragon", "Herald", "Baron", "Tower", "Inhibitor", "Game Win",
                  "Assists", "Kills", "Creep Score", "Vision Score"]
    default = sorted({"Dragon", "Herald", "Baron", "Tower", "Inhibitor", "Game Win",
                      "Assists", "Kills", "Creep Score", "Vision Score"})

class SupportSpecialTreatment(DefaultOnToggle):
    """
    When enabled, support-role champions will not receive Kill and Creep Score checks,
    and Vision Score checks will only apply to support champions.
    (This was enabled by default on version <=0.2.0)
    Disable this to give all champions identical checks.
    """
    display_name = "Support Special Treatment"

class WinCompletesChampion(Toggle):
    """
    If enabled, winning a game with a champion (Enemy Nexus Destroyed check) will
    automatically complete all remaining checks for that champion.
    """
    display_name = "Win Completes Champion"

@dataclass
class LOLOptions(PerGameCommonOptions):
    champions: Champions
    starting_champions: StartingChampions
    champion_subset_count: ChampionSubsetCount
    enabled_checks: EnabledChecks
    support_special_treatment: SupportSpecialTreatment
    win_completes_champion: WinCompletesChampion
    required_creep_score: RequiredCreepScore
    required_vision_score: RequiredVisionScore
    required_kills: RequiredKills
    required_assists: RequiredAssists
    total_lp_count: TotalLPCount
    required_lp: RequiredLPPercentage


lol_option_groups = [
    OptionGroup("Champion Options", [
        Champions,
        StartingChampions,
        ChampionSubsetCount,
    ]),
    OptionGroup("Check Options", [
        EnabledChecks,
        SupportSpecialTreatment,
        WinCompletesChampion,
        RequiredCreepScore,
        RequiredVisionScore,
        RequiredKills,
        RequiredAssists,
    ]),
    OptionGroup("Goal Options", [
        TotalLPCount,
        RequiredLPPercentage,
    ]),
]