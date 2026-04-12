"""
amoginarium/base/_settings.py

Project: amoginarium
"""

from typing import Literal, Callable

from .. import pv
from ..graphics.ui import UIRectangle, UIButton, UIEntity


##################################################
#                     Code                       #
##################################################

class SettingsMenu(UIEntity):
    __close_settings_callback: Callable[[], None]

    def __init__(
            self,
            close_settings_callback: Callable[[], None],
            update_window_callback: Callable[[], None],
    ) -> None:
        super().__init__()

        self.__update_window_callback = update_window_callback
        self.__close_settings_callback = close_settings_callback

        current_parent = UIRectangle((0.5, 0.5), (0.2, 0.5), parent=self, bg_color=(70, 70, 70, 150), border_width=0)

        padding = 0.06
        but_width = 1 - padding * 2
        but_height = (1 - padding * 5) / 4
        step = padding + but_height

        UIButton(
            (0.5, padding + but_height / 2),
            (but_width, but_height),
            "Bars",
            parent=current_parent,
            command=lambda: self.__set_scaling("bars"),
        )

        UIButton(
            (0.5, padding + but_height / 2 + step),
            (but_width, but_height),
            "Fixed ratio",
            parent=current_parent,
            command=lambda: self.__set_scaling("fixed_aspect_ratio"),
        )

        UIButton(
            (0.5, padding + but_height / 2 + step * 2),
            (but_width, but_height),
            "Stretching",
            parent=current_parent,
            command=lambda: self.__set_scaling("stretching"),
        )

        UIButton(
            (0.5, 1 - (padding + but_height / 2)),
            (but_width, but_height),
            "Back",
            parent=current_parent,
            command=self.__close_settings_callback,
        )

    def __set_scaling(self, value: Literal["bars", "fixed_aspect_ratio", "stretching"]) -> None:
        pv.global_vars.scaling = value
        self.__update_window_callback()
