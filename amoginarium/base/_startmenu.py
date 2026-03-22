"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable

from ..logic import convert_coord, Vec2
from ..ui import Button, UIEntity, Rectangle


##################################################
#                     Code                       #
##################################################

class StartMenu(UIEntity):
    call = 0

    def __init__(
            self,
            start_game_callback: Callable[[], None],
            open_settings_callback: Callable[[], None],
            exit_callback: Callable[[], None],
    ) -> None:
        super().__init__()

        rect = Rectangle(
            (0.5, 0.5),
            (0.5, 0.5),
            parent=self,
        )

        Button(
            (0.5, 0.35),
            (0.2, 0.12),
            "New game",
            parent=rect,
            command=start_game_callback
        )

        self.but = Button(
            (0.5, 0.5),
            (0.2, 0.12),
            "Settings",
            parent=rect,
            command=self.toggle_use_collision_mask,
        )

        Button(
            (0.5, 0.65),
            (0.2, 0.12),
            "Exit",
            parent=rect,
            command=exit_callback,
        )

    def toggle_use_collision_mask(self, *_):
        self.but.width = 100

        self.call += 1
