"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable

from ..logic import Color
from ..ui import Button, BaseFrame


##################################################
#                     Code                       #
##################################################

class StartMenu(BaseFrame):
    __widgets: list[Button]

    def __init__(
            self,
            start_game_callback: Callable[[], None],
            open_settings_callback: Callable[[], None],
            exit_callback: Callable[[], None],
    ) -> None:
        self.__widgets = [
            Button(
                (0.5, 0.35),
                (0.2, 0.12),
                "New game",
                start_game_callback,
                20,
                "center"
            ),
            Button(
                (0.5, 0.5),
                (0.2, 0.12),
                "Settings",
                open_settings_callback,
                20,
                "center"
            ),
            Button(
                (0.5, 0.65),
                (0.2, 0.12),
                "Exit",
                exit_callback,
                20,
                "center"
            )
        ]

    def gl_draw(self) -> None:
        for widget in self.__widgets:
            widget.gl_draw()
