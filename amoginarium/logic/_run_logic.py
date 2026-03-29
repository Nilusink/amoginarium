"""
_run_logic.py
28.03.2026

runs the logic process

Author:
Nilusink
"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.connection import Connection
from time import perf_counter, sleep, perf_counter_ns
from multiprocessing import Queue, Lock, Value
from icecream import ic
from queue import Empty
import typing as tp
import pygame as pg
import ctypes
import json
import os

from ..shared import base_entity_t, MAX_ENTITIES, GlobalVars, ProcessCommand
from ..shared import CommandType, Coalitions
from ..shared.controllers import Controllers, Controller, GameController
from ..shared.debugging import print_ic_style, CC, run_with_debug
from ..shared.debugging import print_with_prefix, get_fg_color
from ..shared.utility import Vec2
from .. import pv
from .radar import DETECTION_GROUP_MANAGER, DetectionGroup, \
    DETECTION_GLOBAL_RED, DETECTION_GLOBAL_BLUE, DETECTION_GLOBAL_NEUTRAL
from .audio import sound_effects, BackgroundPlayer, sounds, SoundEffect
from .entities import *


class LogicProcess:
    def __init__(
            self,
            shm: SharedMemory,
            command_in_queue: Queue,
            command_out_queue: Queue,
            write_lock: Lock,
            global_vars: GlobalVars,
            base_comm: Connection,
            process_comm: Connection,
            start_time: float
    ):
        self._start = start_time
        ic.configureOutput(
            prefix="",
            outputFunction=lambda s, **kwargs: print_with_prefix(
                s,
                prefix=self.get_ic_prefix(),
                **kwargs
            )
        )

        pv.set_shared_process_values(
            global_vars,
            command_in_queue,
            command_out_queue,
            write_lock,
            shm,
            base_comm,
            process_comm
        )

        # initialize pygame
        pg.mixer.init()

        self._write_lock = write_lock
        self._ciq = command_in_queue
        self._coq = command_out_queue
        self._global_vars = global_vars

        local_buffer = bytearray(ctypes.sizeof(base_entity_t) * MAX_ENTITIES)

        self.__entity_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(shm.buf)
        self._runtime_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(local_buffer)

        # controller setup
        self._new_controllers: list[Controller] = []

        self._controllers_cid = Controllers.on_new_controller(
            self._add_controller
        )

        # initialize sound stuff
        self._background_player = BackgroundPlayer()
        self._background_player.volume = .6

        # copy once to make sure starting value is the same
        self._runtime_buffer[:] = self.__entity_buffer

        # preload sounds
        self.preload()

        self._running = True
        self._paused = False

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    @run_with_debug(reraise_errors=True, show_finish=True)
    def preload(self) -> None:
        start = perf_counter_ns()
        # load sounds
        sounds.load_sounds("assets/audio/background")
        sounds.load_sounds("assets/audio/effects/ak47")
        sounds.load_sounds("assets/audio/effects/minigun")
        sounds.load_sounds("assets/audio/effects/explosions")
        sounds.load_sounds("assets/audio/effects/shots")
        sounds.load_sounds("assets/audio/effects/reloads")
        sounds.load_sounds("assets/audio/effects/ui")
        sounds.load_sounds("assets/audio/effects/groaning")
        sounds.load_sounds("assets/audio/effects/death")

        end = perf_counter_ns()
        load_time = round((end - start) / 1e6, 2)
        ic(load_time)

    def get_ic_prefix(self) -> str:
        t = round(perf_counter() - self._start, 4)

        t1, t2 = str(t).split(".")

        return (
            f"{get_fg_color(36)}{t1: >4}.{t2: <4}{get_fg_color(247)} | "
            f"{get_fg_color(12)}logic{get_fg_color(247)} |> "
        )

    def _add_controller(self, controller: Controller) -> None:
        """
        appends a new controller to the queue
        """
        self._new_controllers.append(controller)

    def update_entities(self, delta: float) -> None:
        """
        update all entities
        """
        start = perf_counter()

        # update commands
        while True:
            try:
                item: ProcessCommand = self._ciq.get_nowait()

            except Empty:
                break

            if item.type == CommandType.quit:
                self._running = False
                return

            elif item.type == CommandType.reset:
                self.reset_game()
                return

            elif item.type == CommandType.pause:
                self._paused = True

            elif item.type == CommandType.unpause:
                self._paused = False

            elif item.type == CommandType.load_map:
                self.load_map(**item.kwargs)

            elif item.type == CommandType.play_sound:
                kwargs = item.kwargs
                s = SoundEffect(kwargs["sound_name"])
                kwargs.pop("sound_name")
                s.play(**kwargs)

            else:
                ic(item)

        if self._paused:
            return

        # check for new controllers
        # if len(self._new_controllers) > 0:
        #     self._new_controllers_lock.aquire()
        #     tmp = self._new_controllers.copy()
        #     self._new_controllers.clear()
        #     self._new_controllers_lock.release()
        #
        #     for new_controller in tmp:
        #         # spawn new player
        #         Player(coalition=Coalitions.blue, controller=new_controller)
        #         ic(new_controller, Player)

        # update sounds
        try:  # throws error on game end
            self._background_player.update()

        except pg.error:
            return

        sound_effects.update()

        # reset and update detection Groups
        DETECTION_GROUP_MANAGER.reset()

        # update entities
        GravityAffected.calculate_gravity(delta)
        FrictionXAffected.calculate_friction(delta)
        WallBouncer.update()

        Bullets.update(delta)
        DETECTION_GROUP_MANAGER.update_detection()
        Updated.update(delta)

        CollisionDestroyed.update()

        # update world position
        _, max_player_pos = Players.get_position_extremes()

        # background_pos_left = self._background.position + 60
        screen_size = self._global_vars.get_screen_size()
        Updated.world_position.y = -(
                (screen_size.y / self._global_vars.get_pixel_per_meter())
                - screen_size.y
        )
        self._global_vars.set_world_position(Updated.world_position)

        # TODO: world shifting

    def load_map(self, map_path: tp.LiteralString) -> None:
        """
        load a map from a json file
        """
        if not os.path.isfile(map_path):
            # if the file wasn't found, try adding the root program path
            map_path = os.path.dirname(__file__) + "/" + map_path
            ic(map_path)
            if not os.path.isfile(map_path):
                raise FileNotFoundError(f"Couldn't find map \"{map_path}\"")

        # load map data
        data = json.load(open(map_path, "r"))
        self._last_loaded = map_path

        pg.display.set_caption(f"amoginarium - {data["name"]}")

        # Players.spawn_point = Vec2().from_cartesian(*data["spawn_pos"])

        # load islands
        # for island in data["platforms"]:
        #     self._update_loading_screen(26, "spawning islands")
        #     island_type = GrassIsland
        #     if "type" in island:
        #         if island["type"] in ISLANDS:
        #             island_type = ISLANDS[island["type"]]
        #
        #     if "args" in island:
        #         i = island_type(**island["args"])
        #
        #     elif "size" in island:
        #         i = island_type(
        #             Vec2().from_cartesian(*island["pos"]),
        #             size=Vec2().from_cartesian(*island["size"]),
        #         )
        #
        #     elif "form" in island:
        #         i = island_type(
        #             Vec2().from_cartesian(*island["pos"]),
        #             form=island["form"],
        #         )
        #
        #     else:
        #         print_ic_style(
        #             f"{CC.fg.RED}invalid island: "
        #             f"{CC.fg.YELLOW}{island}"
        #         )
        #         continue
        #
        #     if "move" in island:
        #         create_moving_island(
        #             i,
        #             **island["move"]
        #         )

        # load entities
        detection_groups: dict[int, DetectionGroup] = {
            -1: DETECTION_GLOBAL_BLUE,
            -2: DETECTION_GLOBAL_RED,
            -3: DETECTION_GLOBAL_NEUTRAL,
        }
        for entity in data["entities"]:
            if entity["type"] not in SPAWNABLES:
                print_ic_style(
                    f"{CC.fg.RED}unknown entity: "
                    f"{CC.fg.YELLOW}{entity["type"]}"
                )
                continue

            # check if arguments were given
            args = {}
            if "args" in entity:
                args = entity["args"]

            if "group" in entity:
                group = entity["group"]
                if group not in detection_groups:
                    detection_groups[group] = DetectionGroup(str(group))

                args["detection_group"] = detection_groups[group]

            try:
                SPAWNABLES[entity["type"]](
                    coalition=Coalitions.red,
                    position=Vec2().from_cartesian(*entity["pos"]),
                    **args
                )

            except TypeError:
                print_ic_style(
                    f"{CC.fg.RED}invalid arguments for "
                    f"{CC.fg.YELLOW}{entity["type"]}{CC.fg.RED}: "
                    f"\"{CC.fg.YELLOW}{args}{CC.fg.RED}\""
                )

    def update_memory(self) -> None:
        """
        copy runtime buffer to memory buffer
        """
        self._write_lock.acquire()
        self.__entity_buffer[:] = self._runtime_buffer
        self._write_lock.release()

    def reset_game(self) -> None:
        Updated.kill()

        # reset entity buffer
        self._write_lock.acquire()
        self.__entity_buffer[:] = 0
        self._runtime_buffer[:] = self.__entity_buffer
        self._write_lock.release()

        # reset global vars
        self._global_vars.reset()

        for player in Players.sprites():
            player.respawn()


def run_continuous(
        shm: SharedMemory,
        command_in_queue: Queue,
        command_out_queue: Queue,
        write_lock: Lock,
        global_vars_values: dict[str, Value],
        base_comm: Connection,
        process_comm: Connection,
        start_time: float
) -> None:
    """
    run the logic process continuously
    """
    global_vars = GlobalVars(global_vars_values)
    global_vars.update()

    lp = LogicProcess(
        shm,
        command_in_queue,
        command_out_queue,
        write_lock,
        global_vars,
        base_comm,
        process_comm,
        start_time
    )

    ic("logic process start")

    last_run = perf_counter()
    while lp.running:
        # calculate time since last loop
        now = perf_counter()
        delta = last_run - now

        # update entities
        lp.update_entities(delta)

        # don't update if paused
        if lp.paused:
            sleep(.05)
            continue

        # copy buffer
        lp.update_memory()

        # update from buffer
        pv.global_vars.update()

        last_run = now

    ic("logic quit")
