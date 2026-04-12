"""
amoginarium/base/_startmenu.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

import typing as tp
from amoginarium.graphics.ui import Button, Rectangle, UIStaticText


##################################################
#                     Code                       #
##################################################

class StartMenu(Rectangle):
    call = 0

    def __init__(
            self,
            start_game_callback: tp.Callable[[], None],
            open_settings_callback: tp.Callable[[], None],
            exit_callback: tp.Callable[[], None],
    ) -> None:
        super().__init__((0.5, 0.5), (0.2, 0.5), bg_color=(70, 70, 70, 150), border_width=0)

        padding = 0.06
        but_width = 1 - padding * 2
        but_height = (1 - padding * 5) / 4

        # Slot 1: Top
        UIStaticText(
            (0.5, padding + but_height / 2),
            (but_width, but_height),
            "Welcome",
            parent=self,
            font_size=80,
            fg_color=(255, 255, 255),
        )

        # Slot 2: Middle-Top
        Button(
            (0.5, padding * 2 + but_height * 1.5),
            (but_width, but_height),
            "New game",
            parent=self,
            command=start_game_callback
        )

        # Slot 3: Middle-Bottom
        self.count = 0
        self.but = Button(
            (0.5, padding * 3 + but_height * 2.5),
            (but_width, but_height),
            "Settings",
            parent=self,
            command=open_settings_callback
        )

        # Slot 4: Bottom (Uses original bottom math)
        Button(
            (0.5, 1 - (padding + but_height / 2)),
            (but_width, but_height),
            "Exit",
            parent=self,
            command=exit_callback,
        )
