"""
amoginarium/base/_settings.py

Project: amoginarium
"""

from typing import Literal, Callable
# noinspection PyPackageRequirements
import pygame as pg

from ..settings import Settings
from ..ui import Rectangle


##################################################
#                     Code                       #
##################################################

class SettingsMenu(Rectangle):
    __close_settings_callback: Callable[[], None]

    def __init__(
            self,
            close_settings_callback: Callable[[], None],
    ) -> None:
        super().__init__((0.5, 0.5), (0.9, 0.9))

        self.__close_settings_callback = close_settings_callback
        self.add_fullscreen_event(pg.KEYUP, key=pg.K_ESCAPE, callback=lambda *_: self.__close_settings_callback())

    def update(self) -> None:
        super().update()

    def gl_draw(self) -> None:
        super().gl_draw()
