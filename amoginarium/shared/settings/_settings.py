"""
Manages persistent game configuration via JSON file I/O (not used).

Path: amoginarium/shared/settings/_settings.py
Project: amoginarium
Created: 01.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp
from json import dump, load

##################################################
#                     Code                       #
##################################################


class _Settings:
    __file: str
    __data: dict

    vsync: bool
    fps: int | None

    master_volume: float
    gun_volume: float
    music_volume: float
    scaling: tp.Literal["bars", "fixed_aspect_ratio", "stretching"]

    def __init__(self, file: str = "settings.json") -> None:
        self.__file = file
        self.read()

    def read(self) -> None:
        try:
            with open(self.__file, "r") as file:
                self.__data = load(file)
        except FileNotFoundError:
            self.__data = {
                "vsync": False,
                "fps": 60,
                "master_volume": 1.0,
                "gun_volume": 1.0,
                "music_volume": 1.0,
                "scaling": 0,
            }
            for key, value in self.__data.items():
                self.__setattr__(key, value)

            self.write()

        for key, value in self.__data.items():
            self.__setattr__(key, value)

    def write(self) -> None:
        for key in self.__data:
            self.__data[key] = getattr(self, key)

        with open(self.__file, "w") as file:
            dump(self.__data, file, indent=4)


Settings = _Settings()
