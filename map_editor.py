"""
map_editor.py
08. February 2024

all controller types should inherit from this

Author:
Nilusink
"""
raise DeprecationWarning("map editor hasn't been updated yet!")

from pginter.types import Color, StringVar
from PIL.Image import open as iopen
from threading import Thread  # for opening files without disrupting pginter
from pginter import widgets
from icecream import ic
import crossfiledialog
import pginter as pgi
import typing as tp
import pygame as pg
import pydantic
import os

from amoginarium.logic import Vec2
from amoginarium.base import BaseGame  # needed to import Entities
from amoginarium.entities import Island


class PlatformDict(pydantic.BaseModel):
    pos: tuple[float, float]
    size: tuple[float, float]
    texture: str


class MapDict(pydantic.BaseModel):
    name: str
    background: (
            str
            | tuple[float, float, float]
            | tuple[float, float, float, float]
    )
    spawn_pos: tuple[float, float]
    platforms: tp.Optional[list[PlatformDict]] = []
    entities: tp.Optional[list[dict]] = []


class MapRenderer:
    def __init__(
            self,
            name_var: StringVar,
            map_path: str = ...
    ) -> None:
        self.map_path = map_path
        self._map_params: MapDict = ...
        self._islands: list[Island] = []
        self._name_var = name_var

        # view variables
        self._map_pos = Vec2()
        self._scale = 1
        self.mouse_moving = False
        self.last_mouse_pos = Vec2()
        self.last_mouse_scroll = Vec2()

        if self.map_path is ...:
            self.map_path = "assets/maps/tmp.json"

        if os.path.exists(self.map_path):
            self.load_map(self.map_path)

        else:
            self.create_map()

    @property
    def scale(self) -> float:
        """
        currently applied map scale
        """
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        self._scale = value

    @tp.overload
    def move_by(self, x: float, y: float) -> None:
        ...

    @tp.overload
    def move_by(self, delta: Vec2) -> None:
        ...

    def move_by(self, *args, **kwargs) -> None:
        """
        move the viewport by x and y pixels
        """
        args = list(args)
        if isinstance(args[0], Vec2):
            x, y = args[0].xy

        else:
            # first, check if either x or y are specified
            # in the keyword arguments. If any of the variables
            # are still unspecified, fill them with the arguments
            # from args
            x = ...
            y = ...
            if "x" in kwargs:
                x = kwargs["x"]

            if "y" in kwargs:
                y = kwargs["y"]

            if x is ...:
                x = args.pop(0)

            if y is ...:
                y = args.pop(0)

        # applying scale
        x *= 1 / self.scale
        y *= 1 / self.scale

        self._map_pos += Vec2().from_cartesian(x, y)

    def scale_by(self, value: float) -> None:
        """
        does some math stuff and scales the map
        """
        self.scale *= 1 + value / -100

    def load_map(self, path: str) -> None:
        """
        load an existing map

        map file layout::

            {
                "name": "map name",
                "background": (rgb or argb tuple),
                "spawn_pos": (x, y),
                "platforms": [
                    {
                        "pos": (left, top),
                        "size": (width, height),
                        "texture": "path/to/texture.png"
                    }
                ],
                "entities": [
                    {
                        "pos": (x, y),
                        "type": "type of entity",
                        # optional
                        "vel": (vel_x, vel_y)
                    }
                ]
            }

        Both ``platforms`` and ``entities`` can be empty or left out.
        Background ``images`` currently not implemented.
        """
        # load map from file
        self._map_params: MapDict = MapDict.model_validate_json(
            open(path, "r").read()
        )

        # update entry variable
        self._name_var.set(self._map_params.name)

        # create entities
        # for platform in params["platforms"]:
        #     ic("created", platform)
        #     self._islands.append(Island(
        #         platform["pos"],
        #         platform["size"],
        #         platform["texture"]
        #     ))

        # for entity in params["entities"]:
        #     ic("new entity", entity)

    def create_map(self) -> None:
        """
        create a new map
        """
        self._map_params = MapDict(
            name="temp_world",
            background=(0, 0, 0, 255),
            spawn_pos=(100, 100),
            platforms=[],
            entities=[]
        )

        # update entry variable
        self._name_var.set(self._map_params.name)

    def save_map(self, path: str) -> None:
        """
        save the currently created map
        """
        with open(path, "w") as out:
            out.write(self._map_params.model_dump_json(indent=4))

    def change_name(self, name: str) -> None:
        """
        change the maps name
        """
        self._map_params.name = name

    def render_to_surface(self, surface: pg.Surface) -> None:
        """
        render the map with all currently applied parameters to a surface
        """
        # check if the background is a color or an image
        if type(self._map_params.background) in (list, tuple):
            surface.fill(self._map_params.background)

        else:
            raise NotImplementedError(
                "background images currently not supported"
            )

        # draw span point
        spawn_position = Vec2().from_cartesian(*self._map_params.spawn_pos)
        spawn_position -= self._map_pos
        spawn_position *= self.scale
        spawn_size = 20 * self.scale

        pg.draw.circle(
            surface,
            (255, 0, 0, 125),
            spawn_position.xy,
            spawn_size
        )

        # draw platforms
        for platform in self._map_params.platforms:
            platform_position = Vec2().from_cartesian(*platform.pos)
            platform_position -= self._map_pos
            platform_position *= self.scale

            platform_size = Vec2().from_cartesian(*platform.size)
            platform_size *= self.scale

            pg.draw.rect(
                surface,
                (255, 255, 255),
                pg.Rect(
                    platform_position.xy,
                    platform_size.xy
                )
            )


def main() -> None:
    # ################## create window ##################
    root = pgi.PgRoot(
        margin=20,
        padding=10,
        title="Amoginarium Map Editor"
    )
    root.theme.set_appearance(root.theme.Appearance.dark)
    # root.show_wireframe = True

    root.grid_columnconfigure(0, 1)
    root.grid_rowconfigure(0, 1)
    root.grid_rowconfigure(1, 8)

    # ################## load map ##################
    world_name_var = StringVar()
    map = MapRenderer(world_name_var)

    # update map name on entry change
    world_name_var.trace_add(
        StringVar.TraceModes.write,
        lambda s, *_: map.change_name(s.update())
    )

    # ################## top menu ##################
    menu_frame = widgets.Frame(root, min_height=100)
    menu_frame.grid(0, 0, sticky="ew", margin=10)

    menu_frame.grid_rowconfigure(0, 1)
    menu_frame.grid_columnconfigure(range(0, 7), 1)
    menu_frame.grid_columnconfigure(3, 2)

    # buttons for top menu
    def open_file():
        path = crossfiledialog.open_file(
            "open map",
            os.getcwd()
        )
        if path == "":
            return

        map.load_map(path)

    def save_file():
        path = crossfiledialog.save_file(
            "save map",
            os.getcwd()
        )
        if path == "":
            return

        map.save_map(path)

    load_btn = widgets.Button(
        menu_frame,
        text="",
        bg=Color.transparent(),
        border_radius=1,
        image=iopen("./assets/icons/open.png"),
        height=80,
        width=80,
        command=lambda: Thread(target=open_file).start()
    )
    load_btn.grid(0, 0, margin=10)

    save_btn = widgets.Button(
        menu_frame,
        text="",
        bg=Color.transparent(),
        border_radius=1,
        image=iopen("./assets/icons/diskette.png"),
        height=80,
        width=80,
        command=lambda: Thread(target=save_file).start()
    )
    save_btn.grid(0, 1, margin=10)

    widgets.Frame(
        menu_frame,
        width=3,
        border_radius=1,
        bg=Color.from_rgb(200, 200, 200),
        height=80
    ).grid(0, 2)

    world_name = widgets.Entry(
        menu_frame,
        height=60,
        placeholder_text="World Name",
        textvariable=world_name_var
    )
    world_name.grid(0, 3, sticky="ew", margin=10)

    widgets.Frame(
        menu_frame,
        width=3,
        border_radius=1,
        bg=Color.from_rgb(200, 200, 200),
        height=80
    ).grid(0, 4)

    new_island_btn = widgets.Button(
        menu_frame,
        text="New Island",
        height=80,
        width=160,
        # command=lambda: Thread(target=save_file).start()
    )
    new_island_btn.grid(0, 5, margin=10)

    new_entity_btn = widgets.Button(
        menu_frame,
        text="New Entity",
        height=80,
        width=160,
        # command=lambda: Thread(target=save_file).start()
    )
    new_entity_btn.grid(0, 6, margin=10)

    # ################## world ##################
    render_width = 1
    render_height = 1
    render_wrapper = widgets.Frame(
        root,
        bg=Color.transparent(),
        border_radius=0
    )
    render_wrapper.grid(1, 0, sticky="nsew", margin=10)
    render_frame = widgets.SurfaceFrame(
        render_wrapper,
    )
    render_frame.grid(0, 0, sticky="nsew", margin=0)

    # callback for SurfaceFrame
    def update_map(surf: pg.Surface):
        nonlocal render_width, render_height
        new_width, new_height = render_wrapper.get_size()

        # update surface size
        if any([
            new_width != render_width,
            new_height != render_height
        ]):
            ic(
                "new size",
                (new_width, new_height),
                (render_width, render_height)
            )
            render_frame._surface = pg.Surface(
                (
                    new_width,
                    new_height
                ),
                pg.SRCALPHA
            )

            render_width = new_width
            render_height = new_height
            render_frame.width = render_width
            render_frame.height = render_height

        # movement
        last_moving = map.mouse_moving
        map.mouse_moving = render_frame.is_active

        now_pos = Vec2().from_cartesian(*root.mouse_pos)
        if last_moving:
            # calculate mouse position delta
            delta = now_pos - map.last_mouse_pos

            # only call function if the mouse has actually moved
            if not delta.length == 0:
                # negative becaouse pygame
                map.move_by(delta * -1)

        map.last_mouse_pos = now_pos

        # zoom
        now_scroll = Vec2().from_cartesian(*root.mouse_scroll)
        if render_frame.is_hover:
            delta = now_scroll - map.last_mouse_scroll

            if not delta.length == 0:
                map.scale_by(delta.y)

        map.last_mouse_scroll = now_scroll

        # draw world
        render_frame._surface.fill((0, 0, 0, 0))
        map.render_to_surface(render_frame._surface)

    render_frame.in_loop(update_map)

    # start loop
    root.mainloop()


if __name__ == "__main__":
    main()
