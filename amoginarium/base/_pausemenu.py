"""
amoginarium/base/_pausemenu.py

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

class PauseMenu(BaseFrame):
    __widgets: list[Button]

    def __init__(
            self,
            continue_callback: Callable[[], None],
            restart_callback: Callable[[], None],
            open_settings_callback: Callable[[], None],
            end_game_callback: Callable[[], None],
    ) -> None:
        self.__widgets = [
            Button(
                (0.5, 0.26),
                (0.2, 0.12),
                "Continue",
                continue_callback,
                20,
                "center"
            ),
            Button(
                (0.5, 0.42),
                (0.2, 0.12),
                "Restart",
                restart_callback,
                20,
                "center"
            ),
            Button(
                (0.5, 0.58),
                (0.2, 0.12),
                "Settings",
                open_settings_callback,
                20,
                "center"
            ),
            Button(
                (0.5, 0.74),
                (0.2, 0.12),
                "End game",
                end_game_callback,
                20,
                "center"
            )
        ]

    def gl_draw(self) -> None:
        for widget in self.__widgets:
            widget.gl_draw()
