"""
amoginarium/base/_pausemenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable
import pygame as pg

from ..ui import Button, UIEntity


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
        Button(
            (0.5, 0.26),
            (0.2, 0.12),
            "Continue",
            parent=self,
            command=continue_callback,
        )
        Button(
            (0.5, 0.42),
            (0.2, 0.12),
            "Restart",
            parent=self,
            command=restart_callback,
        )
        Button(
            (0.5, 0.58),
            (0.2, 0.12),
            "Settings",
            parent=self,
            command=open_settings_callback,
        )
        Button(
            (0.5, 0.74),
            (0.2, 0.12),
            "End game",
            parent=self,
            command=end_game_callback,
        )
