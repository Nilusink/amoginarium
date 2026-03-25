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
from ..ui._types import Anchor


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

        num_rects = 5
        current_parent = self

        for i in range(num_rects):
            # Interpolate color: i=0 is 255 (White), i=99 is 0 (Black)
            color_val = int(255 * (1 - i / (num_rects - 1)))

            rect = UIElement(
                (0.5, 0.5),      # Positioned in the center of the parent
                (0.999, 0.999),    # 95% the size of the parent
                # bg_color=(color_val, color_val, color_val),
                parent=current_parent,
                # use_collision_mask=False,
                # radius=0
            )

            # Set the newly created rectangle as the parent for the next iteration
            current_parent = rect

        Button(
            (0.5, 0.35),
            (0.2, 0.12),
            "New game",
            parent=current_parent,
            command=start_game_callback
        )

        self.but = Button(
            (0.5, 0.5),
            (0.2, 0.12),
            "Settings",
            parent=current_parent,
            command=self.toggle_use_collision_mask,
        )

        Button(
            (0.5, 0.65),
            (0.2, 0.12),
            "Exit",
            parent=current_parent,
            command=exit_callback,
        )

    def toggle_use_collision_mask(self, *_):
        self.but.width.absolute = 100

        self.call += 1
