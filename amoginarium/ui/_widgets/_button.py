"""
amoginarium/ui/_button.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

from typing import Any, Callable
# noinspection PyPackageRequirements
import pygame as pg

from amoginarium.audio import PresetEffect, SoundEffect
from amoginarium.logic import coord_t, Color, color_t
from amoginarium.render_bindings import renderer
from .. import anim_vec2_values_t, AnimatedVec2Values
from .._animations import anim_color_values_t, anim_float_values_t, AnimatedColorValues, AnimatedFloatValues, \
    peaked_s_curve

from .._types import Anchor
from .._base import UIEntity

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


OnHoverButtonSound = _OnHoverButtonSound()
OnButtonLeaveSound = _OnButtonLeaveSound()
ButtonClickSound = _ButtonClickSound()

ANIM_TIME: float = .2
ANIM_DEBOUNCE: float = .0


class Button(Rectangle):
    """
    a button, what did you expect?
    """
    __command: Callable[[], None] | None
    __text: str

    __fg_color: Color
    __hover_fg_color: Color

    __last_mouse: bool

    __text_surface: pg.Surface

    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            text: str,
            *_args: Any,
            command: Callable[[], None] | None = None,
            placement_anchor: Anchor = Anchor.CENTER,

            fg_color: color_t = (0, 0, 0),

            bg_color: anim_color_values_t = AnimatedColorValues((56, 254, 255), (140, 255, 255),
                                                                extend_duration=ANIM_TIME,
                                                                extend_debounce_duration=ANIM_DEBOUNCE),
            border_color: anim_color_values_t = AnimatedColorValues((33, 133, 163), (255, 255, 255),
                                                                    extend_duration=ANIM_TIME,
                                                                    extend_debounce_duration=ANIM_DEBOUNCE),
            border_width: anim_float_values_t = AnimatedFloatValues(5, 10,
                                                                    extend_duration=ANIM_TIME,
                                                                    extend_debounce_duration=ANIM_DEBOUNCE),
            radius: anim_float_values_t = AnimatedFloatValues(10, 30,
                                                              extend_duration=ANIM_TIME,
                                                              extend_debounce_duration=ANIM_DEBOUNCE),
            size_extend: anim_vec2_values_t = AnimatedVec2Values(0, (10, 5),
                                                                 extend_duration=ANIM_TIME,
                                                                 extend_curve=peaked_s_curve,
                                                                 collapse_curve=lambda a: a),

            on_enter_sound: SoundEffect | None = OnHoverButtonSound,
            on_leave_sound: SoundEffect | None = OnButtonLeaveSound,
            on_click_sound: SoundEffect | None = ButtonClickSound,

            parent: UIEntity | None = None
    ) -> None:
        super().__init__(relative_position, relative_size, placement_anchor=placement_anchor,
                         on_enter_sound=on_enter_sound, on_leave_sound=on_leave_sound, on_click_sound=on_click_sound,
                         bg_color=bg_color,
                         border_color=border_color,
                         border_width=border_width,
                         radius=radius,
                         size_extend=size_extend,
                         parent=parent
                         )
        self.__command = command
        self.__text = text
        self.__last_mouse = False

        self.__fg_color = Color().from_1(*fg_color)
        self.__hover_fg_color = Color().from_1(*fg_color)

        self.__text_font: pg.font.Font = renderer.get_font(64, "Arial", False, False)
        self.__text_surface = self.__text_font.render(self.__text, True,
                                                      self.__fg_color.rgb255)

        # if self.__command is not None:
        #     self.add_event(pg.MOUSEBUTTONUP, button=pg.BUTTON_LEFT, callback=lambda *_: self.__command())

    def _gl_draw(self) -> None:
        super()._gl_draw()
        # text

        renderer.draw_pg_surf(
            self.top_left + self._absolute_size / 2,
            self.__text_surface,
            centered=True
        )
