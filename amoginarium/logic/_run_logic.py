"""
_run_logic.py
28.03.2026

runs the logic process

Author:
Nilusink
"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.sharedctypes import Synchronized
from multiprocessing.connection import Connection
from time import perf_counter, sleep, perf_counter_ns
from multiprocessing import Queue, synchronize
from icecream import ic, colorize
from queue import Empty
import pygame as pg
import ctypes
import json
import os

from amoginarium.shared import base_entity_t, MAX_ENTITIES, GlobalVars, ProcessCommand
from amoginarium.shared import ProcessCommandType, Coalitions, ENTITY_COUNTER
from amoginarium.shared import BaseCommandType, INVENTORY_COUNTER
from amoginarium.shared.debugging import print_ic_style, CC, run_with_debug, cum_timer
from amoginarium.shared.debugging import print_with_prefix, get_fg_color
from amoginarium.shared.utility import Vec2, calculate_launch_angle
from amoginarium import pv

from .entities import DETECTION_GROUP_MANAGER, DetectionGroup, DETECTION_GLOBAL_NEUTRAL
from .entities import DETECTION_GLOBAL_RED, DETECTION_GLOBAL_BLUE, collision_manager
from .entities import Updated, CollisionDestroyed, WallBouncer, Bullets, Players
from .entities import LogicGameEntity, ISLANDS, GrassIsland, SPAWNABLES, Player
from .entities import GravityAffected, FrictionXAffected, MortarShell, Mortar
from .audio import sound_effects, BackgroundPlayer, sounds, SoundEffect, LargeExplosion
from .graphics_dummies import Controller


class LogicProcess:
    """
    Logic Process data
    """

    def __init__(
            self,
            shm: SharedMemory,
            c_shm: SharedMemory,
            i_shm: SharedMemory,
            command_in_queue: Queue,
            command_out_queue: Queue,
            write_lock: synchronize.Lock,
            global_vars: GlobalVars,
            base_comm: Connection,
            process_comm: Connection,
            start_time: float,
    ) -> None:
        self._start = start_time
        ic.configureOutput(
            prefix="",
            outputFunction=lambda s, **kwargs: print_with_prefix(
                s,
                prefix=self.get_ic_prefix(),
                **kwargs
            )
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
        self._background_player.volume = .6

        # debugging
        self._logic_loop_times: list[tuple[float, float]] = []
        self._n_bullets_times: list[tuple[float, float, float]] = []

        # copy once to make sure starting value is the same
        self._runtime_buffer[:] = self.__entity_buffer

        # preload sounds
        self.preload()
        self._last_spawn = perf_counter()

        self._running = True
        self._paused = False

        # self._v = 3000
        # self._b_vel, *_ = calculate_launch_angle(
        #     Vec2().from_cartesian(6000, -65),
        #     Vec2(),
        #     Vec2(),
        #     self._v,
        #     aim_type="high",
        #     g=GravityAffected.gravity * 2
        # )
        # self._b_vel.y *= -1
        # ic(self._b_vel)
        # self._b_start = Vec2().from_cartesian(700, 700)
        # self._dummy_dad = LogicGameEntity(self._runtime_buffer, Vec2(), self._b_start)
        # self._w = Mortar(
        #     self._dummy_dad,
        #     self._runtime_buffer,
        #     bullet_speed=self._v
        # )
        # self._w.set_parent(self._dummy_dad)
        # self._w.show()
        # self._w._mag_size = 4
        # self._w.reload(True)
        # self._w.facing = self._b_vel

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
        preloads sound effects
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
        """get terminal prefix for icecream"""
        t = round(perf_counter() - self._start, 4)

        t1, t2 = str(t).split(".")

        return (
            f"{get_fg_color(36)}{t1: >4}.{t2: <4}{get_fg_color(247)} | "
            f"{get_fg_color(12)}logic{get_fg_color(247)} |> "
        )

    def load_map(self, map_path: str) -> None:
        """load a map from a json file"""
        if not os.path.isfile(map_path):
            # if the file wasn't found, try adding the root program path
            map_path = os.path.dirname(__file__) + "/" + map_path
            ic(map_path)
            if not os.path.isfile(map_path):
                raise FileNotFoundError(f"Couldn't find map \"{map_path}\"")

        self._map_loading = True
        self._last_map_path = map_path

        # load map data
        data = json.load(open(map_path, "r"))
        self._last_loaded = map_path

        pg.display.set_caption(f"amoginarium - {data["name"]}")

        Players.spawn_point = Vec2().from_cartesian(*data["spawn_pos"])

        # load islands
        for island in data["platforms"]:
            island_type = GrassIsland
            if "type" in island:
                if island["type"] in ISLANDS:
                    island_type = ISLANDS[island["type"]]

            if "args" in island:
                i = island_type(self._runtime_buffer, **island["args"])

            elif "size" in island:
                i = island_type(
                    self._runtime_buffer,
                    Vec2().from_cartesian(*island["pos"]),
                    size=Vec2().from_cartesian(*island["size"]),
                )

            elif "form" in island:
                i = island_type(
                    self._runtime_buffer,
                    Vec2().from_cartesian(*island["pos"]),
                    form=island["form"],
                )

            else:
                print_ic_style(
                    f"{CC.fg.RED}invalid island: "
                    f"{CC.fg.YELLOW}{island}"
                )
                continue

            # if "move" in island:
            #     create_moving_island(
            #         i,
            #         **island["move"]
            #     )

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
                    runtime_buffer=self._runtime_buffer,
                    coalition=Coalitions.red,
                    position=Vec2().from_cartesian(*entity["pos"]),
                    **args
                )

            except KeyError:
                print_ic_style(
                    f"{CC.fg.RED}invalid arguments for "
                    f"{CC.fg.YELLOW}{entity["type"]}{CC.fg.RED}: "
                    f"\"{CC.fg.YELLOW}{args.__repr__()}{CC.fg.RED}\""
                )

        self._map_loading = False

    @cum_timer.time_this
    def update_entities(self, delta: float) -> bool:
        """
        update all entities

        :returns: True if update, false if paused
        """
        start = perf_counter()

        self._logic_loop_times.append(
            (start - self._start, delta)
        )
        self._n_bullets_times.append(
            (start - self._start, Bullets.__len__() + Updated.__len__(), delta)
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

            elif item.type == ProcessCommandType.reset:
                self.reset_game()
                self._paused = True
                ic("logic reset complete")
                pv.COQ.put(
                    ProcessCommand(type=BaseCommandType.confirm_reset, kwargs={})
                )
                return False

            elif item.type == ProcessCommandType.pause:
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
                        **item.kwargs
                    )

                else:
                    self._ciq.put(item)

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

        # # test stuff
        # self._dummy_dad.update(delta)
        # self._w.update(delta)
        # if start - self._last_spawn > 1:
        #     exp = LargeExplosion()
        #     exp.volume = 0.35
        #     exp.play(pos=Vec2().from_cartesian(600, 700))
        #     self._last_spawn = start

        #     self._w.shoot(self._b_vel, 10)
        #     self._w._stop_recoil()

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
        # _, max_player_pos = Players.get_position_extremes()
        players = Players.sprites()
        if len(players) > 0:
            max_player_pos = players[0].position
            pv.audio_observer_pos.xy = max_player_pos.xy
            world_position = pv.global_vars.get_world_position()

            screen_pixels = (
                pv.global_vars.get_screen_size() / pv.global_vars.get_pixel_per_meter()
            ) / 2

            if max_player_pos.x > world_position.x + screen_pixels.x:
                x = max_player_pos.x - screen_pixels.x
                Updated.world_position.x = x

            elif max_player_pos.x < world_position.x + screen_pixels.x * .6:
                x = max_player_pos.x - screen_pixels.x * .6
                Updated.world_position.x = x

            if max_player_pos.y > world_position.y + screen_pixels.y * 1.4:
                y = max_player_pos.y - screen_pixels.y * 1.4
                Updated.world_position.y = y

            elif max_player_pos.y < world_position.y + screen_pixels.y * .6:
                y = max_player_pos.y - screen_pixels.y * .6
                Updated.world_position.y = y

            self._global_vars.set_world_position(Updated.world_position)

        return True

    @cum_timer.time_this
    def update_memory(self) -> None:
        """
        copy runtime buffer to memory buffer
        """
        self._write_lock.acquire()
        ctypes.memmove(
            ctypes.addressof(self.__entity_buffer),
            ctypes.addressof(self._runtime_buffer),
            ctypes.sizeof(self.__entity_buffer),
        )
        self._write_lock.release()

    def reset_game(self) -> None:
        """reset game state"""
        # kill all entities
        for e in Updated.sprites() + Bullets.sprites():
            e.kill()

        collision_manager.clear_all_entities()

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
        """close the logic thread"""
        # print entity stats
        entities = Updated.sprites() + Bullets.sprites()
        entities = [e.__class__.__name__ for e in entities]
        unique = set(entities)
        print_ic_style(CC.fg.YELLOW + "entities: " + CC.ctrl.ENDC)
        for entity in unique:
            print_ic_style(colorize(f"\t{entity}: {entities.count(entity)}"))

        # print debug stats
        times = cum_timer.get_times()
        for func, values in sorted(times.items(), key=lambda e: e[1][0]):
            print_ic_style(
                f"{func}, called {values[1]} times {round(values[2], 3)}µs each,"
                f" totaling {round(values[0] / 1000, 2)}ms"
            )

        # stop background music
        self._background_player.stop()

        # write debug data
        with open("logic_debug.json", "w") as out:
            json.dump({
                "logic": self._logic_loop_times,
                "bullets": self._n_bullets_times
            }, out)


def run_continuous(
        shm: SharedMemory,
        c_shm: SharedMemory,
        i_shm: SharedMemory,
        command_in_queue: Queue,
        command_out_queue: Queue,
        write_lock: synchronize.Lock,
        global_vars_values: dict[str, Synchronized],
        base_comm: Connection,
        process_comm: Connection,
        start_time: float,
        time_multiplier: float
) -> None:
    """
    run the logic process continuously
    """
    global_vars = GlobalVars(global_vars_values, False)
    global_vars.update()

    lp = LogicProcess(
        shm,
        c_shm,
        i_shm,
        command_in_queue,
        command_out_queue,
        write_lock,
        global_vars,
        base_comm,
        process_comm,
        start_time,
    )

    ic("logic process start")

    last_run = perf_counter()
    last_update_success = False
    while lp.running:
        # calculate time since last loop
        now = perf_counter()
        if last_update_success:
            delta = (now - last_run) * pv.global_vars.get_time_mult()

        else:
            delta = 0

        collision_manager.calculate_all_collisions()
        # update entities
        last_update_success = lp.update_entities(delta)

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
