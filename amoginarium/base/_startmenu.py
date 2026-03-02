"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable
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
        super().__init__()
        self.__widgets = [
            Button(
                (0.5, 0.35),
                (0.2, 0.12),
                "New game",
                command=start_game_callback
            ),
            Button(
                (0.5, 0.5),
                (0.2, 0.12),
                "Settings",
                command=open_settings_callback,
            ),
            Button(
                (0.5, 0.65),
                (0.2, 0.12),
                "Exit",
                command=exit_callback,
            )
        ]

    def update(self) -> None:
        super().update()
        for widget in self.__widgets:
            widget.update()

    def gl_draw(self) -> None:
        super().gl_draw()
        for widget in self.__widgets:
            widget.gl_draw()
