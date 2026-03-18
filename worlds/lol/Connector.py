import PySimpleGUI as sg
import json
import requests
import os

###GET CHAMPION DATA###
versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
most_recent_version = requests.get(versions_url).json()[0]
champions_url = "https://ddragon.leagueoflegends.com/cdn/" + str(most_recent_version) + "/data/en_US/champion.json"
champions = {}
champion_data = requests.get(champions_url).json()["data"]

for champion in list(champion_data.keys()):
    champions[int(champion_data[champion]["key"])] = champion_data[champion]

###SET GLOBAL VARIABLES###
url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
unlocked_champion_ids = []
total_lp_gained = 0
in_match = False
tracked_teammates = set()
game_values = {
    "required_assists": 0,
    "required_cs"     : 0,
    "required_kills"  : 0,
    "required_lp"     : 0,
    "required_vs"     : 0,
    "current_lp"      : 0,
    "starting_champions": 0
}

###SET UP GAME COMMUNICATION PATH###
if "localappdata" in os.environ:
    game_communication_path = os.path.expandvars(r"%localappdata%/LOLAP")
else:
    game_communication_path = os.path.expandvars(r"$HOME/LOLAP")
if not os.path.exists(game_communication_path):
    os.makedirs(game_communication_path)


###DEFINE FUNCTIONS###
def get_game_data():
    try:
        return requests.get(url, verify=False).json()
    except:
        return None

def get_items(game_values):
    game_values["current_lp"] = 0
    unlocked_champion_ids.clear()
    for root, dirs, files in os.walk(game_communication_path):
        for file in files:
            if file.startswith("AP"):
                with open(os.path.join(game_communication_path, file), 'r') as f:
                    item_id = int(f.readline())
                    decoded_item = item_id - 565000000
                    if decoded_item == 0:
                        game_values["current_lp"] = game_values["current_lp"] + 1
                    elif decoded_item in champions:
                        unlocked_champion_ids.append(decoded_item)
                    f.close()

def read_cfg(game_values):
    for root, dirs, files in os.walk(game_communication_path):
        if "Required_Assists.cfg" in files:
            with open(os.path.join(game_communication_path, "Required_Assists.cfg"), 'r') as f:
                game_values["required_assists"] = int(f.readline())
        else:
            game_values["required_assists"] = 0
        if "Required_CS.cfg" in files:
            with open(os.path.join(game_communication_path, "Required_CS.cfg"), 'r') as f:
                game_values["required_cs"] = int(f.readline())
        else:
            game_values["required_cs"] = 0
        if "Required_Kills.cfg" in files:
            with open(os.path.join(game_communication_path, "Required_Kills.cfg"), 'r') as f:
                game_values["required_kills"] = int(f.readline())
        else:
            game_values["required_kills"] = 0
        if "Required_LP.cfg" in files:
            with open(os.path.join(game_communication_path, "Required_LP.cfg"), 'r') as f:
                game_values["required_lp"] = int(f.readline())
        else:
            game_values["required_lp"] = 0
        if "Required_VS.cfg" in files:
            with open(os.path.join(game_communication_path, "Required_VS.cfg"), 'r') as f:
                game_values["required_vs"] = int(f.readline())
        else:
            game_values["required_vs"] = 0
        if "Starting_Champion_Count.cfg" in files:
            with open(os.path.join(game_communication_path, "Starting_Champion_Count.cfg"), 'r') as f:
                game_values["starting_champions"] = max(0, int(f.readline()))
        else:
            game_values["starting_champions"] = 0

def display_champion_list(window):
    champion_table_rows = []
    for champion_id in unlocked_champion_ids:
        champion_table_rows.append([champions[champion_id]["name"], champion_id])
    window["Champions Unlocked Table"].update(values=champion_table_rows)

def display_values(window, game_values):
    value_table_rows = []
    value_table_rows.append(['Required Kills:'       , str(game_values["required_kills"])])
    value_table_rows.append(['Required Assists:'     , str(game_values["required_assists"])])
    value_table_rows.append(['Required CS:'          , str(game_values["required_cs"])])
    value_table_rows.append(['Required VS:'          , str(game_values["required_vs"])])
    value_table_rows.append(['Required LP:'          , str(game_values["required_lp"])])
    value_table_rows.append(['Current LP:'           , str(game_values["current_lp"])])
    window["Values Table"].update(values=value_table_rows)

def send_starting_champion_check(game_values):
    for i in range(1, game_values["starting_champions"] + 1):
        with open(os.path.join(game_communication_path, f"send{566000000 + i}"), 'w') as f:
            f.close()

def check_lp_for_victory(game_values):
    if game_values["current_lp"] >= game_values["required_lp"] and game_values["required_lp"] != 0:
        with open(os.path.join(game_communication_path, "victory"), 'w') as f:
            f.close()

def won_game(game_data):
    for event in game_data["events"]["Events"]:
        if event.get("EventName") == "GameEnd" and event.get("Result") == "Win":
            return True
    return False

def get_player_name(game_data):
    return game_data["activePlayer"]["riotIdGameName"]

def get_champion_name(game_data, player_name):
    for player in game_data["allPlayers"]:
        if player["riotIdGameName"] == player_name:
            return player["championName"]

def get_champion_id(champion_name):
    for champion_id in champions:
        if champions[champion_id]["name"] == champion_name:
            return champion_id

def get_player_data(game_data, player_name):
    for player in game_data["allPlayers"]:
        if player["riotIdGameName"] == player_name:
            return player
    return None

def get_available_teammates(game_data):
    player_name = get_player_name(game_data)
    player_data = get_player_data(game_data, player_name)
    if player_data is None:
        return []

    player_team = player_data.get("team")
    teammate_names = []
    for player in game_data["allPlayers"]:
        if player.get("team") == player_team and player["riotIdGameName"] != player_name:
            teammate_names.append(player["riotIdGameName"])
    return sorted(teammate_names)

def update_teammate_selector(window, teammate_names):
    valid_teammates = sorted(tracked_teammates.intersection(teammate_names))
    set_to_index = [teammate_names.index(teammate_name) for teammate_name in valid_teammates]
    window["Tracked Teammates List"].update(values=teammate_names, set_to_index=set_to_index)

def get_tracked_players(game_data):
    player_name = get_player_name(game_data)
    teammate_names = set(get_available_teammates(game_data))
    selected_teammates = sorted(tracked_teammates.intersection(teammate_names))
    return [player_name] + selected_teammates

def took_tower(game_data, player_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == "TurretKilled" and event["KillerName"] == player_name:
            return True
    return False

def assisted_tower(game_data, player_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == "TurretKilled" and (event["KillerName"] == player_name or player_name in event["Assisters"]):
            return True
    return False

def took_inhibitor(game_data, player_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == "InhibKilled" and event["KillerName"] == player_name:
            return True
    return False

def assisted_inhibitor(game_data, player_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == "InhibKilled" and (event["KillerName"] == player_name or player_name in event["Assisters"]):
            return True
    return False

def took_epic_monster(game_data, player_name, monster_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == monster_name + "Kill" and event["KillerName"] == player_name:
            return True
    return False

def assisted_epic_monster(game_data, player_name, monster_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == monster_name + "Kill" and (event["KillerName"] == player_name or player_name in event["Assisters"]):
            return True
    return False

def stole_epic_monster(game_data, player_name, monster_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == monster_name + "Kill" and (event["KillerName"] == player_name or player_name in event["Assisters"]) and str(event["Stolen"]) == "True":
            return True
    return False

def assisted_kill(game_data, player_name):
    for event in game_data["events"]["Events"]:
        if event["EventName"] == "ChampionKill" and (event["KillerName"] == player_name or player_name in event["Assisters"]):
            return True
    return False

def player_vision_score(game_data, player_name):
    for player in game_data["allPlayers"]:
        if player["riotIdGameName"] == player_name:
            return player["scores"]["wardScore"]
    return 0

def player_creep_score(game_data, player_name):
    for player in game_data["allPlayers"]:
        if player["riotIdGameName"] == player_name:
            return player["scores"]["creepScore"]
    return 0

def player_kills(game_data, player_name):
    for player in game_data["allPlayers"]:
        if player["riotIdGameName"] == player_name:
            return player["scores"]["kills"]
    return 0

def player_assists(game_data, player_name):
    for player in game_data["allPlayers"]:
        if player["riotIdGameName"] == player_name:
            return player["scores"]["assists"]
    return 0

def vision_score_above(game_data, player_name, score_target):
    return player_vision_score(game_data, player_name) >= score_target and score_target > 0

def creep_score_above(game_data, player_name, score_target):
    return player_creep_score(game_data, player_name) >= score_target and score_target > 0

def kills_above(game_data, player_name, score_target):
    return player_kills(game_data, player_name) >= score_target and score_target > 0

def assists_above(game_data, player_name, score_target):
    return player_assists(game_data, player_name) >= score_target and score_target > 0

def get_objectives_complete_for_player(game_data, game_values, player_name):
    objectives_complete = []
    champion_name = get_champion_name(game_data, player_name)
    if champion_name is None:
        return objectives_complete, None

    champion_id = get_champion_id(champion_name)
    if champion_id is None:
        return objectives_complete, None

    if champion_id in unlocked_champion_ids:
        if assisted_epic_monster(game_data, player_name, "Dragon"):
            objectives_complete.append(1)
        if assisted_epic_monster(game_data, player_name, "Herald") or assisted_epic_monster(game_data, player_name, "Horde"):
            objectives_complete.append(2)
        if assisted_epic_monster(game_data, player_name, "Baron"):
            objectives_complete.append(3)
        if assisted_tower(game_data, player_name):
            objectives_complete.append(4)
        if assisted_inhibitor(game_data, player_name):
            objectives_complete.append(5)
        if won_game(game_data):
            objectives_complete.append(10)
        if assists_above(game_data, player_name, game_values["required_assists"]):
            objectives_complete.append(6)
        if vision_score_above(game_data, player_name, game_values["required_vs"]):
            objectives_complete.append(7)
        if kills_above(game_data, player_name, game_values["required_kills"]):
            objectives_complete.append(8)
        if creep_score_above(game_data, player_name, game_values["required_cs"]):
            objectives_complete.append(9)
    return objectives_complete, champion_id

def get_objectives_complete(game_data, game_values):
    for player_name in get_tracked_players(game_data):
        objectives_complete, champion_id = get_objectives_complete_for_player(game_data, game_values, player_name)
        if champion_id is not None:
            send_locations(objectives_complete, champion_id)

def send_locations(objectives_complete, champion_id):
    for objective_id in objectives_complete:
        with open(os.path.join(game_communication_path, "send" + str(566000000 + (champion_id * 100) + objective_id)), 'w') as f:
            f.close()

sg.theme('DarkAmber')
layout = [  [
                sg.Text('In Match: No', justification = 'center', key = "In Match Text"),
                sg.Button('Check for Match', key = "Check for Match Button", disabled_button_color = "blue")
            ],
            [   
                sg.Column(
                [   [sg.Text("Champions Unlocked")],
                    [sg.Table(
                        [
                        ], headings = ["Champion Name", "Champion ID"], key = "Champions Unlocked Table")]
                ]),
                sg.Column(
                [
                    [sg.Text("Required Values")],
                    [sg.Table(
                        [
                        ], headings = ["Value Type", "Value Amount"], key = "Values Table")]
               ]),
                sg.Column(
                [
                    [sg.Text("Tracked Teammates")],
                    [sg.Listbox(
                        values = [],
                        select_mode = sg.LISTBOX_SELECT_MODE_MULTIPLE,
                        size = (24, 6),
                        enable_events = True,
                        key = "Tracked Teammates List")]
               ])
            ]
        ]

window = sg.Window('LOL AP', layout)
while True:
    game_data = None
    event, values = window.read(timeout=2000)
    if event == sg.WIN_CLOSED:
        break
    if event == 'Check for Match Button':
        in_match = True
    if event == "Tracked Teammates List":
        tracked_teammates = set(values["Tracked Teammates List"])
    check_lp_for_victory(game_values)
    get_items(game_values)
    read_cfg(game_values)
    display_champion_list(window)
    display_values(window, game_values)
    send_starting_champion_check(game_values)
    if in_match:
        game_data = get_game_data()
    if game_data is None:
        window["In Match Text"].update("In Match: No Match Found")
        update_teammate_selector(window, [])
        in_match = False
    else:
        window["In Match Text"].update("In Match: In Match")
        update_teammate_selector(window, get_available_teammates(game_data))
        get_objectives_complete(game_data, game_values)

window.close()