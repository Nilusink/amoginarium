"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable

from ..logic import convert_coord, Vec2
from ..ui import Button, UIEntity


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

        Button(
            (0.5, 0.35),
            (0.2, 0.12),
            "New game",
            parent=self,
            command=start_game_callback
        )

        Button(
            (0.5, 0.5),
            (0.2, 0.12),
            "Settings",
            parent=self,
            command=open_settings_callback,
        )

        Button(
            (0.5, 0.65),
            (0.2, 0.12),
            "Exit",
            parent=self,
            command=exit_callback,
        )

    def toggle_use_collision_mask(self, *_):
        self.but.relative_size = convert_coord((0.5, 0.5), Vec2)
        self.but.absolute_size = convert_coord((200, 100), Vec2)

        self.call += 1
