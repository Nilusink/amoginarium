"""
_basegame.py
25. January 2024

Defines the core game

Author:
Nilusink
"""
from OpenGL.GL import glClearColor, glViewport, glMatrixMode, GL_PROJECTION, glLoadIdentity, glOrtho, GL_MODELVIEW, \
    glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_VIEWPORT, glGetIntegerv
from time import perf_counter, strftime, time, perf_counter_ns, sleep
from multiprocessing import Process
from dataclasses import dataclass
from icecream import ic, colorizedStderrPrint
from queue import Empty
import typing as tp
import pygame as pg
import numpy
import json

# from ..shared.controllers import Controllers, Controller, GameController
from .. import pv
from ..shared.debugging import run_with_debug, print_ic_style, cum_timer
from ..shared.debugging import print_with_prefix, CC, get_fg_color
from ..shared.utility import Vec2, convert_coord
from ..shared import ProcessCommand, ProcessCommandType, BaseCommandType
from ..shared.settings import Settings
from ..graphics.render_bindings import renderer
from ..graphics.ui import UICursor
from ..graphics.entities import UIEntities, Drawn_0, Drawn_1, SyncedEntities, Drawn_2
from ..graphics.controllers import Controller, Controllers, KeyboardController
from ..graphics.logic_dummies import GRAPHICS_SPAWNABLES, ISLANDS
from ..logic import run_continuous
from ._scrolling_background import ParalaxBackground
from ._settings_menu import SettingsMenu
from ._pausemenu import PauseMenu
from ._startmenu import StartMenu
from ._textures import textures


class BoundFunction(tp.TypedDict):
    func: tp.Callable
    args: tuple
    kwargs: dict


def current_time() -> str:
    """
    helper function for IC debugging
    """
    ms = str(round(perf_counter(), 4)).split(".")[1]
    return f"{strftime('%H:%M:%S')}.{ms: <4} |> "


class BaseGame:
    running: bool = False
    _last_logic: float
    _bg_color: tuple[float, float, float]
    _instance: tp.Self = ...

    def __new__(cls, *args, **kwargs) -> "BaseGame":
        # only one instance can exist
        if cls._instance is not ...:
            return cls._instance

        new = super(BaseGame, cls).__new__(cls)
        cls._instance = new
        return new

    def __init__(
            self,
            debug: bool = False,
            game_port: int = 12345,
            show_targets: bool = False,
            time_multiplier: float = 1
    ) -> None:
        self._game_start = perf_counter()
        ic.configureOutput(
            prefix="",
            outputFunction=lambda s, **kwargs: print_with_prefix(
                s,
                prefix=self.time_since_start(),
                **kwargs
            ),
        )

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
                "time_multiplier": time_multiplier
            }
        )
        self._logic_process.start()

        # pause logic process until game start
        pv.COQ.put(ProcessCommand(type=ProcessCommandType.pause))

        self.global_vars = pv.global_vars
        self.global_vars.show_targets = show_targets
        self.time_multiplier = time_multiplier
        self._last_loaded: tp.LiteralString = ...
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
        pg.init()
        # pg.mixer.init(channels=64, buffer=1024)
        renderer.init("amoginarium")

        self._loading_screen_steps = 28
        self._loading_screen_info = "Window init"

        # initialize background
        self._background: ParalaxBackground = ...
        self._bg_color = (0, 0, 0)
        self._ended = False

        self._update_loading_screen(1)

        self.__windowed_fullscreen()

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
                run_with_debug(
                    on_fail=lambda *_: self.end(),
                    reraise_errors=False
                )(getattr(self, func))
            )

        self._backgrounds = [
            ParalaxBackground(
                "bg1",
                *self.global_vars.get_screen_size().xy,
                parallax_multiplier=1.6,
            ),
            ParalaxBackground(
                "bg2",
                *self.global_vars.get_screen_size().xy,
                parallax_multiplier=1.6,
            ),
            ParalaxBackground(
                "bg3",
                *self.global_vars.get_screen_size().xy,
                parallax_multiplier=1.6,
            ),
            ParalaxBackground(
                "bg4",
                *self.global_vars.get_screen_size().xy,
                parallax_multiplier=1.6,
            )
        ]

        self._update_loading_screen(2, "loading sounds")

        # load textures and sounds
        self.preload()

    def _update_loading_screen(self, step: int, info: str = ...) -> None:
        if info is not ...:
            self._loading_screen_info = info

        # 2. Clear the entire window buffer with that black color
        # (Note: glClear ignores glViewport, so it will clean the whole window)

        # EventHandler.check_events()

        glClearColor(0.0, 0.0, 0.0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # draw info text
        renderer.draw_text(
            (960, 850),
            self._loading_screen_info,
            (1, 1, 1),
            (0, 0, 0, 0),
            font_size=32,
            centered=True,
        )

        # draw loading bar
        bar_start = (100, 900)
        bar_size = (1720, 30)
        renderer.draw_rect(
            bar_start,
            bar_size,
            (.3, .3, .3),
            convert_global=False
        )
        renderer.draw_rect(
            bar_start,
            (
                bar_size[0] * (step / self._loading_screen_steps),
                bar_size[1]
            ),
            (1, 1, 1),
            convert_global=False
        )

        pg.display.flip()

    @run_with_debug(reraise_errors=True, show_finish=True)
    def preload(self) -> None:
        """
        load all textures n stuff
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

        for spwanable in GRAPHICS_SPAWNABLES.values():
            if hasattr(spwanable, "load_textures"):
                spwanable.load_textures()

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
        return -1

    @property
    def root(self) -> tp.Self:
        return self

    @run_with_debug()
    def load_map(self, map_path: tp.LiteralString) -> None:
        """
        load a map from a json file
        """
        # issue load command
        pv.COQ.put(ProcessCommand(
            type=ProcessCommandType.load_map,
            kwargs={"map_path": map_path}
        ))

        # stuff
        data = json.load(open(map_path, "r"))
        pg.display.set_caption(f"amoginarium - {data["name"]}")

        # set background
        if 0 <= data["background"] - 1 <= len(self._backgrounds):
            self._background = self._backgrounds[data["background"] - 1]

        else:
            self._background = self._backgrounds[0]

        # check if background has been assigned
        if not self._background.loaded:
            self._background.load_textures()

        self._last_loaded = map_path

    def time_since_start(self) -> str:
        """
        styleized time since game start
        gamestart being time since `mainloop` was called
        """
        if hasattr(self, "_game_start"):
            t_ms = round(perf_counter() - self._game_start, 4)

        # if game hasn't started yet (bassegame init), set time to -1
        else:
            t_ms = -1.0

        t1, t2 = str(t_ms).split(".")
        return (
            f"{get_fg_color(36)}{t1: >4}.{t2: <4}{get_fg_color(247)} | "
            f"{get_fg_color(14)}base {get_fg_color(247)} |> "
        )

    def _add_controller(self, controller: Controller) -> None:
        """
        appends a new controller to the queue
        """
        self._new_controllers.append(controller)

    def __clean_end(self, *_args: tp.Any, **_kwargs: tp.Any) -> None:
        ic("pygame end")
        self.running = False

    def __scaling_restricted_ratio(self, width: float, height: float, ratio: float):
        # Calculate the aspect ratio of the current window
        window_ratio = width / height

        if window_ratio > ratio:
            # Window is too wide: height is the constraint
            view_h = height
            view_w = int(height * ratio)
            offset_x = (width - view_w) // 2
            offset_y = 0
        else:
            # Window is too tall: width is the constraint
            view_w = width
            view_h = int(width / ratio)
            offset_x = 0
            offset_y = (height - view_h) // 2

        return offset_x, offset_y, view_w, view_h

    def __windowed_fullscreen(self) -> None:
        pg.display.set_mode(
            (0, 0),
            pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE | pg.FULLSCREEN
        )

        size = numpy.ndarray.tolist(glGetIntegerv(GL_VIEWPORT))
        size = size[2], size[3]

        pos = pg.display.get_window_position()

        pg.display.set_mode(
            (0, 0),
            pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE
        )

        self.__window_update(*size)

        pg.display.set_window_position(pos)

    def __window_update(self, width: float = ..., height: float = ...) -> None:
        if width is ...:
            width = pg.display.get_window_size()[0]
        if height is ...:
            height = pg.display.get_window_size()[1]

        res_x, res_y = self.global_vars.get_resolution().xy
        res_ratio = res_x / res_y

        vp_x, vp_y, vp_w, vp_h = self.__scaling_restricted_ratio(width, height, res_ratio)

        scaling = self.global_vars.get_scaling()

        if scaling == "bars":
            # Tell OpenGL to only draw inside the calculated aspect-correct rectangle
            glViewport(vp_x, vp_y, vp_w, vp_h)
            pg.display.set_mode(
                (width, height),
                pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE
            )
            self.global_vars.set_screen_size_real(
                convert_coord((width, height), Vec2)
            )

            self.global_vars.set_screen_size_fac(Vec2().from_cartesian(
                res_x / vp_w, res_y / vp_h
            ))
            self.global_vars.set_screen_size_offset(Vec2().from_cartesian(
                vp_x, vp_y
            ))

        elif scaling == "fixed_aspect_ratio":
            pg.display.set_mode(
                (vp_w, vp_h),
                pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE
            )
            s_size_real = convert_coord((vp_w, vp_h), Vec2)
            self.global_vars.set_screen_size_real(s_size_real)

            self.global_vars.set_screen_size_fac(Vec2().from_cartesian(
                res_x / s_size_real.x, res_y / s_size_real.y
            ))
            self.global_vars.set_screen_size_offset(Vec2().from_cartesian(
                0, 0
            ))

        else:
            pg.display.set_mode(
                (width, height),
                pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE
            )
            glViewport(0, 0, width, height)

            s_size_real =  convert_coord((width, height), Vec2)
            self.global_vars.set_screen_size_real(s_size_real)

            self.global_vars.set_screen_size_fac(Vec2().from_cartesian(
                res_x / s_size_real.x, res_y / s_size_real.y
            ))
            self.global_vars.set_screen_size_offset(Vec2().from_cartesian(
                0, 0
            ))

        # 4. FIXED COORDINATE SPACE
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glOrtho(0, res_x, res_y, 0, -1, 1)

        # Switch back to Modelview for drawing
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _run_pygame(self) -> None:
        """
        start pygame
        """
        last = perf_counter()
        last_fps_print = 0
        clock = pg.time.Clock()

        active_scene: tp.Literal["StartMenu", "PauseMenu", "StartSettings", "PauseSettings", "Game"] = "StartMenu"

        @dataclass(frozen=True)
        class UIVisiblity:
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

        def load_ui_visibility():
            visibility = ui_visibility[active_scene]
            start_menu.set_visibility(visibility.start_menu)
            pause_menu.set_visibility(visibility.pause_menu)
            settings.set_visibility(visibility.settings)

        def start_game():
            nonlocal active_scene
            active_scene = "Game"

            load_ui_visibility()
            # unpause game
            pv.COQ.put(ProcessCommand(type=ProcessCommandType.unpause))

        def reset_game(primary_call: bool = True):
            nonlocal active_scene
            active_scene = "Game"

            self._background.reset_scroll()

            if self._last_loaded is not ...:
                self.load_map(self._last_loaded)

            if primary_call:
                load_ui_visibility()

        def back_to_menu():
            nonlocal active_scene
            reset_game(False)
            active_scene = "StartMenu"

            load_ui_visibility()

        def pause_game():
            nonlocal active_scene
            active_scene = "PauseMenu"

            load_ui_visibility()
            pv.COQ.put(ProcessCommand(type=ProcessCommandType.pause))

        def open_settings():
            nonlocal active_scene
            if active_scene == "PauseMenu":
                active_scene = "PauseSettings"
            else:
                active_scene = "StartSettings"

            load_ui_visibility()

        def close_settings():
            nonlocal active_scene

            if active_scene == "PauseSettings":
                active_scene = "PauseMenu"
            else:
                active_scene = "StartMenu"

            load_ui_visibility()

        def handle_zoom(event):
            self.global_vars.set_pixel_per_meter(
                self.global_vars.get_pixel_per_meter() * (1 + event.y / 30)
            )

        start_menu = StartMenu(
            start_game, open_settings, self.__clean_end
        )

        pause_menu = PauseMenu(
            start_game, reset_game, open_settings, back_to_menu
        )

        settings = SettingsMenu(
            close_settings,
            self.__window_update
        )

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
                        GRAPHICS_SPAWNABLES[cid](
                            sync_id=sync_id,
                            **item.kwargs
                        )

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
                        ISLANDS[cid](
                            sync_id=sync_id,
                            **item.kwargs
                        )

            glClearColor(0.0, 0.0, 0.1, 1)

            # 2. Clear the entire window buffer with that black color
            # (Note: glClear ignores glViewport, so it will clean the whole window)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # total delta since last call
            now = perf_counter()
            self.global_vars.set_time(time())

            delta = now - last
            delta *= self.time_multiplier  # slow-motion

            world_pos = self.global_vars.get_world_position()

            # TEMP SOLUTION - fix with controller rework
            for event in pg.event.get():
                if event.type == pg.VIDEORESIZE:
                    self.__window_update(*event.size)
                elif event.type == pg.MOUSEWHEEL:
                    if active_scene in ["Game", "PauseSettings", "PauseMenu"]:
                        handle_zoom(event)
                elif event.type == pg.QUIT:
                    self.__clean_end()

                # elif event.type == pg.JOYDEVICEADDED:
                #     self.__add_joystick(event)

                elif event.type == pg.KEYUP:
                    if event.key == pg.K_F11:
                        self.__windowed_fullscreen()
                    if event.key == pg.K_ESCAPE:
                        if active_scene == "Game":
                            pause_game()
                        elif active_scene == "PauseMenu":
                            start_game()
                        elif active_scene == "PauseSettings":
                            close_settings()
                        elif active_scene == "StartSettings":
                            close_settings()
                elif event.type == pg.MOUSEBUTTONUP:
                    if event.button == pg.BUTTON_LEFT:
                        for sprite in UIEntities:
                            sprite.check_click()

            mouse_cursor.gl_draw(delta)
            if active_scene in ["StartMenu", "PauseMenu", "StartSettings", "PauseSettings"]:
                # update background music
                self._background.scroll(delta / 200)
                self._background.draw(delta)

                if active_scene in ["PauseMenu", "PauseSettings"]:
                    SyncedEntities.update_from_buffer()
                    Drawn_0.gl_draw(0)
                    Drawn_0.gl_draw(0)

                settings.gl_draw(delta)
                start_menu.gl_draw(delta)
                pause_menu.gl_draw(delta)

            elif active_scene == "Game":
                # only update fps every 200ms (for readability)
                if now - last_fps_print > .2:
                    self._pygame_fps = int(1 / delta)
                    last_fps_print = now

                # update controllers
                Controllers.update()

                # draw background
                self._background.set_position(world_pos.x)
                self._background.draw(delta)

                # handle groups
                SyncedEntities.update_from_buffer()
                Drawn_0.gl_draw(delta)
                Drawn_1.gl_draw(delta)
                Drawn_2.gl_draw(delta)

            pg.display.flip()

            # update global vars
            self.global_vars.update()

            self._total_loop_times.append(
                (now - self._game_start, delta)
            )
            self._pygame_loop_times.append(
                (now - self._game_start, perf_counter() - now)
            )
            last = now

            # clock.tick(self.global_vars.get_max_fps())

        ic("pygame end")
        times = cum_timer.get_times()
        for func, values in sorted(times.items(), key=lambda e: e[1][0]):
            print_ic_style(f"{func}, called {values[1]} times {round(values[2], 3)}µs each, totaling {round(values[0] / 1000, 2)}ms")

        self.end()

    def draw_entities_only(self) -> None:
        """
        only draw entities, no game updates or menus
        """
        glClearColor(0.0, 0.0, 0.1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self._background.draw(0)
        Drawn_0.gl_draw()
        Drawn_1.gl_draw()

        pg.display.flip()

    def mainloop(self) -> None:
        """
        run the game
        """
        self.running = True

        # self._pool.submit(self._run_logic)
        # self._pool.submit(self._run_comms)q
        self._run_pygame()

    @run_with_debug()
    def end(self) -> None:
        """
        stop everything
        """
        # send end to process
        pv.COQ.put(ProcessCommand(
            type=ProcessCommandType.quit
        ))

        # check if end has already been called
        if self._ended:
            return
        self._ended = True

        Settings.scaling = self.global_vars.get_scaling()
        Settings.write()

        # tell threads to exit
        self.running = False

        # tell server to shutdown
        # with suppress(RuntimeError):
        # self._server.close()

        ic("stopping game...")

        # quit pygame
        pg.quit()

        # write debug data
        ic("writing debug data")
        with open("debug.json", "w") as out:
            json.dump({
                "pygame": self._pygame_loop_times,
                "total": self._total_loop_times
            }, out)

        ic("done writing debug data")

        # stop threads
        ic("waiting for threads to quit...")
        ic("all threads exited")
