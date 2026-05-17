"""
amoginarium/base/_pausemenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable

from amoginarium.graphics.ui import UIButton, UIEntity, UIRectangle

##################################################
#                     Code                       #
##################################################


class PauseMenu(UIEntity):
    def __init__(
        self,
        continue_callback: Callable[[], None],
        restart_callback: Callable[[], None],
        open_settings_callback: Callable[[], None],
        end_game_callback: Callable[[], None],
    ) -> None:
        super().__init__()
        current_parent = UIRectangle(
            (0.5, 0.5),
            (0.2, 0.5),
            parent=self,
            bg_color=(70, 70, 70, 150),
            border_width=0,
        )

        padding = 0.06
        but_width = 1 - padding * 2
        but_height = (1 - padding * 5) / 4
        step = padding + but_height

        UIButton(
            (0.5, padding + but_height / 2),
            (but_width, but_height),
            "Continue",
            parent=current_parent,
            command=continue_callback,
        )

        UIButton(
            (0.5, padding + but_height / 2 + step),
            (but_width, but_height),
            "Restart",
            parent=current_parent,
            command=restart_callback,
        )

        UIButton(
            (0.5, padding + but_height / 2 + step * 2),
            (but_width, but_height),
            "Settings",
            parent=current_parent,
            command=open_settings_callback,
        )

        UIButton(
            (0.5, 1 - (padding + but_height / 2)),
            (but_width, but_height),
            "End game",
            parent=current_parent,
            command=end_game_callback,
        )
