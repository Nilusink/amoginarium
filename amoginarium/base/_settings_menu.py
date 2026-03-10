"""
amoginarium/base/_settings.py

Project: amoginarium
"""

from typing import Literal, Callable
# noinspection PyPackageRequirements
import pygame as pg

# from ..settings import Settings
from ..shared import global_vars
from ..ui import Rectangle, Button


##################################################
#                     Code                       #
##################################################

class SettingsMenu(Rectangle):
    __close_settings_callback: Callable[[], None]

    def __init__(
            self,
            close_settings_callback: Callable[[], None],
            update_window_callback: Callable[[], None],
    ) -> None:
        super().__init__((0.1, 0.1), (0.9, 0.9))

        self.__update_window_callback = update_window_callback

        Button(
            (0.5, 0.26),
            (0.2, 0.12),
            "Bars",
            parent=self,
            command=lambda: self.__set_scaling("bars"),
        )
        Button(
            (0.5, 0.42),
            (0.2, 0.12),
            "Fixed ratio",
            parent=self,
            command=lambda: self.__set_scaling("fixed_aspect_ratio"),
        )
        Button(
            (0.5, 0.58),
            (0.2, 0.12),
            "Stretching",
            parent=self,
            command=lambda: self.__set_scaling("stretching"),
        )

        self.__close_settings_callback = close_settings_callback
        # todo: reimplement
        # self.add_fullscreen_event(pg.KEYUP, key=pg.K_ESCAPE, callback=lambda *_: self.__close_settings_callback())

    def __set_scaling(self, value: Literal["bars", "fixed_aspect_ratio", "stretching"]) -> None:
        global_vars.scaling = value
        self.__update_window_callback()
