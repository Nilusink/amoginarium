"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable
from ..ui import Button, UIElement


##################################################
#                     Code                       #
##################################################

class StartMenu(UIElement):
    def __init__(
            self,
            start_game_callback: Callable[[], None],
            open_settings_callback: Callable[[], None],
            exit_callback: Callable[[], None],
    ) -> None:
        super().__init__()
        self._children.append(
            Button(
                (0.5, 0.35),
                (0.2, 0.12),
                "New game",
                command=start_game_callback
            ))
        self._children.append(
            Button(
                (0.5, 0.5),
                (0.2, 0.12),
                "Settings",
                command=open_settings_callback,
            ))
        self._children.append(
            Button(
                (0.5, 0.65),
                (0.2, 0.12),
                "Exit",
                command=exit_callback,
            ))

    def gl_draw(self) -> None:
        """
        Draw function
        """

        for widget in self._children:
            widget.gl_draw()
