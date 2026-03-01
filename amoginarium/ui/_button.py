"""
_button.py
26. March 2024

a button, what did you expect?

Author:
Nilusink
"""

from __future__ import annotations

import typing as tp
import pygame as pg

from ..logic import coord_t, convert_coord, Color, Vec2
from ..render_bindings import renderer, tColor
from ..shared import global_vars

from ._rectangle import Rectangle


class Button(Rectangle):
    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            text: str,
            command: tp.Callable[[], None] = ...,
            radius: float = ...,
            anchor: tp.Literal["nw", "center"] = "center",
    ) -> None:
        super().__init__(relative_position, relative_size, radius, anchor)

        self._hover_color = Color.from_255(90, 90, 90)
        self._fg_color = Color.from_255(255, 255, 255)
        self._command = command
        self._text = text
        self._last_hover = False
        self._last_mouse = False

    def gl_draw(self) -> None:
        super().gl_draw()

        # text
        renderer.draw_text(
            self._top_left + self._abs_size / 2,
            self._text,
            self._fg_color,
            (0, 0, 0, 0),
            # self._hover_color if hover else self._color,
            centered=True
        )

        # check if mouse down
        mouse_left, *_ = pg.mouse.get_pressed()
        if self._hover and not self._last_mouse and mouse_left:
            self._command()

        self._last_hover = self._hover
        self._last_mouse = mouse_left
