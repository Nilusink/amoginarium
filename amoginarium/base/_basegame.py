"""
Defines the core game.

Path: amoginarium/base/_basegame.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import json
import subprocess
import typing as tp
from dataclasses import dataclass
from multiprocessing import Process
from os import makedirs
from queue import Empty
from time import perf_counter, perf_counter_ns, strftime, time
from types import EllipsisType

import pygame as pg  # Will be removed after controller/keybind refactoring
from icecream import colorizedStderrPrint, ic

from amoginarium import pv
from amoginarium.graphics.controllers import Controllers, KeyboardController
from amoginarium.graphics.entities import Drawn_0, Drawn_1, Drawn_2
from amoginarium.graphics.entities import SyncedEntities, UIEntities
from amoginarium.graphics.logic_dummies import GRAPHICS_SPAWNABLES, ISLANDS, SE_MANAGER
from amoginarium.graphics.render_bindings import renderer
from amoginarium.graphics.textures import textures
from amoginarium.graphics.ui import UICursor
from amoginarium.logic import run_continuous
from amoginarium.shared import BaseCommandType, ProcessCommand, ProcessCommandType
from amoginarium.shared.debugging import CC, cum_timer, get_fg_color, print_ic_style
from amoginarium.shared.debugging import print_with_prefix, run_with_debug
from amoginarium.shared.settings import Settings

from ._pausemenu import PauseMenu
from ._scrolling_background import ParallaxBackground
from ._settings_menu import SettingsMenu
from ._startmenu import StartMenu

if tp.TYPE_CHECKING:
    from amoginarium.graphics.controllers import Controller


class BoundFunction[**A, R]:
    """a function with pre-determined arguments."""

    func: tp.Callable[A, R]
    args: A.args
    kwargs: A.kwargs

    def __init__(
        self, func: tp.Callable[A, R], *args: A.args, **kwargs: A.kwargs
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> R:
        return self.func(*self.args, **self.kwargs)


def current_time() -> str:
    """
    Helper function for IC debugging.
    """
    ms = str(round(perf_counter(), 4)).split(".")[1]
    return f"{strftime('%H:%M:%S')}.{ms: <4} |> "


class BaseGame:
    """base game class."""

    running: bool = False
    _last_logic: float
    _bg_color: tuple[float, float, float]
    _instance: tp.Self = ...

    def __new__(cls, *args, **kwargs) -> tp.Self:
        # only one instance can exist
        if cls._instance is not ...:
            return cls._instance

        new = super().__new__(cls)
        cls._instance = new
        return new

    def __init__(
        self,
        debug: bool = False,
        show_targets: bool = False,
        time_multiplier: float = 1,
    ) -> None:
        self._game_start = perf_counter()
        ic.configureOutput(
            prefix="",
            outputFunction=lambda s, **kwargs: print_with_prefix(
                s, prefix=self.time_since_start(), **kwargs
            ),
        )

        try:
            self._git_branch: str = (
                subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
                .decode("ascii")
                .strip()
            )
        except (Exception,):
            self._git_branch = "unknown"

        # multiprocessing setup
        pv.create_shared_process_values()

        self._logic_process = Process(
            target=run_continuous,
            kwargs={
                "command_in_queue": pv.COQ,
                "command_out_queue": pv.CIQ,
                "write_lock": pv.WRITE_LOCK,
                "global_vars_values": pv.global_vars.get_values(),
                "shm": pv.SHM,
                "c_shm": pv.C_SHM,
                "i_shm": pv.I_SHM,
                "base_comm": pv.BASE_COMM,
                "process_comm": pv.PROCESS_COMM,
                "start_time": self._game_start,
                "time_multiplier": time_multiplier,
                "run_name": self._git_branch,
            },
        )
        self._logic_process.start()

        # pause logic process until game start
        pv.COQ.put(ProcessCommand(type=ProcessCommandType.pause))

        self.global_vars = pv.global_vars
        self.global_vars.show_targets = show_targets
        self.time_multiplier = time_multiplier
        self._last_loaded: tp.LiteralString | EllipsisType = ...
        self._shifting = False

        self.global_vars.scaling = Settings.scaling

        # configure icecream
        if not debug:
            ic.disable()

        # debugging
        self._pygame_loop_times: list[tuple[float, float]] = []
        self._total_loop_times: list[tuple[float, float]] = []

        self._pygame_fps: int = 0
        self._logic_fps: int = 0
        self._comms_ping: int = 0

        # initialize pygame (logic) and renderer
        renderer.init("amoginarium")
        renderer.display_windowed_fullscreen()

        self._loading_screen_steps = 28
        self._loading_screen_info = "Window init"

        # initialize background
        self._background: ParallaxBackground | EllipsisType = ...
        self._bg_color = (0, 0, 0)
        self._ended = False

        self._update_loading_screen(1)

        # controller setup
        self._new_controllers: list[Controller] = []

        # self._controllers_cid = Controllers.on_new_controller(
        #     self._add_controller
        # )

        # create keyboard controller
        KeyboardController.get()

        # add decorator with callback to self.end
        for func in ("_run_pygame",):
            setattr(
                self,
                func,
                run_with_debug(on_fail=lambda *_: self.end(), reraise_errors=False)(
                    getattr(self, func)
                ),
            )

        self._backgrounds = [
            ParallaxBackground(
                "bg1",
                parallax_multiplier=1.6,
            ),
            ParallaxBackground(
                "bg2",
                parallax_multiplier=1.6,
            ),
            ParallaxBackground(
                "bg3",
                parallax_multiplier=1.6,
            ),
            ParallaxBackground(
                "bg4",
                parallax_multiplier=1.6,
            ),
        ]

        self._update_loading_screen(2, "loading sounds")

        # load textures and sounds
        self.preload()

    def _update_loading_screen(self, step: int, info: str | EllipsisType = ...) -> None:
        if info is not ...:
            self._loading_screen_info = info

        # 2. Clear the entire window buffer with that black color
        # (Note: glClear ignores glViewport, so it will clean the whole window)

        # EventHandler.check_events()
        renderer.clear_display()

        # draw info text
        renderer.draw_dynamic_text(
            (960, 850),
            self._loading_screen_info,
            color=(1, 1, 1),
            bg_color=(0, 0, 0, 0),
            font_size=32,
            centered=True,
        )

        # draw loading bar
        bar_start = (100, 900)
        bar_size = (1720, 30)
        renderer.draw_rect(bar_start, bar_size, (0.3, 0.3, 0.3), convert_global=False)
        renderer.draw_rect(
            bar_start,
            (bar_size[0] * (step / self._loading_screen_steps), bar_size[1]),
            (1, 1, 1),
            convert_global=False,
        )

        renderer.display_draw_frame()

    @run_with_debug(reraise_errors=True, show_finish=True)
    def preload(self) -> None:
        """
        Load all textures n stuff.
        """
        start = perf_counter_ns()
        self._update_loading_screen(10, "loading textures")

        # load entity textures
        textures.load_images("assets/images/textures.zip")
        self._update_loading_screen(11)
        textures.load_images("assets/images/dirt_islands")
        self._update_loading_screen(12)
        textures.load_images("assets/images/bricks_gray")
        self._update_loading_screen(13)
        textures.load_images("assets/images/bricks_green")
        self._update_loading_screen(14)
        textures.load_images("assets/images/columns")
        self._update_loading_screen(15)
        textures.load_images("assets/images/platforms")
        self._update_loading_screen(15)
        textures.load_images("assets/images/missiles")
        textures.load_images("assets/images/missiles/maverick")
        self._update_loading_screen(15)
        textures.load_images("assets/images/weapons/railgun.zip")
        self._update_loading_screen(15)
        textures.load_images("assets/images/potions")
        self._update_loading_screen(16)
        textures.load_images("assets/images/Shield_6")
        self._update_loading_screen(16)
        textures.load_images("assets/images/bg1.zip")
        self._update_loading_screen(17)
        textures.load_images("assets/images/bg2.zip")
        self._update_loading_screen(18)
        textures.load_images("assets/images/bg3.zip")
        self._update_loading_screen(19)
        textures.load_images("assets/images/bg4.zip")
        self._update_loading_screen(20)
        textures.load_images("assets/images/animations/explosion.zip")
        self._update_loading_screen(21)
        textures.load_images("assets/images/animations/flame")

        for island in ISLANDS.values():
            island.load_textures()
        #
        # for entity in Updated.sprites():
        #     if hasattr(entity, "load_textures"):
        #         entity.load_textures()
        # self._update_loading_screen(22)

        for spawnable in GRAPHICS_SPAWNABLES.values():
            if hasattr(spawnable, "load_textures"):
                spawnable.load_textures()

        self._update_loading_screen(23)

        # Player.load_textures()
        # explosion.load_textures(size=(512, 512))

        self._update_loading_screen(24, "loading map")

        end = perf_counter_ns()
        load_time = round((end - start) / 1e6, 2)
        ic(load_time)

        self._update_loading_screen(24, "loading map")

    @property
    def id(self) -> int:
        """Why is this even here."""
        return -1

    @property
    def root(self) -> tp.Self:
        """Same question."""
        return self

    @run_with_debug()
    def load_map(self, map_path: tp.LiteralString) -> None:
        """
        Load a map from a JSON file.
        """
        # issue load command
        pv.COQ.put(
            ProcessCommand(
                type=ProcessCommandType.load_map, kwargs={"map_path": map_path}
            )
        )

        # stuff
        data = json.load(open(map_path, "r", encoding="utf-8"))
        renderer.display_set_title(f"amoginarium - {data['name']}")

        # set background
        if 0 <= data["background"] - 1 <= len(self._backgrounds):
            background: ParallaxBackground = self._backgrounds[data["background"] - 1]

        else:
            background: ParallaxBackground = self._backgrounds[0]

        # check if background has been assigned
        if not background.loaded:
            background.load_textures()

        self._background = background
        self._last_loaded = map_path

    def time_since_start(self) -> str:
        """
        Stylized time since game start
        gamestart being time since `mainloop` was called.
        """
        if hasattr(self, "_game_start"):
            t_ms = round(perf_counter() - self._game_start, 4)

        # if game hasn't started yet (base-game init), set time to -1
        else:
            t_ms = -1.0

        t1, t2 = str(t_ms).split(".")
        return (
            f"{get_fg_color(36)}{t1: >4}.{t2: <4}{get_fg_color(247)} | "
            f"{get_fg_color(14)}base {get_fg_color(247)} |> "
        )

    def _add_controller(self, controller: Controller) -> None:
        """
        Appends a new controller to the queue.
        """
        self._new_controllers.append(controller)

    def __clean_end(self, *_args: tp.Any, **_kwargs: tp.Any) -> None:
        ic("pygame end")
        self.running = False

    def _run_pygame(self) -> None:
        """
        Start pygame.
        """
        last = perf_counter()
        last_fps_print = 0

        active_scene: tp.Literal[
            "StartMenu", "PauseMenu", "StartSettings", "PauseSettings", "Game"
        ] = "StartMenu"

        @dataclass(frozen=True)
        class UIVisiblity:
            """this is a docstring."""

            start_menu: bool
            pause_menu: bool
            settings: bool

        ui_visibility: dict = {
            "StartMenu": UIVisiblity(True, False, False),
            "PauseMenu": UIVisiblity(False, True, False),
            "StartSettings": UIVisiblity(False, False, True),
            "PauseSettings": UIVisiblity(False, False, True),
            "Game": UIVisiblity(False, False, False),
        }

        # self.load_map("assets/maps/test.json")

        def load_ui_visibility() -> None:
            """Whatever this does (I didn't code it)."""
            visibility = ui_visibility[active_scene]
            start_menu.set_visibility(visibility.start_menu)
            pause_menu.set_visibility(visibility.pause_menu)
            settings.set_visibility(visibility.settings)

        def start_game() -> None:
            """Start game callback."""
            nonlocal active_scene
            active_scene = "Game"

            load_ui_visibility()
            # unpause game
            pv.COQ.put(ProcessCommand(type=ProcessCommandType.unpause))

        def reset_game(primary_call: bool = True) -> None:
            """Reset game callback."""
            nonlocal active_scene
            active_scene = "Game"

            if not isinstance(self._background, EllipsisType):
                self._background.reset_scroll()

            pv.COQ.put(ProcessCommand(type=ProcessCommandType.reset))
            SE_MANAGER.reset()

            if primary_call:
                load_ui_visibility()

            # wait for confirm
            while True:
                pv.CIQ.get()  # wait for confirm reset
                break

            # re-load map
            if not isinstance(self._last_loaded, EllipsisType):
                self.load_map(self._last_loaded)

            # respawn player
            Controllers.reset()
            KeyboardController.get()
            Controllers.update()

            # unpause logic
            pv.COQ.put(ProcessCommand(type=ProcessCommandType.unpause))

        def back_to_menu() -> None:
            """Menu callback."""
            nonlocal active_scene
            reset_game(False)
            active_scene = "StartMenu"

            load_ui_visibility()

        def pause_game() -> None:
            """Pause callback."""
            nonlocal active_scene
            active_scene = "PauseMenu"

            load_ui_visibility()
            pv.COQ.put(ProcessCommand(type=ProcessCommandType.pause))

        def open_settings() -> None:
            """Settings callback."""
            nonlocal active_scene
            if active_scene == "PauseMenu":
                active_scene = "PauseSettings"
            else:
                active_scene = "StartSettings"

            load_ui_visibility()

        def close_settings() -> None:
            """anti-settings callback."""
            nonlocal active_scene

            if active_scene == "PauseSettings":
                active_scene = "PauseMenu"
            else:
                active_scene = "StartMenu"

            load_ui_visibility()

        def handle_zoom(e) -> None:
            """Zoom callback."""
            self.global_vars.set_pixel_per_meter(
                self.global_vars.get_pixel_per_meter() * (1 + e.y / 30)
            )

        start_menu = StartMenu(start_game, open_settings, self.__clean_end)

        pause_menu = PauseMenu(start_game, reset_game, open_settings, back_to_menu)

        settings = SettingsMenu(close_settings)

        start_menu.show()

        mouse_cursor = UICursor()

        # draw background once
        while self.running:
            # print process comms
            while pv.BASE_COMM.poll(0):
                msg = pv.BASE_COMM.recv()
                colorizedStderrPrint(msg)

            # wait if buffer is being updated
            pv.WRITE_LOCK.acquire()
            pv.WRITE_LOCK.release()

            if pg.key.get_pressed()[pg.K_DOWN]:
                pv.global_vars.set_time_mult(0.01)
                t_mult = 0.01

            else:
                pv.global_vars.set_time_mult(self.time_multiplier)
                t_mult = self.time_multiplier

            # # check for new controllers
            # if len(self._new_controllers) > 0:
            #     tmp = self._new_controllers.copy()
            #     self._new_controllers.clear()
            #
            #     for new_controller in tmp:
            #         # spawn new player
            #         if Players.spawn_point:
            #             Player(
            #                 runtime_buffer=self._runtime_buffer,
            #                 coalition=Coalitions.blue,
            #                 controller=new_controller
            #             )
            #
            #         else:
            #             self._new_controllers.append(new_controller)

            # update commands
            while True:
                try:
                    item: ProcessCommand = pv.CIQ.get_nowait()

                except Empty:
                    break

                if item.type == BaseCommandType.spawn_dummy:
                    # try to spawn graphics dummy
                    cid = item.kwargs.pop("cid")

                    if cid in GRAPHICS_SPAWNABLES:
                        sync_id = item.kwargs.pop("id")
                        GRAPHICS_SPAWNABLES[cid](sync_id=sync_id, **item.kwargs)

                    else:
                        print_ic_style(
                            f"{CC.bfg.YELLOW}Unknown spawned item{CC.ctrl.ENDC}"
                            f": {cid} ({item})"
                        )

                elif item.type == BaseCommandType.spawn_island:
                    # try to spawn graphics dummy
                    cid = item.kwargs.pop("cid")

                    if cid in ISLANDS:
                        sync_id = item.kwargs.pop("id")
                        ISLANDS[cid](sync_id=sync_id, **item.kwargs)

            ppm = self.global_vars.get_pixel_per_meter()
            renderer.clear_display()

            # total delta since last call
            now = perf_counter()
            self.global_vars.set_time(time())

            delta = now - last
            delta *= t_mult  # slow-motion

            world_pos = self.global_vars.get_world_position()

            # TEMP SOLUTION - fix with controller rework
            display_updated = False
            for event in pg.event.get():
                if (
                    event.type in [pg.WINDOWRESIZED, pg.WINDOWMOVED, pg.VIDEORESIZE]
                    and not display_updated
                ):
                    renderer.display_update()
                    display_updated = True
                elif event.type == pg.MOUSEWHEEL:
                    if active_scene in ["Game", "PauseSettings", "PauseMenu"]:
                        handle_zoom(event)
                elif event.type == pg.QUIT:
                    self.__clean_end()

                # elif events.type == pg.JOYDEVICEADDED:
                #     self.__add_joystick(events)

                elif event.type == pg.KEYUP:
                    if event.key == pg.K_F11:
                        if renderer.display_state == "windowed_fullscreen":
                            renderer.display_set_windowed()
                        else:
                            renderer.display_windowed_fullscreen()
                    if event.key == pg.K_ESCAPE:
                        if active_scene == "Game":
                            pause_game()
                        elif active_scene == "PauseMenu":
                            start_game()
                        elif (
                            active_scene == "PauseSettings"
                            or active_scene == "StartSettings"
                        ):
                            close_settings()
                elif event.type == pg.MOUSEBUTTONUP:
                    if event.button == pg.BUTTON_LEFT:
                        for sprite in UIEntities:
                            sprite.check_click()

            mouse_cursor.gl_draw(delta)
            if active_scene in [
                "StartMenu",
                "PauseMenu",
                "StartSettings",
                "PauseSettings",
            ]:
                # update background music
                if not isinstance(self._background, EllipsisType):
                    self._background.set_position(world_pos.x * ppm)
                    self._background.draw(delta)

                renderer.flush()

                if active_scene in ["PauseMenu", "PauseSettings"]:
                    # handle groups
                    SyncedEntities.update_from_buffer()
                    Drawn_0.gl_draw(delta)
                    renderer.flush_layer(0)
                    Drawn_1.gl_draw(0)
                    renderer.flush_layer(1)
                    Drawn_2.gl_draw(0)
                    renderer.flush_layer(2)
                    renderer.flush()

                settings.gl_draw(delta)
                start_menu.gl_draw(delta)
                pause_menu.gl_draw(delta)

            elif active_scene == "Game":
                # only update fps every 200ms (for readability)
                if now - last_fps_print > 0.2:
                    self._pygame_fps = int(1 / delta)
                    last_fps_print = now

                # update controllers
                Controllers.update()

                # draw background
                if not isinstance(self._background, EllipsisType):
                    self._background.set_position(world_pos.x * ppm)
                    self._background.draw(delta)

                renderer.flush()

                # handle groups
                SyncedEntities.update_from_buffer()
                Drawn_0.gl_draw(delta)
                renderer.flush_layer(0)
                Drawn_1.gl_draw(0)
                renderer.flush_layer(1)
                Drawn_2.gl_draw(0)
                renderer.flush_layer(2)
                renderer.flush()

            # update global vars
            self.global_vars.update()

            self._total_loop_times.append((now - self._game_start, delta))
            self._pygame_loop_times.append(
                (now - self._game_start, perf_counter() - now)
            )
            last = now

            renderer.display_draw_frame()

        ic("pygame end")
        times = cum_timer.get_times()
        for func, values in sorted(times.items(), key=lambda e: e[1][0]):
            print_ic_style(
                f"{func}, called {values[1]} times {round(values[2], 3)}µs each, "
                f"totaling {round(values[0] / 1000, 2)}ms"
            )

        self.end()

    def draw_entities_only(self) -> None:
        """
        Only draw entities, no game updates or menus.
        """
        renderer.clear_display()

        if not isinstance(self._background, EllipsisType):
            self._background.draw(0)

        SyncedEntities.update_from_buffer()
        Drawn_0.gl_draw(0)
        Drawn_1.gl_draw(0)
        Drawn_2.gl_draw(0)
        renderer.flush_layer(0)
        renderer.flush_layer(1)
        renderer.flush_layer(2)
        renderer.flush()

        renderer.display_draw_frame()

    def mainloop(self) -> None:
        """
        Run the game.
        """
        self.running = True

        # self._pool.submit(self._run_logic)
        # self._pool.submit(self._run_comms)q
        self._run_pygame()

    @run_with_debug()
    def end(self) -> None:
        """
        Stop everything.
        """
        # send end to process
        pv.COQ.put(ProcessCommand(type=ProcessCommandType.quit))

        # check if end has already been called
        if self._ended:
            return
        self._ended = True

        Settings.scaling = self.global_vars.get_scaling()
        Settings.write()

        # tell threads to exit
        self.running = False

        ic("stopping game...")

        # quit pygame
        renderer.quit()

        # write debug data
        ic("writing debug data")

        makedirs("debug", exist_ok=True)
        with open(
            f"debug/graphic_debug_{self._git_branch}_{int(self._game_start)}.json",
            "w",
            encoding="utf-8",
        ) as out:
            json.dump(
                {"pygame": self._pygame_loop_times, "total": self._total_loop_times},
                out,
            )

        with open("graphic_debug.json", "w", encoding="utf-8") as out:
            json.dump(
                {"pygame": self._pygame_loop_times, "total": self._total_loop_times},
                out,
            )

        ic("done writing debug data")

        # stop threads
        ic("waiting for threads to quit...")
        ic("all threads exited")
