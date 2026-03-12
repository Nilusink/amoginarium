"""
amoginarium/ui/_rectangle.py

Project: amoginarium
"""

##################################################
#                    Imports                     #
##################################################

from __future__ import annotations

from typing import Any, Callable, Tuple
# noinspection PyPackageRequirements
import pygame as pg

from ._entity import UIEntity
from ._animation import Animation, MultiAnimation
from ..audio import SoundEffect
from ..logic import coord_t, Color, convert_coord, Vec2
from ..render_bindings import renderer

from ._component import UIComponent
from ._types import anchor_t, ui_color_t

from .temp_pygame_rendering import draw_rounded_rect
from ..shared import global_vars


##################################################
#                     Code                       #
##################################################

class Rectangle(UIComponent):
    __hover_bg_color_animation: MultiAnimation
    __hover_border_color_animation: MultiAnimation
    __hover_border_width_animation: Animation
    __hover_radius_animation: Animation
    __hover_extend_animation: MultiAnimation

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

            bg_color: ui_color_t = Color.c_255_to_1(70, 70, 70),
            border_color: ui_color_t = Color.c_255_to_1(70, 70, 70),
            border_width: int = 5,
            radius: float = 20,

            hover_bg_color: ui_color_t = Color.c_255_to_1(70, 70, 70),
            hover_bg_color_duration: float = 0,
            hover_bg_color_reverse_duration: float = 0,

            hover_border_color: ui_color_t = Color.c_255_to_1(70, 70, 70),
            hover_border_color_duration: float = 0,
            hover_border_color_reverse_duration: float = 0,

            hover_border_width: int = 5,
            hover_border_width_duration: float = 0,
            hover_border_width_reverse_duration: float = 0,

            hover_radius: float = 20,
            hover_radius_duration: float = 0,
            hover_radius_reverse_duration: float = 0,

            hover_extend: coord_t | float | int = 0,
            hover_extend_duration: coord_t | float | int = 0,
            hover_collapse_duration: coord_t | float | int = 0,

            transparency: float = 0,
            transparency_show_duration: float = 0,
            transparency_hide_duration: float = 0,

            on_hover_sound: SoundEffect | None = None,
            on_leave_sound: SoundEffect | None = None,
            on_click_sound: SoundEffect | None = None,

            parent: UIEntity | None = None
    ) -> None:
        super().__init__(position, size, placement_anchor=anchor, parent=parent)

        self.__on_hover_sound = on_hover_sound
        self.__on_leave_sound = on_leave_sound
        self.__on_click_sound = on_click_sound

        self.__hover_bg_color_animation = MultiAnimation(start=bg_color, end=hover_bg_color, count=3,
                                                         extend_duration=hover_bg_color_duration,
                                                         reduce_duration=hover_bg_color_reverse_duration)
        self.__hover_border_color_animation = MultiAnimation(start=border_color, end=hover_border_color, count=3,
                                                             extend_duration=hover_border_color_duration,
                                                             reduce_duration=hover_border_color_reverse_duration)
        self.__hover_border_width_animation = Animation(start_value=border_width, end_value=hover_border_width,
                                                        extend_duration_seconds=hover_border_width_duration,
                                                        reduce_duration_seconds=hover_border_width_reverse_duration)
        self.__hover_radius_animation = Animation(start_value=radius, end_value=hover_radius,
                                                  extend_duration_seconds=hover_radius_duration,
                                                  reduce_duration_seconds=hover_radius_reverse_duration)
        self.__hover_extend_animation = MultiAnimation(start=0, end=hover_extend, count=2,
                                                       extend_duration=hover_extend_duration,
                                                       reduce_duration=hover_collapse_duration)

        self.add_enter_callback(self.__on_enter)
        self.add_buffer_callback(self.__on_buffer_zone)
        self.add_leave_callback(self.__on_leave)

        # self.add_event(pg.MOUSEBUTTONUP, button=pg.BUTTON_LEFT, sound=self.__on_click_sound)

    def __on_enter(self) -> None:
        self.__hover_extend_animation.extend()
        self.__hover_bg_color_animation.extend()
        self.__hover_border_color_animation.extend()
        self.__hover_border_width_animation.extend()
        self.__hover_radius_animation.extend()

    def __on_leave(self) -> None:
        self.__hover_extend_animation.contract()
        self.__hover_bg_color_animation.contract()
        self.__hover_border_color_animation.contract()
        self.__hover_border_width_animation.contract()
        self.__hover_radius_animation.contract()

    def __on_buffer_zone(self) -> None:
        self.__hover_extend_animation.stop()
        self.__hover_bg_color_animation.stop()
        self.__hover_border_color_animation.stop()
        self.__hover_border_width_animation.stop()
        self.__hover_radius_animation.stop()

    def _gl_draw(self) -> None:
        if self._work_with_collision_mask and not self._ui_changed:
            self._ui_changed = any([
                self.__hover_border_width_animation.is_changing(),
                self.__hover_border_color_animation.is_changing(),
                self.__hover_bg_color_animation.is_changing(),
                self.__hover_radius_animation.is_changing(),
                self.__hover_extend_animation.is_changing(),
            ])

        super()._gl_draw()

        border_width: float = self.__hover_border_width_animation.update(global_vars.delta)
        border_color: ui_color_t = self.__hover_border_color_animation.update(global_vars.delta)
        bg_color: ui_color_t = self.__hover_bg_color_animation.update(global_vars.delta)
        radius: float = self.__hover_radius_animation.update(global_vars.delta)
        extend: Tuple[float, float] = self.__hover_extend_animation.update(global_vars.delta)

        extend_vec = convert_coord(extend, Vec2)
        double_extend_vec = extend_vec * 2

        self._top_left -= extend_vec
        self._bottom_right += double_extend_vec
        self._abs_size += double_extend_vec

        if radius > 0:
            if border_width > 0:
                renderer.draw_rounded_rect(
                    self._top_left,
                    self._abs_size + double_extend_vec,
                    border_color,
                    radius
                )

            inner_radius = radius - border_width
            renderer.draw_rounded_rect(
                self._top_left + border_width,
                self._abs_size - 2 * border_width + double_extend_vec,
                bg_color,
                inner_radius if inner_radius > 0 else 0
            )

            if self._ui_changed:
                draw_rounded_rect(
                    self._collision_surface,
                    (0, 0),
                    self._abs_size + double_extend_vec,
                    border_color,
                    radius
                )

        else:
            if border_width > 0:
                renderer.draw_rect(
                    self._top_left,
                    self._abs_size + double_extend_vec,
                    border_color,
                )

            renderer.draw_rect(
                self._top_left + border_width,
                self._abs_size - 2 * border_width - double_extend_vec,
                bg_color,
            )
