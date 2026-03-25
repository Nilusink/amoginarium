"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable

from ..logic import convert_coord, Vec2
from ..ui import Button, UIEntity, Rectangle, UIElement
from ..ui._types import Anchor, Positions


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
        current_parent = Rectangle((0.5, 0.5), (0.2, 0.4), parent=self, bg_color=(70, 70, 70, 150), border_width=0)

        padding = 0.08
        but_width = 1 - padding * 2
        but_height = (1 - padding * 4) / 3

        Button(
            (0.5, padding + but_height / 2),
            (but_width, but_height),
            "New game",
            parent=current_parent,
            command=start_game_callback
        )

        Button(
            (0.5, 0.5),
            (but_width, but_height),
            "Settings",
            parent=current_parent,
            command=open_settings_callback
        )

        Button(
            (0.5, 1 - (padding + but_height / 2)),
            (but_width, but_height),
            "Exit",
            parent=current_parent,
            command=exit_callback,
        )
