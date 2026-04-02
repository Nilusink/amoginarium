"""
amoginarium/ui/_button.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp
# noinspection PyPackageRequirements
import pygame as pg

from amoginarium.audio import PresetEffect, SoundEffect
from amoginarium.logic import coord_t, Color, color_t, TupleMath
from amoginarium.render_bindings import renderer

from .._animations import anim_color_values_t, anim_float_values_t, AnimatedColorValues, AnimatedFloatValues, \
    peaked_s_curve, anim_vec2_values_t, AnimatedVec2Values
from .._types import Anchor, Positions
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

from .._debug import draw_debug_bounds

@draw_debug_bounds
class Button(Rectangle):
    """
    a button, what did you expect?
    """
    __command: tp.Callable[[], None] | None
    __text: str

    __fg_color: Color
    __hover_fg_color: Color

    __last_mouse: bool

    __text_surface: pg.Surface

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            text: str,
            *_args: tp.Any,
            command: tp.Callable[[], None] | None = None,

            parent: UIEntity | None = None,
            placement_anchor: Anchor = Anchor.CENTER,
            absolute_values: bool = False,
            positon_is_relative_to_parent: bool = True,
            size_is_relative_to_parent: bool = True,
            parent_reference_position: Positions = Positions.TOP_LEFT,

            collision_buffer: int = 1,
            use_collision_mask: bool = True,
            on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,

            fg_color: color_t = (0, 0, 0),

            bg_color: anim_color_values_t = AnimatedColorValues((56, 254, 255), (140, 255, 255),
                                                                extend_duration=ANIM_TIME),
            border_color: anim_color_values_t = AnimatedColorValues((33, 133, 163), (255, 255, 255),
                                                                    extend_duration=ANIM_TIME),
            border_width: anim_float_values_t = AnimatedFloatValues(5, 10,
                                                                    extend_duration=ANIM_TIME),
            radius: anim_float_values_t = AnimatedFloatValues(10, 30,
                                                              extend_duration=ANIM_TIME),
            size_extend: anim_vec2_values_t = AnimatedVec2Values(0, 10,
                                                                 extend_duration=ANIM_TIME,
                                                                 extend_curve=peaked_s_curve,
                                                                 collapse_curve=lambda a: a),

            on_enter_sound: SoundEffect | None = OnHoverButtonSound,
            on_leave_sound: SoundEffect | None = OnButtonLeaveSound,
            on_click_sound: SoundEffect | None = ButtonClickSound
    ) -> None:
        super().__init__(
            position=position,
            size=size,
            parent=parent,
            placement_anchor=placement_anchor,
            absolute_values=absolute_values,
            positon_is_relative_to_parent=positon_is_relative_to_parent,
            size_is_relative_to_parent=size_is_relative_to_parent,
            parent_reference_position=parent_reference_position,
            collision_buffer=collision_buffer,
            use_collision_mask=use_collision_mask,
            on_enter_callbacks=on_enter_callbacks,
            on_leave_callbacks=on_leave_callbacks,
            on_buffer_callbacks=on_buffer_callbacks,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            radius=radius,
            size_extend=size_extend,
            on_enter_sound=on_enter_sound,
            on_leave_sound=on_leave_sound,
            on_click_sound=on_click_sound,
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
        if self.__command is not None:
            self.add_click_callback(lambda *_: self.__command())

    def _gl_draw(self) -> None:
        super()._gl_draw()

        renderer.draw_pg_surf(
            self.center.absolute_global,
            self.__text_surface,
            centered=True,
            convert_global=False
        )
