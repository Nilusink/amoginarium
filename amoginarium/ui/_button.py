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
from ._types import anchor_t, ui_color_t

from ._rectangle import Rectangle


class _OnHoverButtonSound(PresetEffect):
    volume = .5
    _sound_name = "button_hover"


class _ButtonClickSound(PresetEffect):
    volume = 1
    _sound_name = "button_click"


class _OnButtonLeaveSound(PresetEffect):
    volume = .5
    _sound_name = "button_leave"


TEST_DURATION = .15


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

            fg_color: ui_color_t = (0, 0, 0),
            hover_fg_color: ui_color_t = (0, 0, 0),

            bg_color: ui_color_t = Color.c_255_to_1(56.0, 254.0, 255.0),
            hover_bg_color: ui_color_t = Color.c_255_to_1(140, 255, 255),
            hover_bg_color_duration: float = TEST_DURATION,
            hover_bg_color_reverse_duration: float = TEST_DURATION,

            border_color: ui_color_t = Color.c_255_to_1(33, 133, 163),
            hover_border_color: ui_color_t = Color.c_255_to_1(255, 255, 255),
            hover_border_color_duration: float = TEST_DURATION,
            hover_border_color_reverse_duration: float = TEST_DURATION,

            border_width: int = 5,
            hover_border_width: int = 10,
            hover_border_width_duration: float = TEST_DURATION,
            hover_border_width_reverse_duration: float = TEST_DURATION,

            radius: float = 20,
            hover_radius: float = 40,
            hover_radius_duration: float = TEST_DURATION,
            hover_radius_reverse_duration: float = TEST_DURATION,

            hover_extend: coord_t | float | int = (10, 5),
            hover_extend_duration: coord_t | float | int = TEST_DURATION,
            hover_collapse_duration: coord_t | float | int = TEST_DURATION,

            on_hover_sound: SoundEffect | None = _OnHoverButtonSound(),
            on_leave_sound: SoundEffect | None = _OnButtonLeaveSound(),
            on_click_sound: SoundEffect | None = _ButtonClickSound(),
    ) -> None:
        super().__init__(position, size, anchor=anchor, absolute=absolute, scaling=scaling,
                         on_hover_sound=on_hover_sound, on_leave_sound=on_leave_sound, on_click_sound=on_click_sound,

                         bg_color=bg_color, hover_bg_color=hover_bg_color,
                         hover_bg_color_duration=hover_bg_color_duration,
                         hover_bg_color_reverse_duration=hover_bg_color_reverse_duration,

                         border_color=border_color, hover_border_color=hover_border_color,
                         hover_border_color_duration=hover_border_color_duration,
                         hover_border_color_reverse_duration=hover_border_color_reverse_duration,

                         border_width=border_width, hover_border_width=hover_border_width,
                         hover_border_width_duration=hover_border_width_duration,
                         hover_border_width_reverse_duration=hover_border_width_reverse_duration,

                         radius=radius, hover_radius=hover_radius,
                         hover_radius_duration=hover_radius_duration,
                         hover_radius_reverse_duration=hover_radius_reverse_duration,

                         hover_extend=hover_extend,
                         hover_extend_duration=hover_extend_duration,
                         hover_collapse_duration=hover_collapse_duration
                         )
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
