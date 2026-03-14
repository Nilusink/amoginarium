"""
amoginarium/ui/_pointer.py

Project: amoginarium
"""

from ._component import UIComponent

import pygame as pg

from ..logic import convert_coord, Vec2
from ..entities import Cursor
from ..shared import global_vars


##################################################
#                     Code                       #
##################################################

class UICursor(UIComponent):
    def __init__(self) -> None:
        super().__init__((0, 0), (0, 0), _work_with_collision_mask=False)

        self.add(Cursor)

    def _gl_draw(self) -> None:
        mouse_pos = pg.mouse.get_pos()
        mouse_pos = ((mouse_pos[0] - global_vars.screen_size_offset_x) * global_vars.screen_size_fac_x,
                     (mouse_pos[1] - global_vars.screen_size_offset_y) * global_vars.screen_size_fac_y)
        self._abs_position_original = convert_coord(mouse_pos, Vec2)

        super()._gl_draw()
