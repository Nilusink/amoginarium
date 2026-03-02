"""
amoginarium/ui/_rectangle.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from __future__ import annotations

from typing import Any, Callable
# noinspection PyPackageRequirements
import pygame as pg

from ..audio import SoundEffect
from ..logic import coord_t, Color, convert_coord, Vec2
from ..render_bindings import renderer

from ._base_widget import BaseWidget
from ._types import anchor_t


##################################################
#                     Code                       #
##################################################

class Rectangle(BaseWidget):
    __bg_color: Color
    __border_color: Color
    __border_width: int
    __radius: float | None

    __hover_bg_color: Color
    __hover_border_color: Color
    __hover_border_width: int
    __hover_radius: float | None
    __hover_extend: Vec2

    __on_hover_sound: SoundEffect | None
    __on_leave_sound: SoundEffect | None
    __on_click_sound: SoundEffect | None

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            *_args: Any,
            anchor: anchor_t = "center",
            absolute: bool = False,
            scaling: bool = True,

            bg_color: Color = Color.from_255(70, 70, 70),
            border_color: Color = Color.from_255(40, 40, 40),
            border_width: int = 5,
            radius: float | None = None,

            hover_bg_color: Color = Color.from_255(90, 90, 90),
            hover_border_color: Color = Color.from_255(40, 40, 40),
            hover_border_width: int = 5,
            hover_radius: float | None = None,
            hover_extend: coord_t | int = 0,

            on_hover_sound: SoundEffect | None = None,
            on_leave_sound: SoundEffect | None = None,
            on_click_sound: SoundEffect | None = None,
    ) -> None:
        super().__init__(position, size, anchor=anchor, absolute=absolute, scaling=scaling)

        self.__bg_color = bg_color
        self.__border_color = border_color
        self.__border_width = border_width
        self.__radius = radius

        self.__hover_bg_color = hover_bg_color
        self.__hover_border_color = hover_border_color
        self.__hover_border_width = hover_border_width
        self.__hover_radius = hover_radius
        if isinstance(hover_extend, int):
            hover_extend = (hover_extend, hover_extend)
        self.__hover_extend = convert_coord(hover_extend, Vec2)

        self.add_event("mouse-enter", sound=on_hover_sound)
        self.add_event("mouse-leave", sound=on_leave_sound)
        self.add_event(pg.MOUSEBUTTONUP, button=pg.BUTTON_LEFT, sound=on_click_sound)

    def gl_draw(self) -> None:
        super().gl_draw()

        border_width: float = self.__hover_border_width if self._hover else self.__border_width
        border_color: Color = self.__hover_border_color if self._hover else self.__border_color
        bg_color: Color = self.__hover_bg_color if self._hover else self.__bg_color
        extend: Vec2 = self.__hover_extend if self._hover else convert_coord((0, 0), Vec2)
        double_extend: Vec2 = convert_coord((extend.x * 2, extend.y * 2), Vec2)

        if self.__radius is not None:
            if self.__border_width > 0:
                renderer.draw_rounded_rect(
                    self._top_left - extend,
                    self._abs_size + double_extend,
                    border_color,
                    self.__radius
                )

            renderer.draw_rounded_rect(
                self._top_left + border_width - extend,
                self._abs_size - 2 * border_width + double_extend,
                bg_color,
                self.__radius - border_width
            )

        else:
            if self.__border_width > 0:
                renderer.draw_rect(
                    self._top_left - extend,
                    self._abs_size + double_extend,
                    border_color,
                )

            renderer.draw_rect(
                self._top_left + border_width - extend,
                self._abs_size - 2 * border_width - double_extend,
                bg_color,
            )
