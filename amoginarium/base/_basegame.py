"""
_basegame.py
25. January 2024

Defines the core game

Author:
Nilusink
"""
import math
from time import perf_counter, strftime, time, perf_counter_ns
from concurrent.futures import ThreadPoolExecutor
from icecream import ic
import typing as tp
import pygame as pg
import json
import os

from OpenGL.GL import glClearColor
from typing_extensions import Any

from ._groups import HasBars, WallBouncer, CollisionDestroyed, Bullets, Players
from ._groups import Updated, GravityAffected, Drawn, FrictionXAffected
from ._pausemenu import PauseMenu
from ._settings_menu import SettingsMenu
from ._startmenu import StartMenu
from ..entities import SniperTurret, AkTurret, MinigunTurret, MortarTurret
from ..entities import CRAMTurret, TextEntity, BaseTurret, FlakTurret
from ..entities import Player, GrassIsland, GrayBrickIsland, Island
from ..entities import GreenBrickIsland, PillarIsland
from ..controllers import Controllers, Controller, GameController
from ..debugging import run_with_debug, print_ic_style, CC
from ._scrolling_background import ParalaxBackground
from ..shared import global_vars, Coalitions
from ..logic import SimpleLock, Color, Vec2
from ..audio import sounds, sound_effects
from ..render_bindings import renderer
from ..audio import BackgroundPlayer
from ..communications import TCPServer
from ..animations import explosion
from ._textures import textures
from ..settings import Settings
from ..ui import UIElement
from ..ui._event_handler import EventHandler


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


SPAWNABLES: dict[str, tp.Type[BaseTurret]] = {
    "turret.static.sniper": SniperTurret,
    "turret.static.ak47": AkTurret,
    "turret.static.minigun": MinigunTurret,
    "turret.static.mortar": MortarTurret,
    "turret.static.flak": FlakTurret,
    "turret.static.cram": CRAMTurret,
    "instructions.text": TextEntity,
}
ISLANDS: dict[str, tp.Type[Island]] = {
    "island.grass": GrassIsland,
    "island.brick.gray": GrayBrickIsland,
    "island.brick.green": GreenBrickIsland,
    "island.pillar": PillarIsland,
}


class BaseGame:
    running: bool = True
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
        global_vars.show_targets = show_targets
        self.time_multiplier = time_multiplier
        self._last_loaded = ...
        self._shifting = False

        # configure icecream
        if not debug:
            ic.disable()

        ic.configureOutput(prefix=self.time_since_start)

        # multi-threading stuff
        self._pool = ThreadPoolExecutor(max_workers=5)

        # debugging
        self._logic_loop_times: list[tuple[float, float]] = []
        self._pygame_loop_times: list[tuple[float, float]] = []
        self._comms_loop_times: list[tuple[float, float]] = []
        self._total_loop_times: list[tuple[float, float]] = []

        # time since start, n_bullets, loop_time
        self._n_bullets_times: list[tuple[float, float, float]] = []

        self._pygame_fps: int = 0
        self._logic_fps: int = 0
        self._comms_ping: int = 0

        # logic setup
        self._new_controllers: list[Controller] = []
        self._new_controllers_lock = SimpleLock()

        self._controllers_cid = Controllers.on_new_controller(
            self._add_controller
        )

        # other things
        # self._in_next_loop: list[BoundFunction] = []

        # server setup
        self._server = TCPServer(("0.0.0.0", game_port))

        # initialize pygame (logic) and renderer
        pg.init()
        pg.mixer.init(channels=64, buffer=1024)
        renderer.init("amoginarium")

        # initialize background
        self._background = ...
        self._bg_color = (0, 0, 0)
        self._background_player = BackgroundPlayer()
        self._background_player.volume = .6

        # add decorator with callback to self.end
        for func in ("_run_pygame", "_run_logic", "_run_comms"):
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
                *global_vars.screen_size.xy,
                parallax_multiplier=1.6,
            ),
            ParalaxBackground(
                "bg2",
                *global_vars.screen_size.xy,
                parallax_multiplier=1.6,
            ),
            ParalaxBackground(
                "bg3",
                *global_vars.screen_size.xy,
                parallax_multiplier=1.6,
            ),
            ParalaxBackground(
                "bg4",
                *global_vars.screen_size.xy,
                parallax_multiplier=1.6,
            )
        ]

        # load map
        self.preload()

        self._game_start = 0

    @run_with_debug(reraise_errors=True, show_finish=True)
    def preload(self) -> None:
        """
        load all textures n stuff
        """
        start = perf_counter_ns()
        # load sounds
        sounds.load_sounds("assets/audio/background")
        sounds.load_sounds("assets/audio/effects/ak47")
        sounds.load_sounds("assets/audio/effects/minigun")
        sounds.load_sounds("assets/audio/effects/explosions")
        sounds.load_sounds("assets/audio/effects/shots")
        sounds.load_sounds("assets/audio/effects/reloads")
        sounds.load_sounds("assets/audio/effects/ui")
        self._background_player.assign_scope("background")

        # load entity textures
        textures.load_images("assets/images/textures.zip")
        textures.load_images("assets/images/dirt_islands.zip")
        textures.load_images("assets/images/bricks_gray")
        textures.load_images("assets/images/bricks_green")
        textures.load_images("assets/images/column")
        textures.load_images("assets/images/bg1.zip")
        textures.load_images("assets/images/bg2.zip")
        textures.load_images("assets/images/bg3.zip")
        textures.load_images("assets/images/bg4.zip")
        textures.load_images("assets/images/animations/explosion.zip")

        for island in ISLANDS.values():
            island.load_textures()

        Player.load_textures()
        BaseTurret.load_textures()
        explosion.load_textures(size=(512, 512))
        end = perf_counter_ns()
        load_time = (end-start)/1e6
        ic(load_time)

    @property
    def id(self) -> int:
        return -1

    @property
    def root(self) -> tp.Self:
        return self

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
        Players.spawn_point = Vec2.from_cartesian(*data["spawn_pos"])

        # set background
        if 0 <= data["background"] - 1 <= len(self._backgrounds):
            self._background = self._backgrounds[data["background"] - 1]

        else:
            self._background = self._backgrounds[0]

        # check if background has been assigned
        if not self._background.loaded:
            self._background.load_textures()

        # # spwan a lot of bulllets
        # Players.spawn_point = Vec2.from_cartesian(950, -100)
        # n_bullets = 150
        # x_spacing = global_vars.screen_size.x / n_bullets

        # for i in range(n_bullets):
        #     Bullet(
        #          self,
        #          Vec2.from_cartesian(0 + x_spacing*i, 0),
        #          Vec2.from_cartesian(0, 100), time_to_life=5
        #     )
        #     Bullet(
        #          self,
        #          Vec2.from_cartesian(0 + x_spacing*i, 100),
        #          Vec2.from_cartesian(0, 100), time_to_life=5
        #     )
        # return

        # load islands
        for island in data["platforms"]:
            island_type = GrassIsland
            if "type" in island:
                if island["type"] in ISLANDS:
                    island_type = ISLANDS[island["type"]]

            if "size" in island:
                island_type(
                    Vec2.from_cartesian(*island["pos"]),
                    size=Vec2.from_cartesian(*island["size"]),
                )

            elif "form" in island:
                island_type(
                    Vec2.from_cartesian(*island["pos"]),
                    form=island["form"],
                )

            else:
                print_ic_style(
                    f"{CC.fg.RED}invalid island: "
                    f"{CC.fg.YELLOW}{island}"
                )

        # load entities
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

            try:
                SPAWNABLES[entity["type"]](
                    Coalitions.red,
                    Vec2.from_cartesian(*entity["pos"]),
                    **args
                )

            except TypeError:
                print_ic_style(
                    f"{CC.fg.RED}invalid arguments for "
                    f"{CC.fg.YELLOW}{entity["type"]}{CC.fg.RED}: "
                    f"\"{CC.fg.YELLOW}{args}{CC.fg.RED}\""
                )

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
        return f"{t1: >4}.{t2: <4} |> "

    @staticmethod
    def run_in_next_loop[**A, R](
            func: tp.Callable[A, R],
            *args: A.args,
            **kwargs: A.kwargs
    ) -> None:
        global_vars.in_next_loop.append({
            "func": func,
            "args": args,
            "kwargs": kwargs
        })

    def _add_controller(self, controller: Controller) -> None:
        """
        appends a new controller to the queue
        """
        self._new_controllers_lock.aquire()
        self._new_controllers.append(controller)
        self._new_controllers_lock.release()

    def __add_joystick(self, event: pg.Event) -> None:
        joy = pg.joystick.Joystick(event.device_index)
        c = GameController.get(joy.get_guid(), joy)

        # re-assign pygame joystick instance
        c.set_joystick(joy)

    def __clean_end(self, *_args: Any, **_kwargs: Any) -> None:
        ic("pygame end")
        self.running = False

    def _run_pygame(self) -> None:
        """
        start pygame
        """
        last = perf_counter()
        last_fps_print = 0
        clock = pg.time.Clock()

        active_scene: tp.Literal["StartMenu", "PauseMenu", "StartSettings", "PauseSettings", "Game"] = "StartMenu"

        self.load_map("assets/maps/test.json")

        EventHandler.add_event(pg.QUIT, callback=self.__clean_end)
        EventHandler.add_event(pg.JOYDEVICEADDED, callback=self.__add_joystick)

        # self.load_map("assets/maps/test.json")

        def start_game():
            nonlocal active_scene
            active_scene = "Game"

            start_menu.hide()
            settings.hide()
            pause_menu.hide()

            game_ui_dummy.show()

        def reset_game():
            nonlocal active_scene
            active_scene = "Game"

            for entity in Updated.sprites():
                entity.kill()

            self._background.reset_scroll()
            global_vars.reset()
            Updated.world_position *= 0

            self.load_map(self._last_loaded)

            # respawn players
            for player in Players.sprites():
                player.respawn()

            # UI
            start_menu.hide()
            settings.hide()
            pause_menu.hide()

            game_ui_dummy.show()

        def back_to_menu():
            nonlocal active_scene
            reset_game()
            active_scene = "StartMenu"

            game_ui_dummy.hide()
            settings.hide()
            pause_menu.hide()

            start_menu.show()

        def pause_game():
            nonlocal active_scene
            active_scene = "PauseMenu"

            start_menu.hide()
            settings.hide()
            game_ui_dummy.hide()

            pause_menu.show()

        def open_settings():
            nonlocal active_scene
            if active_scene == "PauseMenu":
                active_scene = "PauseSettings"

                pause_menu.hide()
                start_menu.hide()
                game_ui_dummy.hide()

                settings.show()
            else:
                active_scene = "StartSettings"

                game_ui_dummy.hide()
                pause_menu.hide()
                start_menu.hide()

                settings.show()

        def close_settings():
            nonlocal active_scene
            if active_scene == "PauseSettings":
                active_scene = "PauseMenu"

                start_menu.hide()
                settings.hide()
                game_ui_dummy.hide()

                pause_menu.show()
            else:
                active_scene = "StartMenu"

                game_ui_dummy.hide()
                pause_menu.hide()
                settings.hide()

                start_menu.show()

        start_menu = StartMenu(
            start_game, open_settings, self.__clean_end
        )

        pause_menu = PauseMenu(
            start_game, reset_game, open_settings, back_to_menu
        )
        pause_menu.add_fullscreen_event(pg.KEYUP, key=pg.K_ESCAPE, callback=lambda *_: start_game())

        settings = SettingsMenu(
            close_settings
        )

        # Temporary solution
        game_ui_dummy: UIElement = UIElement()
        game_ui_dummy.add_fullscreen_event(pg.KEYUP, key=pg.K_ESCAPE, callback=lambda *_: pause_game())

        start_menu.show()

        # draw background once
        while self.running:
            # total delta since last call
            now = perf_counter()
            global_vars.time = time()

            delta = now - last

            delta *= self.time_multiplier  # slow-motion

            EventHandler.check_events()

            if active_scene in ["StartMenu", "PauseMenu", "StartSettings", "PauseSettings"]:
                # update background music
                try:  # throws error on game end
                    self._background_player.update()

                except pg.error:
                    break

                self._background.scroll(delta / 200)
                self._background.draw(delta)

                if active_scene in ["PauseMenu", "PauseSettings"]:
                    Drawn.gl_draw()
                    HasBars.gl_draw()

                start_menu.draw_if_visible()
                pause_menu.draw_if_visible()
                settings.draw_if_visible()

                pg.display.flip()
                # debugging kopieren - @
                clock.tick(global_vars.max_fps)

                self._game_start = perf_counter()
                last = now

            elif active_scene == "Game":
                self._update_logic(delta, now)

                # pygame loop time
                start = perf_counter()

                # only update fps every 200ms (for readability)
                if now - last_fps_print > .2:
                    self._pygame_fps = int(1 / delta)
                    last_fps_print = now

                # update background music
                try:  # throws error on game end
                    self._background_player.update()

                except pg.error:
                    break

                # clear screen
                glClearColor(0, 0, 0, 1)

                _, max_player_pos = Players.get_position_extremes()

                # background_pos_left = self._background.position + 60

                if self._shifting:
                    background_pos_right = self._background.position \
                                           + global_vars.screen_size.x - 1400

                    if max_player_pos.x > background_pos_right:
                        # world speed coefficient:
                        # V(x)=ℯ^( ( (1400-x) / 800 )^2 )

                        speed_coeff = (abs((
                                                   self._background.position
                                                   + global_vars.screen_size.x
                                                   - 1400
                                           ) - max_player_pos.x) / 800) ** 2
                        speed_coeff = math.exp(speed_coeff)

                        self._background.scroll(delta * 3 * speed_coeff)
                        Updated.world_position.x = self._background.position

                    else:
                        self._shifting = False

                else:
                    background_pos_right = self._background.position \
                                           + global_vars.screen_size.x - 900

                    if max_player_pos.x > background_pos_right:
                        self._background.scroll(delta * 3)
                        Updated.world_position.x = self._background.position
                        self._shifting = True

                # elif min_player_pos.x < background_pos_left:
                #     self._background.scroll(-delta * 15)
                #     Updated.world_position.x = self._background.position

                # draw background
                self._background.draw(delta)

                # global_vars.pixel_per_meter *= .999

                # handle groups
                Drawn.gl_draw()
                HasBars.gl_draw()

                # draw in_loop
                for f in [*global_vars.in_next_loop, *global_vars.get_in_loop()]:
                    f["func"](*f["args"], **f["kwargs"])

                global_vars.in_next_loop.clear()

                # # show fps
                # fps_surf = self.font.render(
                #     f"{self._pygame_fps} FPS (render)", False, (255, 255, 255,
                # 255)
                # )

                # self.top_layer.blit(fps_surf, (0, 0))
                # fps_surf = self.font.render(
                #     f"{self._logic_fps} FPS (logic)", False, (255, 255, 255, 255)
                # )
                # self.top_layer.blit(fps_surf, (0, 15))
                # ping_surf = self.font.render(
                #     f"{self._comms_ping} ms ping", False, (255, 255, 255, 255)
                # )
                # self.top_layer.blit(ping_surf, (0, 30))

                # render_text(
                #     f"{self._pygame_fps} FPS (render)",
                #     0, 0,
                #     self.font
                # )

                pg.display.flip()

                self._pygame_loop_times.append(
                    (now - self._game_start, perf_counter() - start)
                )
                self._total_loop_times.append(
                    (now - self._game_start, delta)
                )
                last = now

                clock.tick(global_vars.max_fps)

        ic("pygame end")
        self.end()

    def _run_logic(self) -> None:
        """
        start game logic
        """
        last = perf_counter()
        last_fps_print = 0
        while self.running:
            now = perf_counter()

            # minimum loop time of .5 ms (so the CPU isn't stressed too much)
            while now - last < .0005:
                now = perf_counter()

            delta = now - last

            # only update fps every 200ms (for readability)
            if now - last_fps_print > .2:
                self._logic_fps = int(1 / delta)
                last_fps_print = now

            self._update_logic(delta, now)

            last = now

        ic("logic end")

    def _update_logic(self, delta, now) -> float:
        start = perf_counter()

        # check for new controllers
        if len(self._new_controllers) > 0:
            self._new_controllers_lock.aquire()
            tmp = self._new_controllers.copy()
            self._new_controllers.clear()
            self._new_controllers_lock.release()

            for new_controller in tmp:
                # spawn new player
                Player(coalition=Coalitions.blue, controller=new_controller)
                ic(new_controller, Player)

        # update sounds
        sound_effects.update()

        # update entities
        GravityAffected.calculate_gravity(delta)
        FrictionXAffected.calculate_friction(delta)
        WallBouncer.update()

        Updated.update(delta)

        CollisionDestroyed.update()

        logic_time = perf_counter() - start
        self._logic_loop_times.append(
            (now - self._game_start, logic_time)
        )
        self._n_bullets_times.append(
            (now - self._game_start, len(Bullets.sprites()), logic_time)
        )

        return logic_time

    def _run_comms(self) -> None:
        """
        start communications
        """
        # asyncio.run(self._server.run())
        ic("comms end")

        # TODO: controller latency in graph

        return

    def mainloop(self) -> None:
        """
        run the game
        """
        self._game_start = perf_counter()

        # self._pool.submit(self._run_logic)
        self._pool.submit(self._run_comms)
        self._run_pygame()

    @run_with_debug()
    def end(self) -> None:
        """
        stop everything
        """
        # check if end has already been called
        if not self.running:
            return

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
                "logic": self._logic_loop_times,
                "comms": self._comms_loop_times,
                "bullets": self._n_bullets_times,
                "pygame": self._pygame_loop_times,
                "total": self._total_loop_times
            }, out)

        ic("done writing debug data")

        # stop threads
        ic("waiting for threads to quit...")
        self._pool.shutdown(wait=True)
        ic("all threads exited")
