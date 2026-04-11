"""
amoginarium/ui/_pointer.py

Project: amoginarium
Created: 11.03.2026
Authors: LukasKrah
"""

from .._base import UIEventElement

import pygame as pg

from amoginarium.shared.utility import convert_coord, Vec2
from ...entities import Cursor
from .... import pv


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

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        mouse_pos = pg.mouse.get_pos()
        screen_size_offset = pv.global_vars.get_screen_size_offset()
        screen_size_fac = pv.global_vars.get_screen_size_fac()
        mouse_pos = ((mouse_pos[0] - screen_size_offset.x) * screen_size_fac.x,
                     (mouse_pos[1] - screen_size_offset.y) * screen_size_fac.y)
        new_pos = convert_coord(mouse_pos, Vec2)

        self.__velocity.xy = (new_pos - self.position.absolute_global).xy

        self.absolute_position_global = new_pos

        super()._gl_draw(delta_cal, layer)

    @property
    def velocity(self) -> Vec2:
        """:return: Cursor velocity"""
        return self.__velocity
