"""
Defines an animated UI button with text and sound effects.

Path: amoginarium/graphics/ui/_widgets/_ui_button.py
Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.utility import convert_color, coord_t, Color, color_t

from ...render_bindings import renderer
from ...sound_effect import PresetGraphicsSoundEffect
from .._animations import (
    anim_color_values_t,
    anim_float_values_t,
    AnimatedColorValues,
    AnimatedFloatValues,
    peaked_s_curve,
    anim_vec2_values_t,
    AnimatedVec2Values,
)
from .._types import Anchor, Positions
from .._base import UIEntity
from ._ui_rectangle import UIRectangle


# region SoundsEffects
class _OnHoverButtonSound(PresetGraphicsSoundEffect):
    volume = 0.5
    _sound_name = "button_hover"


class _ButtonClickSound(PresetGraphicsSoundEffect):
    volume = 1
    _sound_name = "button_click"


class _OnButtonLeaveSound(PresetGraphicsSoundEffect):
    volume = 0.5
    _sound_name = "button_leave"


OnHoverButtonSound = _OnHoverButtonSound()
OnButtonLeaveSound = _OnButtonLeaveSound()
ButtonClickSound = _ButtonClickSound()

# endregion

ANIM_TIME: float = 0.2


class UIButton(UIRectangle):
    """
    a button, what did you expect?
    """

    __command: tp.Callable[[], None] | None

    __text_id: renderer.DynamicTextID | renderer.StaticTextID | None
    __dynamic_text: bool

    __text: str
    __text_color: Color
    __font_size: int
    __font_family: str
    __bold: bool
    __italic: bool

    def __init__(
        self,
        position: coord_t,
        size: coord_t,
        text: str,
        *,
        parent: UIEntity | None = None,
        command: tp.Callable[[], None] | None = None,
        text_color: color_t = (0, 0, 0),
        font_size: int = 64,
        font_family: str = "Arial",
        bold: bool = False,
        italic: bool = False,
        dynamic_text: bool = False,
        bg_color: anim_color_values_t = AnimatedColorValues(
            (56, 254, 255), (140, 255, 255), extend_duration=ANIM_TIME
        ),
        border_color: anim_color_values_t = AnimatedColorValues(
            (33, 133, 163), (255, 255, 255), extend_duration=ANIM_TIME
        ),
        border_width: anim_float_values_t = AnimatedFloatValues(
            5, 10, extend_duration=ANIM_TIME
        ),
        radius: anim_float_values_t = AnimatedFloatValues(
            10, 30, extend_duration=ANIM_TIME
        ),
        size_extend: anim_vec2_values_t = AnimatedVec2Values(
            0,
            10,
            extend_duration=ANIM_TIME,
            extend_curve=peaked_s_curve,
            collapse_curve=lambda a: a,
        ),
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
        on_enter_sound: PresetGraphicsSoundEffect | None = OnHoverButtonSound,
        on_leave_sound: PresetGraphicsSoundEffect | None = OnButtonLeaveSound,
        on_click_sound: PresetGraphicsSoundEffect | None = ButtonClickSound,
    ) -> None:
        """
        a button, what did you expect?
        :param position: Relative position of the component (absolute if absolute_values is set to True)
        :param size: Relative size of the component (absolute if absolute_values is set to True)
        :param parent: Optional parent UI-Entity
        :param command: Callback called when button is pressed
        :param text_color: Text color
        :param font_size: Font size
        :param font_family: Font family
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param dynamic_text: Whether the text-related values need to be changed after creation of the button
        :param bg_color: Background color of the rectangle (hover animated)
        :param border_color: Border color of the rectangle (hover animated)
        :param border_width: Width of the border (hover animated)
        :param radius: Radius of the rectangle (hover animated)
        :param size_extend: Hover animated size expansion
        :param placement_anchor: Placement anchor of the component
        :param absolute_values: Whether the position and size are absolute or relative
        :param positon_is_relative_to_parent: Whether the position is relative to the parent or the screen
        :param size_is_relative_to_parent: Whether the size is relative to the parent or the screen
        :param parent_reference_position: What reference position of the parent component to use
        :param collision_buffer: Mouse hovering buffer for edge cases
        :param use_collision_mask: Whether a collision mask should be used or just a collision box
        :param use_collision_mask: Whether a collision mask should be used or just a collision box
        :param on_enter_callbacks: Callbacks to be called when a cursor enters the component
        :param on_leave_callbacks: Callbacks to be called when a cursor leaves the component
        :param on_enter_sound: Sound to play when the cursor enters the rectangle
        :param on_leave_sound: Sound to play when the cursor leaves the rectangle
        :param on_click_sound: Sound to play when the cursor clicks the rectangle
        """
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
        self.__text_color = convert_color(text_color, Color)
        self.__font_size = font_size
        self.__font_family = font_family
        self.__bold = bold
        self.__italic = italic
        self.__dynamic_text = dynamic_text

        if self.__dynamic_text:
            self.__text_id = None
        else:
            self.__text_id = renderer.generate_static_text(
                self.__text,
                self.__text_color,
                (0, 0, 0, 0),
                font_size=self.__font_size,
                font_family=self.__font_family,
                bold=self.__bold,
                italic=self.__italic,
            )

        if self.__command is not None:
            self.add_click_callback(lambda: self.__command())

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)

        if self.__dynamic_text:
            self.__text_id = renderer.draw_dynamic_text(
                self.center.absolute_global,
                self.__text,
                color=self.__text_color,
                bg_color=(0, 0, 0, 0),
                centered=True,
                font_size=self.__font_size,
                font_family=self.__font_family,
                bold=self.__bold,
                italic=self.__italic,
                text_id=self.__text_id,
                convert_global=False,
            )
        else:
            renderer.draw_static_text(
                self.center.absolute_global,
                self.__text_id,
                centered=True,
                convert_global=False,
            )

    # region Properties
    @property
    def dynamic_text(self) -> bool:
        """:return: If the text is dynamic"""
        return self.__dynamic_text

    @dynamic_text.setter
    def dynamic_text(self, value: bool) -> None:
        """:param value: New value for dynamic_text"""
        self.__dynamic_text = value

        if self.__dynamic_text:
            self.__text_id = None
        else:
            self.__text_id = renderer.generate_static_text(
                self.__text,
                self.__text_color,
                (0, 0, 0, 0),
                font_size=self.__font_size,
                font_family=self.__font_family,
                bold=self.__bold,
                italic=self.__italic,
            )

    @property
    def text(self) -> str:
        """:return: Current text"""
        return self.__text

    @text.setter
    def text(self, value: str) -> None:
        """
        :param value: New text
        :raises NotImplementedError: If dynamic_text is set to false
        """
        if not self.__dynamic_text:
            raise NotImplementedError(
                "Cannot change text. dynamic_text is set to false"
            )
        self.__text = value

    @property
    def text_color(self) -> Color:
        """:return: Current text color"""
        return self.__text_color

    @text_color.setter
    def text_color(self, value: color_t) -> None:
        """
        :param value: New text color
        :raises NotImplementedError: If dynamic_text is set to false
        """
        if not self.__dynamic_text:
            raise NotImplementedError(
                "Cannot change text. dynamic_text is set to false"
            )
        self.__text_color = convert_color(value, Color)

    @property
    def font_size(self) -> int:
        """:return: Current font size"""
        return self.__font_size

    @font_size.setter
    def font_size(self, value: int) -> None:
        """
        :param value: New font size
        :raises NotImplementedError: If dynamic_text is set to false
        """
        if not self.__dynamic_text:
            raise NotImplementedError(
                "Cannot change text. dynamic_text is set to false"
            )
        self.__font_size = value

    @property
    def font_family(self) -> str:
        """:return: Current font family"""
        return self.__font_family

    @font_family.setter
    def font_family(self, value: str) -> None:
        """
        :param value: New font family
        :raises NotImplementedError: If dynamic_text is set to false
        """
        if not self.__dynamic_text:
            raise NotImplementedError(
                "Cannot change text. dynamic_text is set to false"
            )
        self.__font_family = value

    @property
    def bold(self) -> bool:
        """:return: Current bold state"""
        return self.__bold

    @bold.setter
    def bold(self, value: bool) -> None:
        """
        :param value: New bold state
        :raises NotImplementedError: If dynamic_text is set to false
        """
        if not self.__dynamic_text:
            raise NotImplementedError(
                "Cannot change text. dynamic_text is set to false"
            )
        self.__bold = value

    @property
    def italic(self) -> bool:
        """:return: Current italic state"""
        return self.__italic

    @italic.setter
    def italic(self, value: bool) -> None:
        """
        :param value: New italic state
        :raises NotImplementedError: If dynamic_text is set to false
        """
        if not self.__dynamic_text:
            raise NotImplementedError(
                "Cannot change text. dynamic_text is set to false"
            )
        self.__italic = value

    # endregion
