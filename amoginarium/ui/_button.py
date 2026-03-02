"""
amoginarium/ui/_button.py

Project: amoginarium
Created: 26. March 2024
"""

from __future__ import annotations

from typing import Any, Callable
# noinspection PyPackageRequirements
import pygame as pg

from ..audio import PresetEffect, SoundEffect
from ..render_bindings import renderer
from ..logic import coord_t, Color
from ._types import anchor_t

from ._rectangle import Rectangle


class _OnHoverButtonSound(PresetEffect):
    volume = 1
    _sound_name = "button_hover"


class _OnLeaveButtonSound(PresetEffect):
    volume = 1
    _sound_name = "button_leave"


class _ButtonClickSound(PresetEffect):
    volume = 1
    _sound_name = "button_click"


class Button(Rectangle):
    """
    a button, what did you expect?
    """
    __command: Callable[[], None] | None
    __text: str

    __fg_color: Color
    __hover_fg_color: Color

    __last_mouse: bool

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            text: str,
            *_args: Any,
            command: Callable[[], None] | None = None,
            anchor: anchor_t = "center",
            absolute: bool = False,
            scaling: bool = True,

            fg_color: Color = Color.from_255(0, 0, 0),
            hover_fg_color: Color = Color.from_255(0, 0, 0),

            bg_color: Color = Color.from_255(56, 254, 255),
            border_color: Color = Color.from_255(33, 133, 163),
            border_width: int = 5,
            radius: float | None = 20,

            hover_bg_color: Color = Color.from_255(140, 255, 255),
            hover_border_color: Color = Color.from_255(255, 255, 255),
            hover_border_width: int = 10,
            hover_radius: float | None = None,
            hover_extend: coord_t | int = 5,

            on_hover_sound: SoundEffect | None = _OnHoverButtonSound(),
            on_leave_sound: SoundEffect | None = _OnLeaveButtonSound(),
            on_click_sound: SoundEffect | None = _ButtonClickSound(),
    ) -> None:
        super().__init__(position, size, anchor=anchor, absolute=absolute, scaling=scaling, bg_color=bg_color,
                         border_color=border_color, border_width=border_width, radius=radius,
                         hover_bg_color=hover_bg_color, hover_border_color=hover_border_color,
                         hover_border_width=hover_border_width, hover_radius=hover_radius, hover_extend=hover_extend,
                         on_hover_sound=on_hover_sound, on_leave_sound=on_leave_sound, on_click_sound=on_click_sound)
        self.__command = command
        self.__text = text
        self.__last_mouse = False

        self.__fg_color = fg_color
        self.__hover_fg_color = hover_fg_color

        self.add_event(pg.MOUSEBUTTONUP, button=pg.BUTTON_LEFT, callback=lambda *_: self.__command())

    def gl_draw(self) -> None:
        super().gl_draw()

        # text
        renderer.draw_text(
            self._top_left + self._abs_size / 2,
            self.__text,
            self.__hover_fg_color if self._hover else self.__fg_color,
            (0, 0, 0, 0),
            # self._hover_color if hover else self._color,
            centered=True
        )
