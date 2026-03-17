"""
amoginarium/ui/_rectangle.py

Project: amoginarium
Created: 01.03.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.render_bindings import renderer
from amoginarium.logic import coord_t, Vec2
from amoginarium.shared import global_vars
from amoginarium.audio import SoundEffect

from .._animations import FloatAnimation, Vec2Animation, anim_vec2_values_t, create_float_animation, \
    anim_float_values_t, anim_color_values_t, ColorAnimation
from .._surface_renderer import PygameSurfaceRenderer
from .._base import UIElement, UIEntity
from .._types import Anchor


class Rectangle(UIElement):
    """UI rectangle with basic sounds and animations"""
    __bg_color_animation: ColorAnimation
    __border_color_animation: ColorAnimation
    __border_width_animation: FloatAnimation
    __radius_animation: FloatAnimation
    __extend_animation: Vec2Animation

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

            bg_color: anim_color_values_t = (70, 70, 70),
            border_color: anim_color_values_t = (70, 70, 70),
            border_width: anim_float_values_t = 5,
            radius: anim_float_values_t = 20,
            size_extend: anim_vec2_values_t = 0,

            on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_enter_sound: SoundEffect | None = None,
            on_leave_sound: SoundEffect | None = None,
            on_click_sound: SoundEffect | None = None,

            _use_collision_mask: bool = True
    ) -> None:
        """
        Create a new UI rectangle
        :param relative_position: Relative position of the component
        :param relative_size: Relative size of the component
        :param parent: Optional parent UI-Entity
        :param placement_anchor: Placement anchor of the component
        :param collision_buffer: Mouse hovering buffer for edge cases
        :param bg_color: Background color of the rectangle (hover animated)
        :param border_color: Border color of the rectangle (hover animated)
        :param border_width: Width of the border (hover animated)
        :param radius: Radius of the rectangle (hover animated)
        :param size_extend: Hover animated size expansion
        :param on_enter_callbacks: Callbacks to be called when a cursor enters the component
        :param on_leave_callbacks: Callbacks to be called when a cursor leaves the component
        :param on_buffer_callbacks: Callbacks to be called when a cursor is right on the edge of the component
        :param on_enter_sound: Sound to play when the cursor enters the rectangle
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

        self.__bg_color_animation = ColorAnimation(bg_color)
        self.__border_color_animation = ColorAnimation(border_color)
        self.__border_width_animation = create_float_animation(border_width)
        self.__radius_animation = create_float_animation(radius)
        self.__extend_animation = Vec2Animation(size_extend)

        self.__on_hover_sound = on_enter_sound
        self.__on_leave_sound = on_leave_sound
        self.__on_click_sound = on_click_sound

        self.add_enter_callback(self.__on_cursor_enter)
        self.add_buffer_callback(self.__on_cursor_in_buffer)
        self.add_leave_callback(self.__on_cursor_leave)
        self.add_click_callback(lambda *_: self.__on_click_sound.play() if self.__on_click_sound is not None else None)

    def __on_cursor_enter(self) -> None:
        """Called when a cursor enters the rectangle"""
        if self.__on_hover_sound is not None:
            self.__on_hover_sound.play()
        self.__extend_animation.extend()
        self.__bg_color_animation.extend()
        self.__border_color_animation.extend()
        self.__border_width_animation.extend()
        self.__radius_animation.extend()

    def __on_cursor_leave(self) -> None:
        """Called when a cursor leaves the rectangle"""
        if self.__on_leave_sound is not None:
            self.__on_leave_sound.play()
        self.__extend_animation.contract()
        self.__bg_color_animation.contract()
        self.__border_color_animation.contract()
        self.__border_width_animation.collapse()
        self.__radius_animation.collapse()

    def __on_cursor_in_buffer(self) -> None:
        """Called when a cursor is right on the edge of the rectangle"""
        self.__extend_animation.stop()
        self.__bg_color_animation.stop()
        self.__border_color_animation.stop()
        self.__border_width_animation.stop()
        self.__radius_animation.stop()

    @property
    def absolute_size(self) -> Vec2:
        return super().absolute_size + self.__extend_animation.current_value * 2

    def _gl_draw(self) -> None:
        if self.use_collision_mask and not self._ui_changed:
            self._ui_changed = any([
                self.__border_width_animation.is_changing(),
                self.__border_color_animation.is_changing(),
                self.__bg_color_animation.is_changing(),
                self.__radius_animation.is_changing(),
                self.__extend_animation.is_changing(),
            ])

        delta_cal = global_vars.delta

        border_width = self.__border_width_animation.update(delta_cal)
        border_color = self.__border_color_animation.update(delta_cal)
        bg_color = self.__bg_color_animation.update(delta_cal)
        radius = self.__radius_animation.update(delta_cal)
        self.__extend_animation.update(delta_cal)

        super()._gl_draw()

        if radius > 0:
            if border_width > 0:
                renderer.draw_rounded_rect(
                    self.top_left,
                    self.absolute_size,
                    border_color,
                    radius,
                    convert_global=False
                )

            inner_radius = radius - border_width
            renderer.draw_rounded_rect(
                self.top_left + border_width,
                self.absolute_size - 2 * border_width,
                bg_color,
                inner_radius if inner_radius > 0 else 0,
                convert_global=False
            )

        else:
            if border_width > 0:
                renderer.draw_rect(
                    self.top_left,
                    self.absolute_size,
                    border_color,
                    convert_global=False
                )

            renderer.draw_rect(
                self.top_left + border_width,
                self.absolute_size - 2 * border_width,
                bg_color,
                convert_global=False
            )

        if self._ui_changed and self.use_collision_mask:
            PygameSurfaceRenderer.draw_rect(
                self._collision_surface,
                (0, 0),
                self.absolute_size,
                border_radius=radius
            )

    def hide(self) -> None:
        super().hide()
        self.__extend_animation.reset()
        self.__bg_color_animation.reset()
        self.__border_color_animation.reset()
        self.__border_width_animation.reset()
        self.__radius_animation.reset()
