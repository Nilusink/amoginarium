"""
amoginarium/ui/_rectangle.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from __future__ import annotations

import typing as tp
import pygame as pg

from ..logic import coord_t, convert_coord, Color, Vec2
from ..render_bindings import renderer, tColor
from ..shared import global_vars

from ._base_widget import BaseWidget


##################################################
#                     Code                       #
##################################################

class Rectangle(BaseWidget):
    _hover: bool = False

    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            radius: float = ...,
            anchor: tp.Literal["nw", "center"] = "center",
    ) -> None:
        super().__init__(relative_position, relative_size, anchor=anchor)

        self._radius = radius
        self._color = Color.from_255(70, 70, 70)
        self._hover_color = Color.from_255(90, 90, 90)
        self._border_color = Color.from_255(40, 40, 40)
        self._border_width = 5

    def gl_draw(self) -> None:
        super().gl_draw()

        mouse_pos = pg.mouse.get_pos()
        self._hover = all([
            self._top_left.x <= mouse_pos[0] <= self._bottom_right.x,
            self._top_left.y <= mouse_pos[1] <= self._bottom_right.y
        ])

        # base box
        if self._radius is not ...:
            if self._border_width > 0:
                renderer.draw_rounded_rect(
                    self._top_left,
                    self._abs_size,
                    self._border_color,
                    self._radius
                )

            renderer.draw_rounded_rect(
                self._top_left + self._border_width,
                self._abs_size - 2 * self._border_width,
                self._hover_color if self._hover else self._color,
                self._radius
            )

        else:
            if self._border_width > 0:
                renderer.draw_rect(
                    self._top_left,
                    self._abs_size,
                    self._border_color,
                )

            renderer.draw_rect(
                self._top_left + self._border_width,
                self._abs_size - 2 * self._border_width,
                self._color,
            )
