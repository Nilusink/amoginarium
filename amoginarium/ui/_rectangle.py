"""
amoginarium/ui/_rectangle.py

Project: amoginarium
Created: 01.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from ..logic import coord_t, c_255_to_1, convert_coord, Vec2
from ..render_bindings import renderer
from ..shared import global_vars
from ..audio import SoundEffect

from ._animations import Animation, MultiAnimation, Vec2Animation, anim_vec2_values_t, create_float_animation, \
    anim_float_values_t
from ._types import Anchor, ui_color_t
from ._component import UIComponent
from ._entity import UIEntity

from .temp_pygame_rendering import draw_rounded_rect


class Rectangle(UIComponent):
    """UI rectangle with basic sounds and animations"""
    __hover_bg_color_animation: MultiAnimation[tuple[int, int, int]]
    __hover_border_color_animation: MultiAnimation[tuple[int, int, int]]
    __hover_border_width_animation: Animation
    __hover_radius_animation: Animation
    __hover_extend_animation: Vec2Animation

    __on_hover_sound: SoundEffect | None
    __on_leave_sound: SoundEffect | None
    __on_click_sound: SoundEffect | None

    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            *_args: tp.Any,
            parent: UIEntity | None = None,
            placement_anchor: Anchor = Anchor.CENTER,
            collision_buffer: int = 1,

            on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,

            bg_color: ui_color_t = c_255_to_1(70, 70, 70),
            hover_bg_color: ui_color_t = c_255_to_1(70, 70, 70),
            hover_bg_color_duration: float = 0,
            hover_bg_color_reverse_duration: float = 0,

            border_color: ui_color_t = c_255_to_1(70, 70, 70),
            hover_border_color: ui_color_t = c_255_to_1(70, 70, 70),
            hover_border_color_duration: float = 0,
            hover_border_color_reverse_duration: float = 0,

            border_width: anim_float_values_t = 5,
            radius: anim_float_values_t = 20,

            size_extend: anim_vec2_values_t = 0,

            on_hover_sound: SoundEffect | None = None,
            on_leave_sound: SoundEffect | None = None,
            on_click_sound: SoundEffect | None = None,

            _use_collision_mask: bool = True
    ) -> None:
        """
        Create a new UI rectangle
        :param relative_position: Relative position of the component
        :param relative_size: Relative size of the component
        :param _args: Not used
        :param parent: Optional parent UI-Entity
        :param placement_anchor: Placement anchor of the component
        :param collision_buffer: Mouse hovering buffer for edge cases
        :param on_enter_callbacks: Callbacks to be called when a cursor enters the component
        :param on_leave_callbacks: Callbacks to be called when a cursor leaves the component
        :param on_buffer_callbacks: Callbacks to be called when a cursor is right on the edge of the component
        :param bg_color: Background color of the rectangle
        :param hover_bg_color: Background color of the rectangle when hovering
        :param hover_bg_color_duration: Time it takes to change the background color to hover_bg_color
        :param hover_bg_color_reverse_duration: Time it takes to change the background color back to bg_color
        :param border_color: Border color of the rectangle
        :param hover_border_color: Border color of the rectangle when hovering
        :param hover_border_color_duration: Time it takes to change the border color to hover_border_color
        :param hover_border_color_reverse_duration: Time it takes to change the border color back to border_color
        :param border_width: Width of the border
        :param hover_border_width: Width of the border when hovering
        :param hover_border_width_duration: Time it takes to change the border width to hover_border_width
        :param hover_border_width_reverse_duration: Time it takes to change the border width back to border_width
        :param radius: Radius of the rectangle
        :param hover_radius: Radius of the rectangle when hovering
        :param hover_radius_duration: Time it takes to change the radius to hover_radius
        :param hover_radius_reverse_duration: Time it takes to change the radius back to radius
        :param hover_extend: How much the rectangle should be extended when hovering
        :param hover_extend_duration: Time it takes to extend the rectangle
        :param hover_collapse_duration: Time it takes to collapse the rectangle
        :param on_leave_sound: Sound to play when the cursor leaves the rectangle
        :param on_click_sound: Sound to play when the cursor clicks the rectangle
        :param _use_collision_mask: Whether a collision mask should be used or just a collision box
        """
        super().__init__(
            relative_position=relative_position,
            relative_size=relative_size,
            parent=parent,
            placement_anchor=placement_anchor,
            collision_buffer=collision_buffer,
            on_enter_callbacks=on_enter_callbacks,
            on_leave_callbacks=on_leave_callbacks,
            on_buffer_callbacks=on_buffer_callbacks,
            _use_collision_mask=_use_collision_mask
        )

        self.__on_hover_sound = on_hover_sound
        self.__on_leave_sound = on_leave_sound
        self.__on_click_sound = on_click_sound

        self.__hover_bg_color_animation = MultiAnimation(
            start_values=bg_color, end_values=hover_bg_color, count=3,
            extend_durations_in_seconds=hover_bg_color_duration,
            collapse_duration_in_seconds=hover_bg_color_reverse_duration)
        self.__hover_border_color_animation = MultiAnimation(
            start_values=border_color, end_values=hover_border_color, count=3,
            extend_durations_in_seconds=hover_border_color_duration,
            collapse_duration_in_seconds=hover_border_color_reverse_duration)
        self.__hover_border_width_animation = create_float_animation(border_width)
        self.__hover_radius_animation = create_float_animation(radius)
        self.__hover_extend_animation = Vec2Animation(size_extend)

        self.add_enter_callback(self.__on_enter)
        self.add_buffer_callback(self.__on_buffer_zone)
        self.add_leave_callback(self.__on_leave)

        # self.add_event(pg.MOUSEBUTTONUP, button=pg.BUTTON_LEFT, sound=self.__on_click_sound)

    def __on_enter(self) -> None:
        """Called when the cursor enters the rectangle"""
        if self.__on_hover_sound is not None:
            self.__on_hover_sound.play()
        self.__hover_extend_animation.extend()
        self.__hover_bg_color_animation.extend()
        self.__hover_border_color_animation.extend()
        self.__hover_border_width_animation.extend()
        self.__hover_radius_animation.extend()

    def __on_leave(self) -> None:
        """Called when the cursor leaves the rectangle"""
        if self.__on_leave_sound is not None:
            self.__on_leave_sound.play()
        self.__hover_extend_animation.contract()
        self.__hover_bg_color_animation.contract()
        self.__hover_border_color_animation.contract()
        self.__hover_border_width_animation.collapse()
        self.__hover_radius_animation.collapse()

    def __on_buffer_zone(self) -> None:
        """Called when the cursor is right on the edge of the rectangle"""
        self.__hover_extend_animation.stop()
        self.__hover_bg_color_animation.stop()
        self.__hover_border_color_animation.stop()
        self.__hover_border_width_animation.stop()
        self.__hover_radius_animation.stop()

    @property
    def _absolute_size(self) -> Vec2:
        return super()._absolute_size + self.__hover_extend_animation.current_value * 2

    def _gl_draw(self) -> None:
        if self._use_collision_mask and not self._ui_changed:
            self._ui_changed = any([
                self.__hover_border_width_animation.is_changing(),
                self.__hover_border_color_animation.is_changing(),
                self.__hover_bg_color_animation.is_changing(),
                self.__hover_radius_animation.is_changing(),
                self.__hover_extend_animation.is_changing(),
            ])

        border_width: float = self.__hover_border_width_animation.update(global_vars.delta)
        border_color: ui_color_t = self.__hover_border_color_animation.update(global_vars.delta)
        bg_color: ui_color_t = self.__hover_bg_color_animation.update(global_vars.delta)
        radius: float = self.__hover_radius_animation.update(global_vars.delta)
        self.__hover_extend_animation.update(global_vars.delta)

        super()._gl_draw()

        if radius > 0:
            if border_width > 0:
                renderer.draw_rounded_rect(
                    self.top_left,
                    self.absolute_size,
                    border_color,
                    radius
                )

            inner_radius = radius - border_width
            renderer.draw_rounded_rect(
                self.top_left + border_width,
                self.absolute_size - 2 * border_width,
                bg_color,
                inner_radius if inner_radius > 0 else 0
            )

            if self._ui_changed:
                draw_rounded_rect(
                    self._collision_surface,
                    (0, 0),
                    self.absolute_size,
                    border_color,
                    radius
                )

        else:
            if border_width > 0:
                renderer.draw_rect(
                    self.top_left,
                    self.absolute_size,
                    border_color,
                )

            renderer.draw_rect(
                self.top_left + border_width,
                self.absolute_size - 2 * border_width,
                bg_color,
            )
