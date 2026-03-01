"""
amoginarium/ui/_base_widget.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from __future__ import annotations

from typing import Tuple, Literal

from ..logic import coord_t, convert_coord, Vec2
from ._base_frame import BaseFrame
from ..shared import global_vars


##################################################
#                     Code                       #
##################################################

class BaseWidget(BaseFrame):
    _abs_position: Vec2
    _abs_size: Vec2
    _rel_position: Vec2
    _rel_size: Vec2
    _anchor: Literal["nw", "center"]

    _width: float
    _height: float
    _top_left: Vec2
    _top_right: Vec2
    _bottom_left: Vec2
    _bottom_right: Vec2

    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            anchor: Literal["nw", "center"] = "nw"
    ) -> None:
        self._rel_position = convert_coord(relative_position, Vec2)
        self._rel_size = convert_coord(relative_size, Vec2)
        self._anchor = anchor

    def gl_draw(self) -> None:
        self._abs_position = convert_coord(
            (
                int(self._rel_position.x * global_vars.screen_size.x),
                int(self._rel_position.y * global_vars.screen_size.y)
            ),
            Vec2
        )
        self._abs_size = convert_coord(
            (
                int(self._rel_size.x * global_vars.screen_size.x),
                int(self._rel_size.y * global_vars.screen_size.y)
            ),
            Vec2
        )

        self._width = self._abs_size.x
        self._height = self._abs_size.y

        if self._anchor == "nw":
            self._top_left = self._abs_position
            self._top_right = self._abs_position + convert_coord((self._abs_size.x, 0), Vec2)
            self._bottom_left = self._abs_position + convert_coord((0, self._abs_size.y), Vec2)
            self._bottom_right = self._abs_position + self._abs_size.y
        elif self._anchor == "center":
            self._top_left = self._abs_position - self._abs_size / 2
            self._top_right = self._abs_position + convert_coord((self._abs_size.x / 2, -self._abs_size.y / 2), Vec2)
            self._bottom_left = self._abs_position + convert_coord((-self._abs_size.x / 2, self._abs_size.y / 2), Vec2)
            self._bottom_right = self._abs_position + self._abs_size / 2
