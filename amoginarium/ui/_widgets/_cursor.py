"""
amoginarium/ui/_pointer.py

Project: amoginarium
Created: 11.03.2026
Authors: LukasKrah
"""

from amoginarium.ui._base._ui_element import UIElement

import pygame as pg

from amoginarium.logic import convert_coord, Vec2
from amoginarium.entities import Cursor
from amoginarium.shared import global_vars


##################################################
#                     Code                       #
##################################################

class UICursor(UIElement):
    def __init__(self) -> None:
        super().__init__((0, 0), (0, 0), _use_collision_mask=False)

        self.add(Cursor)

    def _gl_draw(self) -> None:
        mouse_pos = pg.mouse.get_pos()
        mouse_pos = ((mouse_pos[0] - global_vars.screen_size_offset_x) * global_vars.screen_size_fac_x,
                     (mouse_pos[1] - global_vars.screen_size_offset_y) * global_vars.screen_size_fac_y)
        self._absolute_position = convert_coord(mouse_pos, Vec2)

        super()._gl_draw()
