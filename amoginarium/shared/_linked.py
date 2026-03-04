"""
_linked.py
20. March 2024

globals

Author:
Nilusink
"""
from amoginarium.debugging import get_caller_name, print_ic_style, CC
from amoginarium.logic import Vec2
from enum import Enum
import typing as tp

# idk how to do this with the pythin 3.12 typehinting
_A = tp.TypeVar("_A", int, float, Vec2)


class Coalitions(Enum):
    neutral = 0
    blue = 1
    red = 2


class BoundFunction(tp.TypedDict):
    func: tp.Callable
    args: tuple
    kwargs: dict


class _GlobalVars:
    _instance: tp.Self = ...

    ic_debugger = ...
    screen_size: Vec2 = ...
    screen_size_real: Vec2 = ...
    _world_position: Vec2 = ...
    pixel_per_meter: Vec2 = ...
    in_next_loop: list[BoundFunction] = []
    _in_loop: dict[int, BoundFunction] = {}

    time: float = 0

    max_fps: int = 60
    show_targets: bool = True
    background_position = 0

    def __new__(cls, *args, **kwargs) -> tp.Self:
        # only one instance may be created
        if cls._instance is not ...:
            print_ic_style(
                f"{CC.fg.MAGENTA}{get_caller_name()}{CC.ctrl.ENDC} "
                "tried to re-instance GloablVars"
            )
            return cls._instance

        cls._instance = super(_GlobalVars, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._world_position = Vec2()

    @property
    def world_position(self) -> Vec2:
        # apply y offset (scaling should occur at bottom-left)
        pos = self._world_position
        offset_x = self.screen_size.y - self.screen_size.y
        offset_x *= self.pixel_per_meter

        return pos - offset_x

    @world_position.setter
    def world_position(self, value: Vec2) -> None:
        self._world_position = value

    def set_in_loop[**A, R](
            self,
            func: tp.Callable[A, R],
            *args: A.args,
            **kwargs: A.kwargs
    ) -> int:
        """
        schedule a function to be executed in the games main loop
        """
        if len(self._in_loop) > 0:
            new_key = max(self._in_loop.keys()) + 1

        else:
            new_key = 0

        self._in_loop[new_key] = {
            "func": func,
            "args": args,
            "kwargs": kwargs
        }

        return new_key

    def reset_in_loop(self, key: int) -> None:
        """
        remove hook from being run in the games main loop
        """
        self._in_loop.pop(key)

    def get_in_loop(self) -> list[BoundFunction]:
        """
        get all functions to be run in the main loop
        (should only be called by BaseGame)
        """
        return list(self._in_loop.values())

    def translate_scale(self, value: _A) -> _A:
        """
        translate an absolute value to a screen-size relative value
        """
        if self.pixel_per_meter is ...:
            raise RuntimeError("pixel per meter hasn't been set yet")

        return value * self.pixel_per_meter

    def translate_screen_coord[A: float | int | Vec2](self, coord: A) -> A:
        """
        translate an absolute coordinate to a screen-relative coordinate
        """
        scaled_coord = self.translate_scale(coord)

        return scaled_coord - self.world_position

    def reset(self):
        """
        reset all variables to their original state
        """
        self._world_position *= 0


global_vars = _GlobalVars()
