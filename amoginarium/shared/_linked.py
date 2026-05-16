"""
_linked.py
20. March 2024

globals

Author:
Nilusink
"""

import typing as tp
from ctypes import c_double, c_int8
from enum import Enum
from multiprocessing import Value
from multiprocessing.sharedctypes import Synchronized

from .debugging import cum_timer
from .utility import Vec2

_GLOBAL_VARS_VALUES: dict[str, type] = {
    "screen_size_x": c_double,
    "screen_size_y": c_double,
    "screen_size_real_x": c_double,
    "screen_size_real_y": c_double,
    "screen_size_fac_x": c_double,
    "screen_size_fac_y": c_double,
    "screen_size_offset_x": c_double,
    "screen_size_offset_y": c_double,
    "acceleration_factor": c_double,
    "scaling": c_int8,
    "resolution_x": c_double,
    "resolution_y": c_double,
    "pixel_per_meter": c_double,
    "world_position_x": c_double,
    "world_position_y": c_double,
    "time": c_double,
    "t_mult": c_double,
    "max_fps": c_double,
    "background_position": c_double,
}


def generate_global_vars() -> dict[str, Synchronized]:
    """
    Generate multiprocessing Values for global vars
    """
    out = {}
    for key, value in _GLOBAL_VARS_VALUES.items():
        out[key] = Value(value)

    return out


class Coalitions(Enum):
    neutral = 0
    blue = 1
    red = 2


class BoundFunction(tp.TypedDict):
    func: tp.Callable
    args: tuple
    kwargs: dict


class GlobalVars:
    show_targets: bool = False

    def __init__(self, values: dict[str, Synchronized], set: bool = True) -> None:
        self.__values = values

        self._screen_size = Vec2()
        self._screen_size_real = Vec2()
        self._screen_size_fac = Vec2()
        self._screen_size_offset = Vec2()
        self._resolution = Vec2()
        self._world_position = Vec2()

        self._acceleration_factor = 50
        self._max_fps = 60

        self._background_position = 0
        self._pixel_per_meter = 1
        self._scaling = 0
        self._time = 0
        self._t_mult = 1

        if set:
            self._set_from_current()

        self.__compiled = []

        self.__compile_values()

    def __compile_values(self) -> None:
        for key, item in self.__values.items():
            if key.endswith(("_x", "_y")):
                obj = getattr(self, f"_{key[:-2]}")
                attr = key[-1]

            else:
                obj = self
                attr = f"_{key}"

            self.__compiled.append((item, obj, attr, []))

    def add_callback(self, value: str, callback: tp.Callable[[tp.Any], tp.Any]) -> None:
        """Add a value change callback"""
        for i, v in enumerate(self.__compiled):
            if v[1] == value:
                self.__compiled[i][3].append(callback)

    def _set_from_current(self) -> None:
        self.__values["screen_size_x"].value = self._screen_size.x
        self.__values["screen_size_y"].value = self._screen_size.y
        self.__values["screen_size_real_x"].value = self._screen_size_real.x
        self.__values["screen_size_real_y"].value = self._screen_size_real.y
        self.__values["screen_size_fac_x"].value = self._screen_size_fac.x
        self.__values["screen_size_fac_y"].value = self._screen_size_fac.y
        self.__values["screen_size_offset_x"].value = self._screen_size_offset.x
        self.__values["screen_size_offset_y"].value = self._screen_size_offset.y
        self.__values["acceleration_factor"].value = self._acceleration_factor
        self.__values["scaling"].value = self._scaling
        self.__values["resolution_x"].value = self._resolution.x
        self.__values["resolution_y"].value = self._resolution.y
        self.__values["pixel_per_meter"].value = self._pixel_per_meter
        self.__values["world_position_x"].value = self._world_position.x
        self.__values["world_position_y"].value = self._world_position.y
        self.__values["time"].value = self._time
        self.__values["t_mult"].value = self._t_mult
        self.__values["max_fps"].value = self._max_fps
        self.__values["background_position"].value = self._background_position

    def get_values(self) -> dict[str, Synchronized]:
        return self.__values

    def get_screen_size(self) -> Vec2:
        return self._screen_size.copy()

    def set_screen_size(self, size: Vec2) -> None:
        self._screen_size.x = size.x
        self._screen_size.y = size.y

        self.__values["screen_size_x"].value = size.x
        self.__values["screen_size_y"].value = size.y

    def get_screen_size_real(self) -> Vec2:
        return self._screen_size_real.copy()

    def set_screen_size_real(self, size: Vec2) -> None:
        self._screen_size_real.x = size.x
        self._screen_size_real.y = size.y

        self.__values["screen_size_real_x"].value = size.x
        self.__values["screen_size_real_y"].value = size.y

    def get_screen_size_fac(self) -> Vec2:
        return self._screen_size_fac.copy()

    def set_screen_size_fac(self, size: Vec2) -> None:
        self._screen_size_fac.x = size.x
        self._screen_size_fac.y = size.y

        self.__values["screen_size_fac_x"].value = size.x
        self.__values["screen_size_fac_y"].value = size.y

    def get_screen_size_offset(self) -> Vec2:
        return self._screen_size_offset.copy()

    def set_screen_size_offset(self, offset: Vec2) -> None:
        self._screen_size_offset.x = offset.x
        self._screen_size_offset.y = offset.y

        self.__values["screen_size_offset_x"].value = offset.x
        self.__values["screen_size_offset_y"].value = offset.y

    def get_world_position(self) -> Vec2:
        return self._world_position.copy()

    def set_world_position(self, position: Vec2) -> None:
        self._world_position.x = position.x
        self._world_position.y = position.y

        self.__values["world_position_x"].value = position.x
        self.__values["world_position_y"].value = position.y

    @property
    def resolution_screen(self) -> Vec2:
        return self._resolution / self._pixel_per_meter

    def get_resolution(self) -> Vec2:
        return self._resolution.copy()

    def set_resolution(self, resolution: Vec2) -> None:
        self._resolution.x = resolution.x
        self._resolution.y = resolution.y

        self.__values["resolution_x"].value = resolution.x
        self.__values["resolution_y"].value = resolution.y

    def get_acceleration_factor(self) -> float:
        return self._acceleration_factor

    def set_acceleration_factor(self, factor: float) -> None:
        self._acceleration_factor = factor

        self.__values["acceleration_factor"].value = factor

    def get_scaling(self) -> int:
        return self._scaling

    def set_scaling(self, scaling: int) -> None:
        self._scaling = scaling

        self.__values["scaling"].value = scaling

    def get_time(self) -> float:
        return self._time

    def set_time(self, time: float) -> None:
        self._time = time

        self.__values["time"].value = time

    def get_time_mult(self) -> float:
        return self._t_mult

    def set_time_mult(self, time_mult: float) -> None:
        self._t_mult = time_mult

        self.__values["t_mult"].value = time_mult

    def get_max_fps(self) -> float:
        return self._max_fps

    def set_max_fps(self, max_fps: float) -> None:
        self._max_fps = max_fps

        self.__values["max_fps"].value = max_fps

    def get_background_position(self) -> float:
        return self._background_position

    def set_background_position(self, position: float) -> None:
        self._background_position = position

        self.__values["background_position"].value = position

    def get_pixel_per_meter(self) -> float:
        return self._pixel_per_meter

    def set_pixel_per_meter(self, value: float) -> None:
        self._pixel_per_meter = value

        self.__values["pixel_per_meter"].value = value

    @property
    def screen_pixels(self) -> Vec2:
        return self._screen_size_real / self._pixel_per_meter

    def translate_scale[A: float | int | Vec2](self, value: A) -> A:
        """
        Translate an absolute value to a screen-size relative value
        """
        if self._pixel_per_meter is ...:
            raise RuntimeError("pixel per meter hasn't been set yet")

        return value * self._pixel_per_meter

    def translate_screen_coord[A: float | int | Vec2](self, coord: A) -> A:
        """
        Translate an absolute coordinate to a screen-relative coordinate
        """
        scaled_coord = self.translate_scale(coord)

        return scaled_coord - self._pixel_per_meter

    def reset(self):
        """
        Reset all variables to their original state
        """
        self.set_pixel_per_meter(1)
        self.set_background_position(0)
        self.set_world_position(Vec2())

    @cum_timer.time_this
    def update(self) -> None:
        """
        Update from Values
        """
        for item, obj, attr, callbacks in self.__compiled:
            new = item.value
            old = getattr(obj, attr)

            if new != old:
                setattr(obj, attr, new)

                if callbacks:
                    for cb in callbacks:
                        cb(new)
