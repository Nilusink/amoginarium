"""
amoginarium/ui/_pointer.py

Project: amoginarium
Created: 11.03.2026
Authors: LukasKrah
"""

from .._base import UIEventElement

import pygame as pg

from amoginarium.logic import convert_coord, Vec2
from amoginarium.entities import Cursor
from amoginarium.shared import global_vars


##################################################
#                     Code                       #
##################################################

class UICursor(UIEventElement):
    __velocity: Vec2

    def __init__(self) -> None:
        super().__init__((0, 0), (0, 0), use_collision_mask=False)

        self.cursor = True
        self.__velocity = Vec2()
        self.add(Cursor)
        self.show()

    def _gl_draw(self) -> None:
        mouse_pos = pg.mouse.get_pos()
        mouse_pos = ((mouse_pos[0] - global_vars.screen_size_offset_x) * global_vars.screen_size_fac_x,
                     (mouse_pos[1] - global_vars.screen_size_offset_y) * global_vars.screen_size_fac_y)
        new_pos = convert_coord(mouse_pos, Vec2)

        self.__velocity.xy = (new_pos - self.absolute_position_global).xy

        self.absolute_position_global = new_pos

        super()._gl_draw()

    @property
    def velocity(self) -> Vec2:
        """:return: Cursor velocity"""
        return self.__velocity
