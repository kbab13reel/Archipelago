import PySimpleGUI as sg
import json
import requests
import os
import ast
import sys

###GET VERSION###
def _get_world_version() -> str:
    try:
        base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, 'archipelago.json'), 'r') as f:
            return json.load(f).get('world_version', '')
    except Exception:
        return ''

_WORLD_VERSION = _get_world_version()
_WINDOW_TITLE = f"LOL AP v{_WORLD_VERSION}" if _WORLD_VERSION else "LOL AP"

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
    "starting_champions": 0,
    "enabled_checks"  : None,
    "support_special_treatment": True
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
        if "Enabled_Checks.cfg" in files:
            with open(os.path.join(game_communication_path, "Enabled_Checks.cfg"), 'r') as f:
                game_values["enabled_checks"] = ast.literal_eval(f.read())
        else:
            game_values["enabled_checks"] = None
        if "Support_Special_Treatment.cfg" in files:
            with open(os.path.join(game_communication_path, "Support_Special_Treatment.cfg"), 'r') as f:
                game_values["support_special_treatment"] = bool(int(f.read().strip()))
        else:
            game_values["support_special_treatment"] = True

def display_champion_list(window):
    # Try to read active locations and mapping from the client slot data
    active_locations = None
    active_location_ids = None
    checked_location_ids = None
    try:
        path = os.path.join(game_communication_path, "Active_Locations.cfg")
        if os.path.exists(path):
            with open(path, 'r') as f:
                active_locations = ast.literal_eval(f.read())
    except Exception:
        active_locations = None

    try:
        path = os.path.join(game_communication_path, "Active_Location_IDs.cfg")
        if os.path.exists(path):
            with open(path, 'r') as f:
                active_location_ids = ast.literal_eval(f.read())
    except Exception:
        active_location_ids = None

    try:
        path = os.path.join(game_communication_path, "Checked_Locations.cfg")
        if os.path.exists(path):
            with open(path, 'r') as f:
                checked_location_ids = set(ast.literal_eval(f.read()))
    except Exception:
        checked_location_ids = None

    # Build totals per champion from active_locations (names)
    totals = {}
    done = {}
    if active_locations is not None:
        for name in active_locations:
            if name.startswith("Starting Champion"):
                champ_key = "Starting"
            else:
                champ_key = name.split(" - ", 1)[0]
            totals[champ_key] = totals.get(champ_key, 0) + 1
            done.setdefault(champ_key, 0)

    # If we have id->name mapping, use checked ids to count done per champion
    if active_location_ids is not None and checked_location_ids is not None:
        # invert mapping to id -> name
        id_to_name = {int(v): k for k, v in active_location_ids.items() if v is not None}
        for lid in checked_location_ids:
            name = id_to_name.get(int(lid))
            if name:
                if name.startswith("Starting Champion"):
                    champ_key = "Starting"
                else:
                    champ_key = name.split(" - ", 1)[0]
                done[champ_key] = done.get(champ_key, 0) + 1

    # Fallback: if mappings aren't available, fall back to previous per-champion send file counting
    champion_table_rows = []
    if active_locations is None or active_location_ids is None or checked_location_ids is None:
        def count_remaining(champion_id: int) -> int:
            prefix = "send" + str(566000000 + (champion_id * 100))
            cnt = 0
            try:
                for filename in os.listdir(game_communication_path):
                    if filename.startswith(prefix):
                        cnt += 1
            except Exception:
                cnt = 0
            total_objectives = 10
            return max(0, total_objectives - cnt)

        for champion_id in unlocked_champion_ids:
            remaining = count_remaining(champion_id)
            champion_table_rows.append([champions[champion_id]["name"], str(remaining)])
    else:
        for champion_id in unlocked_champion_ids:
            name = champions[champion_id]["name"]
            total = totals.get(name, 0)
            done_count = done.get(name, 0)
            remaining = max(0, total - done_count)
            champion_table_rows.append([name, str(remaining)])

    # honor current sort preference if set on the window object
    sort_pref = window.metadata.get("champion_sort", "name") if hasattr(window, "metadata") else "name"
    reverse = False
    if sort_pref.endswith("_desc"):
        reverse = True
        sort_pref = sort_pref.replace("_desc", "")
    if sort_pref == "name":
        champion_table_rows.sort(key=lambda r: r[0], reverse=reverse)
    elif sort_pref == "remaining":
        champion_table_rows.sort(key=lambda r: int(r[1]), reverse=reverse)

    # Cache for remaining-checks panel
    window.metadata["active_location_ids"] = active_location_ids
    window.metadata["checked_location_ids"] = checked_location_ids

    # Auto-select first champion if none selected yet
    if window.metadata.get("selected_champion_id") is None and champion_table_rows:
        window.metadata["selected_champion_id"] = get_champion_id(champion_table_rows[0][0])

    window["Champions Unlocked Table"].update(values=champion_table_rows)

def display_values(window, game_values):
    selected_champion_id = window.metadata.get("selected_champion_id") if hasattr(window, "metadata") else None
    active_location_ids  = window.metadata.get("active_location_ids")  if hasattr(window, "metadata") else None
    checked_location_ids = window.metadata.get("checked_location_ids") if hasattr(window, "metadata") else None

    if selected_champion_id is None or selected_champion_id not in champions:
        window["Values Table"].update(values=[])
        return

    champion_name = champions[selected_champion_id]["name"]

    if active_location_ids is None or checked_location_ids is None:
        window["Values Table"].update(values=[])
        return

    checked_ids = {int(x) for x in checked_location_ids}
    prefix = champion_name + " - "

    # Map the fixed "X" placeholder to the real required number
    x_substitutions = {
        "Get X Kills":        f"Get {game_values['required_kills']} Kills",
        "Get X Assists":      f"Get {game_values['required_assists']} Assists",
        "Get X Creep Score":  f"Get {game_values['required_cs']} Creep Score",
        "Get X Ward Score":   f"Get {game_values['required_vs']} Ward Score",
    }

    rows = []
    for loc_name, loc_id in active_location_ids.items():
        if not loc_name.startswith(prefix):
            continue
        if loc_id is not None and int(loc_id) in checked_ids:
            continue
        suffix = loc_name[len(prefix):]
        rows.append([x_substitutions.get(suffix, suffix)])

    window["Values Table"].update(values=rows)

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
        is_support = "Support" in champions[champion_id]["tags"]
        enabled = set(game_values.get("enabled_checks") or [])
        sst = game_values.get("support_special_treatment", True)

        def check_enabled(check_name):
            if enabled and check_name not in enabled:
                return False
            if sst:
                if check_name == "Vision Score" and not is_support:
                    return False
                if check_name in ("Kills", "Creep Score") and is_support:
                    return False
            return True

        if check_enabled("Dragon") and assisted_epic_monster(game_data, player_name, "Dragon"):
            objectives_complete.append(1)
        if check_enabled("Herald") and (assisted_epic_monster(game_data, player_name, "Herald") or assisted_epic_monster(game_data, player_name, "Horde")):
            objectives_complete.append(2)
        if check_enabled("Baron") and assisted_epic_monster(game_data, player_name, "Baron"):
            objectives_complete.append(3)
        if check_enabled("Tower") and assisted_tower(game_data, player_name):
            objectives_complete.append(4)
        if check_enabled("Inhibitor") and assisted_inhibitor(game_data, player_name):
            objectives_complete.append(5)
        if check_enabled("Game Win") and won_game(game_data):
            objectives_complete.append(10)
        if check_enabled("Assists") and assists_above(game_data, player_name, game_values["required_assists"]):
            objectives_complete.append(6)
        if check_enabled("Vision Score") and vision_score_above(game_data, player_name, game_values["required_vs"]):
            objectives_complete.append(7)
        if check_enabled("Kills") and kills_above(game_data, player_name, game_values["required_kills"]):
            objectives_complete.append(8)
        if check_enabled("Creep Score") and creep_score_above(game_data, player_name, game_values["required_cs"]):
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
                        ], headings = ["Champion Name", "Remaining"], key = "Champions Unlocked Table",
                        enable_click_events = True)]
                ]),
                sg.Column(
                [
                    [sg.Text("Remaining Checks")],
                    [sg.Table(
                        [
                        ], headings = ["Check"], key = "Values Table",
                        col_widths = [24], auto_size_columns = False)]
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

window = sg.Window(_WINDOW_TITLE, layout)
window.metadata = {"champion_sort": "name", "selected_champion_id": None}
while True:
    game_data = None
    event, values = window.read(timeout=2000)
    if event == sg.WIN_CLOSED:
        break
    if event == 'Check for Match Button':
        in_match = True
    if isinstance(event, tuple) and len(event) == 3 and event[0] == "Champions Unlocked Table" and event[1] == "+CLICKED+":
        cell = event[2]
        # cell may be an int or a (row, col) tuple depending on PySimpleGUI version/events
        row_index = None
        col = None
        if isinstance(cell, (list, tuple)) and len(cell) >= 1:
            row_index = cell[0]
            if len(cell) >= 2:
                col = cell[1]
        else:
            try:
                row_index = int(cell)
            except Exception:
                row_index = None

        if row_index == -1:
            # header clicked -> sort by column if we know the column index
            if col is None:
                continue
            prev = window.metadata.get("champion_sort", "name")
            sort_keys = ["name", "remaining"]
            if col < len(sort_keys):
                new_sort = sort_keys[col]
                if prev == new_sort:
                    window.metadata["champion_sort"] = new_sort + "_desc"
                elif prev == new_sort + "_desc":
                    window.metadata["champion_sort"] = new_sort
                else:
                    window.metadata["champion_sort"] = new_sort
        else:
            # row clicked -> select champion if index valid
            if row_index is None:
                continue
            table_data = window["Champions Unlocked Table"].Values
            if table_data and 0 <= row_index < len(table_data):
                window.metadata["selected_champion_id"] = get_champion_id(table_data[row_index][0])
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