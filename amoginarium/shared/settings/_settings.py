"""
Manages persistent game configuration via JSON file I/O (not used).

| ``Path``: amoginarium/shared/settings/_settings.py
| ``Project``: amoginarium
| ``Created``: 01.03.2026
| ``Authors``: LukasKrah
"""

from __future__ import annotations

import typing as tp
from json import dump, load

from icecream import ic

##################################################
#                     Code                       #
##################################################


_DEFAULT_SETTINGS: dict[str, tp.Any] = {
    "vsync": False,
    "fps": 60,
    "master_volume": 1.0,
    "gun_volume": 1.0,
    "music_volume": 1.0,
    "scaling": 0,
    "debug_vars": 0,
}


class _Settings:
    __file: str
    __data: dict

    vsync: bool
    fps: int | None

    master_volume: float
    gun_volume: float
    music_volume: float
    scaling: tp.Literal["bars", "fixed_aspect_ratio", "stretching"]
    debug_vars: int

    def __init__(self, file: str = "settings.json") -> None:
        self.__file = file
        self.read()

    def read(self) -> None:
        try:
            with open(self.__file, "r", encoding="utf-8") as file:
                self.__data = load(file)

        except FileNotFoundError:
            self.__data = _DEFAULT_SETTINGS.copy()

            # create settings file for future reference
            self.write()

    def write(self) -> None:
        with open(self.__file, "w", encoding="utf-8") as file:
            dump(self.__data, file, indent=4)

    def get_value(self, value: str) -> tp.Any:
        """Get settings value."""
        # add value if not in settings but in default settings
        # (old version compatability)
        if value not in self.__data and value in _DEFAULT_SETTINGS:
            self.__data[value] = _DEFAULT_SETTINGS.copy()[value]

        return self.__data[value]

    def set_value(self, value: str, new_value: tp.Any) -> None:
        """Set settings value."""
        self.__data[value] = new_value

    def __getattr__(self, item: str) -> tp.Any:
        # prefer values in __data
        if item in _DEFAULT_SETTINGS:
            return self.get_value(item)

        return super().__getattribute__(item)

    def __setattr__(self, item: str, value: tp.Any) -> None:
        # prefer values in __data
        if item in _DEFAULT_SETTINGS:
            self.set_value(item, value)
            return

        super().__setattr__(item, value)


Settings = _Settings()
