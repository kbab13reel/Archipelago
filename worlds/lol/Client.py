from __future__ import annotations
import os
import sys
import asyncio
import shutil
import requests
import json

import ModuleUpdate
ModuleUpdate.update()

import Utils

check_num = 0

###Set up game communication path###
if "localappdata" in os.environ:
    game_communication_path = os.path.expandvars(r"%localappdata%/LOLAP")
else:
    game_communication_path = os.path.expandvars(r"$HOME/LOLAP")
if not os.path.exists(game_communication_path):
    os.makedirs(game_communication_path)


###Client###
if __name__ == "__main__":
    Utils.init_logging("LOLClient", exception_logger="Client")

from NetUtils import NetworkItem, ClientStatus
from CommonClient import gui_enabled, logger, get_base_parser, ClientCommandProcessor, \
    CommonContext, server_loop


def check_stdin() -> None:
    if Utils.is_windows and sys.stdin:
        print("WARNING: Console input is not routed reliably on Windows, use the GUI instead.")

class LOLClientCommandProcessor(ClientCommandProcessor):
    pass

class LOLContext(CommonContext):
    command_processor: int = LOLClientCommandProcessor
    game = "League of Legends"
    items_handling = 0b111  # full remote

    def __init__(self, server_address, password):
        super(LOLContext, self).__init__(server_address, password)
        self.send_index: int = 0
        self.syncing = False
        self.awaiting_bridge = False
        self.lp_label = None
        self.required_lp: int = 0
        self.win_completes_champion: bool = False
        # self.game_communication_path: files go in this path to pass data between us and the actual game
        if "localappdata" in os.environ:
            self.game_communication_path = os.path.expandvars(r"%localappdata%/LOLAP")
        else:
            self.game_communication_path = os.path.expandvars(r"$HOME/LOLAP")
        if not os.path.exists(self.game_communication_path):
            os.makedirs(self.game_communication_path)
        for root, dirs, files in os.walk(self.game_communication_path):
            for file in files:
                if file.find("obtain") <= -1:
                    os.remove(root+"/"+file)

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(LOLContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    async def connection_closed(self):
        await super(LOLContext, self).connection_closed()
        for root, dirs, files in os.walk(self.game_communication_path):
            for file in files:
                if file.find("obtain") <= -1:
                    os.remove(root + "/" + file)

    @property
    def endpoints(self):
        if self.server:
            return [self.server]
        else:
            return []

    async def shutdown(self):
        await super(LOLContext, self).shutdown()
        for root, dirs, files in os.walk(self.game_communication_path):
            for file in files:
                if file.find("obtain") <= -1:
                    os.remove(root+"/"+file)

    def on_package(self, cmd: str, args: dict):
        if cmd in {"Connected"}:
            if not os.path.exists(self.game_communication_path):
                os.makedirs(self.game_communication_path)
            for ss in self.checked_locations:
                filename = f"send{ss}"
                with open(os.path.join(self.game_communication_path, filename), 'w') as f:
                    f.close()
            #Handle Slot Data
            for slot_data_key in list(args['slot_data'].keys()):
                with open(os.path.join(self.game_communication_path, slot_data_key.replace(" ", "_") + ".cfg"), 'w') as f:
                    f.write(str(args['slot_data'][slot_data_key]))
                    f.close()
            #End Handle Slot Data
            self.required_lp = int(args['slot_data'].get('Required LP', 0))
            self.win_completes_champion = bool(args['slot_data'].get('Win Completes Champion', False))
            # win_completes_champion sibling filter uses ctx.missing_locations (set after Connected)
            # Write a checked locations file for tools (list of ids)
            try:
                with open(os.path.join(self.game_communication_path, "Checked_Locations.cfg"), 'w') as f:
                    f.write(str(list(self.checked_locations)))
                    f.close()
            except Exception:
                pass
            
        if cmd in {"ReceivedItems"}:
            start_index = args["index"]
            if start_index != len(self.items_received):
                for item in args['items']:
                    check_num = 0
                    for filename in os.listdir(self.game_communication_path):
                        if filename.startswith("AP"):
                            if int(filename.split("_")[-1].split(".")[0]) > check_num:
                                check_num = int(filename.split("_")[-1].split(".")[0])
                    item_id = ""
                    location_id = ""
                    player = ""
                    found = False
                    for filename in os.listdir(self.game_communication_path):
                        if filename.startswith(f"AP"):
                            with open(os.path.join(self.game_communication_path, filename), 'r') as f:
                                item_id = str(f.readline()).replace("\n", "")
                                location_id = str(f.readline()).replace("\n", "")
                                player = str(f.readline()).replace("\n", "")
                                if str(item_id) == str(NetworkItem(*item).item) and str(location_id) == str(NetworkItem(*item).location) and str(player) == str(NetworkItem(*item).player) and int(location_id) > 0:
                                    found = True
                    if not found:
                        filename = f"AP_{str(check_num+1)}.item"
                        with open(os.path.join(self.game_communication_path, filename), 'w') as f:
                            f.write(str(NetworkItem(*item).item) + "\n" + str(NetworkItem(*item).location) + "\n" + str(NetworkItem(*item).player))
                            f.close()

        if cmd in {"RoomUpdate"}:
            if "checked_locations" in args:
                for ss in self.checked_locations:
                    filename = f"send{ss}"
                    with open(os.path.join(self.game_communication_path, filename), 'w') as f:
                        f.close()
            # update checked locations file
            try:
                with open(os.path.join(self.game_communication_path, "Checked_Locations.cfg"), 'w') as f:
                    f.write(str(list(self.checked_locations)))
                    f.close()
            except Exception:
                pass

    async def draw_lp_counter(self):
        try:
            from kvui import MDLabel as Label
        except ImportError:
            from kvui import Label
        # Only show LP counter when we've got a slot and a non-zero required LP
        if not getattr(self, 'slot', None) or not self.required_lp:
            return
        if not self.lp_label:
            # make the label smaller so it doesn't take too much space
            self.lp_label = Label(text="", size_hint_x=None, width=84, halign="center")
            self.ui.connect_layout.add_widget(self.lp_label)
        current_lp = sum(1 for item in self.items_received if item.item == 565_000000)
        self.lp_label.text = f"LP: {current_lp}/{self.required_lp}"

    def run_gui(self):
        """Import kivy UI system and start running it as self.ui_task."""
        from kvui import GameManager

        class LOLManager(GameManager):
            logging_pairs = [
                ("Client", "Archipelago")
            ]
            base_title = "Archipelago LoL Client"

        self.ui = LOLManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")


async def game_watcher(ctx: LOLContext):
    from worlds.lol.Locations import lookup_id_to_name
    while not ctx.exit_event.is_set():
        if ctx.syncing == True:
            sync_msg = [{'cmd': 'Sync'}]
            if ctx.locations_checked:
                sync_msg.append({"cmd": "LocationChecks", "locations": list(ctx.locations_checked)})
            await ctx.send_msgs(sync_msg)
            ctx.syncing = False
        sending = []
        victory = False
        for root, dirs, files in os.walk(ctx.game_communication_path):
            for file in files:
                if file.find("send") > -1:
                    st = file.split("send", -1)[1]
                    if st != "nil":
                        sending = sending+[(int(st))]
                if file.find("victory") > -1:
                    victory = True
        # Win Completes Champion: auto-send all sibling locations when nexus is destroyed
        if ctx.win_completes_champion:
            all_active = ctx.missing_locations | ctx.checked_locations
            new_sends = []
            for loc_id in list(sending):
                # "Enemy Nexus Destroyed" locations have offset 10 in the ID scheme
                if loc_id in lookup_id_to_name and "Enemy Nexus Destroyed" in lookup_id_to_name[loc_id]:
                    champ_bucket = (loc_id - 566_000000) // 100
                    for sibling_id, sibling_name in lookup_id_to_name.items():
                        sibling_relative = sibling_id - 566_000000
                        if (sibling_relative > 0
                                and sibling_relative // 100 == champ_bucket
                                and sibling_id not in sending
                                and sibling_id not in new_sends
                                and sibling_id in all_active):
                            sibling_path = os.path.join(ctx.game_communication_path, f"send{sibling_id}")
                            if not os.path.exists(sibling_path):
                                with open(sibling_path, 'w') as f:
                                    pass
                            new_sends.append(sibling_id)
            sending.extend(new_sends)

        ctx.locations_checked = sending
        if ctx.ui:
            await ctx.draw_lp_counter()
        # persist checked locations for external tools
        try:
            with open(os.path.join(ctx.game_communication_path, "Checked_Locations.cfg"), 'w') as f:
                f.write(str(list(ctx.locations_checked)))
                f.close()
        except Exception:
            pass
        message = [{"cmd": 'LocationChecks', "locations": sending}]
        await ctx.send_msgs(message)
        if not ctx.finished_game and victory:
            await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            ctx.finished_game = True
        await asyncio.sleep(0.1)


def launch():
    async def main(args):
        ctx = LOLContext(args.connect, args.password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        progression_watcher = asyncio.create_task(
            game_watcher(ctx), name="LOLProgressionWatcher")

        await ctx.exit_event.wait()
        ctx.server_address = None

        await progression_watcher

        await ctx.shutdown()

    import colorama

    parser = get_base_parser(description="LoL Client, for text interfacing.")

    args, rest = parser.parse_known_args()
    colorama.init()
    asyncio.run(main(args))
    colorama.deinit()
