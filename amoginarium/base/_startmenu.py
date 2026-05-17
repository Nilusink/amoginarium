"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

import typing as tp
from turtledemo.planet_and_moon import Star

from amoginarium.graphics.logic_dummies import PresetGraphicsSoundEffect
from amoginarium.graphics.ui import UIButton, UIRectangle, UIStaticText

##################################################
#                     Code                       #
##################################################


class _StartGameButtonClick(PresetGraphicsSoundEffect):
    volume = 1
    _sound_name = "button_start_game"


StartGameButtonClick = _StartGameButtonClick()


class StartMenu(UIRectangle):
    def __init__(
        self,
        start_game_callback: tp.Callable[[], None],
        open_settings_callback: tp.Callable[[], None],
        exit_callback: tp.Callable[[], None],
    ) -> None:
        super().__init__(
            (0.5, 0.5), (0.2, 0.5), bg_color=(70, 70, 70, 150), border_width=0
        )

        padding = 0.06
        but_width = 1 - padding * 2
        but_height = (1 - padding * 5) / 4

        UIStaticText(
            (0.5, padding + but_height / 2),
            (but_width, but_height),
            "Welcome",
            parent=self,
            font_size=80,
            text_color=(255, 255, 255),
        )

        UIButton(
            (0.5, padding * 2 + but_height * 1.5),
            (but_width, but_height),
            "New game",
            parent=self,
            command=start_game_callback,
            on_click_sound=StartGameButtonClick,
        )

        self.but = UIButton(
            (0.5, padding * 3 + but_height * 2.5),
            (but_width, but_height),
            "Settings",
            parent=self,
            command=open_settings_callback,
        )

        UIButton(
            (0.5, 1 - (padding + but_height / 2)),
            (but_width, but_height),
            "Exit",
            parent=self,
            command=exit_callback,
        )
