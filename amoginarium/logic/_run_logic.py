"""
Runs the logic process.

| ``Path``: amoginarium/logic/_run_logic.py
| ``Project``: amoginarium
| ``Created``: 28.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import ctypes
import json
import os
from queue import Empty
from time import perf_counter, perf_counter_ns, sleep
from typing import TYPE_CHECKING

import pygame as pg
from icecream import colorize, ic

from amoginarium import pv
from amoginarium.shared import base_entity_t, BaseCommandType, Coalitions
from amoginarium.shared import DebugVarsEnum, ENTITY_COUNTER, GlobalVars
from amoginarium.shared import INVENTORY_COUNTER, MAX_ENTITIES
from amoginarium.shared import ProcessCommand, ProcessCommandType
from amoginarium.shared.audio import BackgroundPlayer, sound_effects
from amoginarium.shared.audio import SoundEffect, sounds
from amoginarium.shared.debugging import CC, cum_timer, get_fg_color, print_ic_style
from amoginarium.shared.debugging import print_with_prefix, run_with_debug
from amoginarium.shared.utility import PIDController, Vec2

from .entities import Bullets, CollisionLogicEntity, Dead, DETECTION_GLOBAL_BLUE
from .entities import DETECTION_GLOBAL_NEUTRAL, DETECTION_GLOBAL_RED
from .entities import DETECTION_GROUP_MANAGER, DetectionGroup, FrictionXAffected
from .entities import GameCollisions, GrassIsland, GravityAffected, Island
from .entities import LogicGameEntity, Player, Players, SPAWNABLES, Updated
from .graphics_dummies import Controller

if TYPE_CHECKING:
    from multiprocessing import Queue, synchronize
    from multiprocessing.connection import Connection
    from multiprocessing.shared_memory import SharedMemory
    from multiprocessing.sharedctypes import Synchronized


class LogicProcess:
    """
    Logic Process data.
    """

    def __init__(  # noqa: PLR0917
        self,
        shm: SharedMemory,
        c_shm: SharedMemory,
        i_shm: SharedMemory,
        d_shm: SharedMemory,
        command_in_queue: Queue,
        command_out_queue: Queue,
        write_lock: synchronize.Lock,
        global_vars: GlobalVars,
        base_comm: Connection,
        process_comm: Connection,
        start_time: float,
        run_name: str,
    ) -> None:
        self._start = start_time
        self._run_name = run_name
        ic.configureOutput(
            prefix="",
            outputFunction=lambda s, **kwargs: print_with_prefix(
                s, prefix=self.get_ic_prefix(), **kwargs
            ),
        )

        # map loading status
        self._map_loading = False

        pv.set_shared_process_values(
            g_vars=global_vars,
            command_in_queue=command_in_queue,
            command_out_queue=command_out_queue,
            shared_memory=shm,
            controller_memory=c_shm,
            inventory_memory=i_shm,
            debugging_memory=d_shm,
            write_lock=write_lock,
            base_comm=base_comm,
            process_comm=process_comm,
        )

        # initialize pygame
        pg.mixer.init(channels=2, buffer=1024)
        pg.mixer.set_num_channels(128)

        self._write_lock = write_lock
        self._ciq = command_in_queue
        self._coq = command_out_queue
        self._global_vars = global_vars

        local_buffer = bytearray(ctypes.sizeof(base_entity_t) * MAX_ENTITIES)

        self.__entity_buffer = pv.E_BUFF
        self._runtime_buffer = (base_entity_t * MAX_ENTITIES).from_buffer(local_buffer)

        # initialize sound stuff
        self._background_player = BackgroundPlayer()
        self._background_player.volume = 0.6

        # debugging
        self._logic_loop_times: list[tuple[float, float]] = []
        self._n_bullets_times: list[tuple[float, float, float]] = []

        # copy once to make sure starting value is the same
        self._runtime_buffer[:] = self.__entity_buffer

        # preload sounds
        self.preload()
        self._last_spawn = 0

        self._running = True
        self._paused = False

        self._b_start = Vec2().from_cartesian(700, 700)
        self._dummy_dad = LogicGameEntity(self._runtime_buffer, Vec2(), self._b_start)

        # world position pid controller
        self._x_pid = PIDController(4, 0.0001, 0.5)
        self._y_pid = PIDController(4, 0.0001, 0.5)

    # region properties
    @property
    def running(self) -> bool:
        """:return: logic process alive"""
        return self._running

    @property
    def paused(self) -> bool:
        """:return: logic process paused"""
        return self._paused

    # endregion

    @run_with_debug(reraise_errors=True, show_finish=True)
    def preload(self) -> None:
        """
        Preloads sound effects.
        """
        start = perf_counter_ns()
        # load sounds
        sounds.load_sounds("./assets/audio/background")
        sounds.load_sounds("./assets/audio/effects/minigun")
        sounds.load_sounds("./assets/audio/effects/explosions")
        sounds.load_sounds("./assets/audio/effects/explosions/explosion_large")
        sounds.load_sounds("./assets/audio/effects/shots")
        sounds.load_sounds("./assets/audio/effects/shots/cannon")
        sounds.load_sounds("./assets/audio/effects/shots/ak47")
        sounds.load_sounds("./assets/audio/effects/reloads")
        sounds.load_sounds("./assets/audio/effects/ui")
        sounds.load_sounds("./assets/audio/effects/groaning")
        sounds.load_sounds("./assets/audio/effects/death")
        sounds.load_sounds("./assets/audio/effects/distant_pop")
        sounds.load_sounds("./assets/audio/effects/metal_pings")
        sounds.load_sounds("./assets/audio/effects/rocket")
        sounds.load_sounds("./assets/audio/effects/potion_drink")

        self._background_player.assign_scope("background")

        end = perf_counter_ns()
        load_time = round((end - start) / 1e6, 2)
        ic(load_time)

    def get_ic_prefix(self) -> str:
        """Get terminal prefix for icecream."""
        t = round(perf_counter() - self._start, 4)

        t1, t2 = str(t).split(".")

        return (
            f"{get_fg_color(36)}{t1: >4}.{t2: <4}{get_fg_color(247)} | "
            f"{get_fg_color(12)}logic{get_fg_color(247)} |> "
        )

    def load_map(self, map_path: str) -> None:  # noqa: C901, PLR0912
        """Load a map from a JSON file."""
        if not os.path.isfile(map_path):
            # if the file wasn't found, try adding the root program path
            map_path = os.path.dirname(__file__) + "/" + map_path
            ic(map_path)
            if not os.path.isfile(map_path):
                msg = f'Couldn\'t find map "{map_path}"'
                raise FileNotFoundError(msg)

        self._map_loading = True

        # load map data
        data = json.load(open(map_path, "r", encoding="utf-8"))

        pg.display.set_caption(f"amoginarium - {data['name']}")

        Players.spawn_point = Vec2().from_cartesian(*data["spawn_pos"])

        # load islands
        for island in data["platforms"]:
            island_type = GrassIsland
            if "type" in island and island["type"] in Island.ISLANDS:
                island_type = Island.ISLANDS[island["type"]]

            if "args" in island:
                island_type(self._runtime_buffer, **island["args"])

            elif "size" in island:
                island_type(
                    self._runtime_buffer,
                    Vec2().from_cartesian(*island["pos"]),
                    size=Vec2().from_cartesian(*island["size"]),
                )

            elif "form" in island:
                island_type(
                    self._runtime_buffer,
                    Vec2().from_cartesian(*island["pos"]),
                    form=island["form"],
                )

            else:
                print_ic_style(f"{CC.fg.RED}invalid island: {CC.fg.YELLOW}{island}")
                continue

        # load entities
        detection_groups: dict[int, DetectionGroup] = {
            -1: DETECTION_GLOBAL_BLUE,
            -2: DETECTION_GLOBAL_RED,
            -3: DETECTION_GLOBAL_NEUTRAL,
        }
        for entity in data["entities"]:
            if entity["type"] not in SPAWNABLES:
                print_ic_style(
                    f"{CC.fg.RED}unknown entity: {CC.fg.YELLOW}{entity['type']}"
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
                    runtime_buffer=self._runtime_buffer,
                    coalition=Coalitions.red,
                    position=Vec2().from_cartesian(*entity["pos"]),
                    **args,
                )

            except KeyboardInterrupt:  # (KeyError, TypeError):
                print_ic_style(
                    f"{CC.fg.RED}invalid arguments for "
                    f"{CC.fg.YELLOW}{SPAWNABLES[entity['type']].__name__}{CC.fg.RED}: "
                    f'"{CC.fg.YELLOW}{args!r}{CC.fg.RED}"'
                )

        # set initial camera position
        view_pos = data["end_pos"] if "end_pos" in data else data["spawn_pos"]

        self._x_pid.set_value(view_pos[0])
        self._y_pid.set_value(view_pos[1])

        self._map_loading = False

    @cum_timer.time_this
    def update_entities(self, delta: float) -> bool:  # noqa: C901, PLR0912, PLR0915
        """
        Update all entities.

        :returns: True if update, false if paused
        """
        start = perf_counter()

        self._logic_loop_times.append((start - self._start, delta))
        self._n_bullets_times.append(
            (start - self._start, len(Bullets) + len(Updated), delta)
        )

        # update commands
        while True:
            try:
                item: ProcessCommand = self._ciq.get_nowait()

            except Empty:
                break

            if item.type == ProcessCommandType.quit:
                self._running = False
                self.end()
                return False

            if item.type == ProcessCommandType.reset:
                self.reset_game()
                self._paused = True
                ic("logic reset complete")
                pv.COQ.put(
                    ProcessCommand(type=BaseCommandType.confirm_reset, kwargs={})
                )
                return False

            if item.type == ProcessCommandType.pause:
                self._paused = True

            elif item.type == ProcessCommandType.unpause:
                self._paused = False

            elif item.type == ProcessCommandType.load_map:
                self.load_map(**item.kwargs)

            elif item.type == ProcessCommandType.play_sound:
                kwargs = item.kwargs
                s = SoundEffect(kwargs["sound_name"])
                kwargs.pop("sound_name")
                s.play(**kwargs)

            elif item.type == ProcessCommandType.spawn_player:
                if Players.spawn_point:
                    ic(item)
                    Player(
                        self._runtime_buffer,
                        Controller(item.kwargs.pop("controller_id")),
                        **item.kwargs,
                    )

                else:
                    self._ciq.put(item)

            elif item.type == ProcessCommandType.set_zoom:
                # get current center
                screen_size = pv.global_vars.get_screen_size()
                ppm = pv.global_vars.get_pixel_per_meter()

                screen_pixels = (screen_size / ppm) / 2
                current_center: Vec2 = (
                    pv.global_vars.get_world_position() + screen_pixels
                )

                # zoom
                ppm *= item.kwargs["zoom"]
                pv.global_vars.set_pixel_per_meter(ppm)

                # update position
                screen_pixels = (screen_size / ppm) / 2
                w_pos = current_center - screen_pixels
                pv.global_vars.set_world_position(w_pos)
                self._x_pid.set_value(w_pos.x)
                self._y_pid.set_value(w_pos.y)

            else:
                ic(item)

        if self._paused:
            return False

        # update sounds
        try:  # throws error on game end
            self._background_player.update()

        except pg.error:
            return False

        # wait when map is loading
        if self._map_loading:
            return False

        sound_effects.update()

        # test stuff
        self._last_spawn -= delta
        if self._last_spawn < 0:
            self._last_spawn = 3

        # reset detection Group
        DETECTION_GROUP_MANAGER.reset()

        # update entities
        GravityAffected.calculate_gravity(delta)
        FrictionXAffected.calculate_friction(delta)

        # give turrets a little extra help with bullets by getting their position from
        # current loop instead of last loop
        Bullets.update(delta)
        DETECTION_GROUP_MANAGER.update_detection(delta)
        Dead.empty()  # empty dead here because it is primarily used for detection
        Updated.update(delta)

        players = Players.entities()
        if len(players) > 0:
            curr_view = players[0].get_current_view()

            screen_pixels = (
                pv.global_vars.get_screen_size() / pv.global_vars.get_pixel_per_meter()
            ) / 2

            if curr_view.centered:
                Updated.world_position.xy = (
                    curr_view.pos.x - screen_pixels.x,
                    curr_view.pos.y - screen_pixels.y,
                )

            else:
                curr_view.pos -= screen_pixels

                # set position in case of graphics position update
                x_pos = self._x_pid.update_value(curr_view.pos.x, delta)
                y_pos = self._y_pid.update_value(curr_view.pos.y, delta)

                Updated.world_position.xy = x_pos, y_pos

            pv.audio_observer_pos.xy = Updated.world_position.xy
            self._global_vars.set_world_position(Updated.world_position)

        return True

    @cum_timer.time_this
    def update_memory(self) -> None:
        """
        Copy runtime buffer to memory buffer.
        """
        self._write_lock.acquire()
        ctypes.memmove(
            ctypes.addressof(self.__entity_buffer),
            ctypes.addressof(self._runtime_buffer),
            ctypes.sizeof(self.__entity_buffer),
        )
        self._write_lock.release()

    def reset_game(self) -> None:
        """Reset game state."""
        # kill all entities
        for e in Updated.entities() + Bullets.entities():
            e.kill()

        # reset shared values
        self._write_lock.acquire()
        pv.reset()
        self._write_lock.release()

        # reset groups
        Updated.world_position = pv.global_vars.get_world_position()

        # reset entity counters
        INVENTORY_COUNTER.reset()
        ENTITY_COUNTER.reset()

    def end(self) -> None:
        """Close the logic thread."""
        # print entity stats
        entities = Updated.entities() + Bullets.entities()
        entities = [e.__class__.__name__ for e in entities]
        unique = set(entities)
        print_ic_style(CC.fg.YELLOW + "entities: " + CC.ctrl.ENDC)
        for entity in unique:
            print_ic_style(colorize(f"\t{entity}: {entities.count(entity)}"))

        # print debug stats
        times = cum_timer.get_times()
        for func, values in sorted(times.items(), key=lambda e: e[1][0]):
            print_ic_style(
                f"{func}, called {values[1]} times {round(values[2], 3)}μs each,"
                f" totaling {round(values[0] / 1000, 2)}ms"
            )

        # stop background music
        self._background_player.stop()

        # write debug data
        os.makedirs("debug", exist_ok=True)
        with open(
            f"debug/logic_debug_{self._run_name}_{int(self._start)}.json",
            "w",
            encoding="utf-8",
        ) as out:
            json.dump(
                {"logic": self._logic_loop_times, "bullets": self._n_bullets_times}, out
            )
        with open("logic_debug.json", "w", encoding="utf-8") as out:
            json.dump(
                {"logic": self._logic_loop_times, "bullets": self._n_bullets_times}, out
            )


def update_debug_vars(values: int) -> None:
    """
    Update debug flags based on bitmask values
    :param values: new bitmask of debug flags.
    """
    # Hitbox debug
    draw_hitboxes = bool(values & (1 << DebugVarsEnum.DRAW_HITBOXES.value))
    CollisionLogicEntity.debug_draw_hitboxes(draw_hitboxes)
    Island.debug_draw_hitboxes(draw_hitboxes)


def run_continuous(  # noqa: PLR0917
    shm: SharedMemory,
    c_shm: SharedMemory,
    i_shm: SharedMemory,
    d_shm: SharedMemory,
    command_in_queue: Queue,
    command_out_queue: Queue,
    write_lock: synchronize.Lock,
    global_vars_values: dict[str, Synchronized],
    base_comm: Connection,
    process_comm: Connection,
    start_time: float,
    run_name: str,
) -> None:
    """
    Run the logic process continuously.
    """
    global_vars = GlobalVars(global_vars_values, False)  # noqa: FBT003
    global_vars.update()

    lp = LogicProcess(
        shm,
        c_shm,
        i_shm,
        d_shm,
        command_in_queue,
        command_out_queue,
        write_lock,
        global_vars,
        base_comm,
        process_comm,
        start_time,
        run_name,
    )

    ic("logic process start")

    # Debugging callbacks
    pv.global_vars.add_callback(value="_debug_vars", callback=update_debug_vars)

    last_run = perf_counter()
    last_update_success = False
    while lp.running:
        # calculate time since last loop
        now = perf_counter()
        if last_update_success:
            delta = (now - last_run) * pv.global_vars.get_time_mult()

        else:
            delta = 0

        # update entities
        last_update_success = lp.update_entities(delta)
        GameCollisions.collision_manager.calculate_all_collisions()

        # don't update if paused
        if lp.paused:
            sleep(0.05)
            continue

        # copy buffer
        lp.update_memory()

        # update from buffer
        pv.global_vars.update()

        last_run = now

    ic("logic quit")
