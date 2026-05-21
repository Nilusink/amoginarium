"""
Defines a UI widget for rendering and updating dynamic text.

Path: amoginarium/graphics/ui/_widgets/_ui_dynamic_text.py
Project: amoginarium
Created: 12.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.utility import Color, convert_color

from ...render_bindings import renderer
from .._base import UIEventElement
from .._types import Anchor, Positions

if tp.TYPE_CHECKING:
    from amoginarium.shared.utility import color_t, coord_t

    from .._base import UIEntity


class UIDynamicText(UIEventElement):
    """Dynamic text UI widget - text values can be changed after creation."""

    __text_id: renderer.DynamicTextID | None

    __text: str
    __text_color: Color
    __bg_color: Color
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
        text_color: color_t = (0, 0, 0),
        bg_color: color_t = (0, 0, 0, 0),
        font_size: int = 64,
        font_family: str = "Arial",
        bold: bool = False,
        italic: bool = False,
        placement_anchor: Anchor = Anchor.CENTER,
        absolute_values: bool = False,
        positon_is_relative_to_parent: bool = True,
        size_is_relative_to_parent: bool = True,
        parent_reference_position: Positions = Positions.TOP_LEFT,
        collision_buffer: int = 0,
        use_collision_mask: bool = False,
        on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
        on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
        on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
    ) -> None:
        """
        Create a new UIDynamicText
        :param position: Relative position of the component (absolute if absolute_values is set to True)
        :param size: Relative size of the component (absolute if absolute_values is set to True)
        :param parent: Optional parent UI-Entity
        :param text_color: Text color
        :param bg_color: Background color. Alpha doesn't work!
        :param font_size: Font size
        :param font_family: Font family
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param placement_anchor: Placement anchor of the component
        :param absolute_values: Whether the position and size are absolute or relative
        :param positon_is_relative_to_parent: Whether the position is relative to the parent or the screen
        :param size_is_relative_to_parent: Whether the size is relative to the parent or the screen
        :param parent_reference_position: What reference position of the parent component to use
        :param collision_buffer: Buffer for mouse hover in pixels
        :param use_collision_mask: Whether to use a collision mask or just a collision box
        :param on_enter_callbacks: List of callbacks to be called when a cursor enters the component
        :param on_leave_callbacks: List of callbacks to be called when a cursor leaves the component
        :param on_buffer_callbacks: List of callbacks to be called when a cursor buffers the component.
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
        )
        self.__text_id = None
        self.__text = text
        self.__text_color = convert_color(text_color, Color)
        self.__bg_color = convert_color(bg_color, Color)
        self.__font_size = font_size
        self.__font_family = font_family
        self.__bold = bold
        self.__italic = italic

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)

        self.__text_id = renderer.draw_dynamic_text(
            self.center.absolute_global,
            self.__text,
            color=self.__text_color,
            bg_color=self.__bg_color,
            centered=True,
            font_size=self.__font_size,
            font_family=self.__font_family,
            bold=self.__bold,
            italic=self.__italic,
            text_id=self.__text_id,
            convert_global=False,
        )

    # region Properties
    @property
    def text(self) -> str:
        """:return: Current text"""
        return self.__text

    @text.setter
    def text(self, value: str) -> None:
        """:param value: New text"""
        self.__text = value

    @property
    def text_color(self) -> Color:
        """:return: Current text color"""
        return self.__text_color

    @text.setter
    def text_color(self, value: color_t) -> None:
        """:param value: New text color"""
        self.__text_color = convert_color(value, Color)

    @property
    def bg_color(self) -> Color:
        """:return: Current background color"""
        return self.__bg_color

    @bg_color.setter
    def bg_color(self, value: color_t) -> None:
        """:param value: New background color"""
        self.__bg_color = convert_color(value, Color)

    @property
    def font_size(self) -> int:
        """:return: Current font size"""
        return self.__font_size

    @font_size.setter
    def font_size(self, value: int) -> None:
        """:param value: New font size"""
        self.__font_size = value

    @property
    def font_family(self) -> str:
        """:return: Current font family"""
        return self.__font_family

    @font_family.setter
    def font_family(self, value: str) -> None:
        """:param value: New font family"""
        self.__font_family = value

    @property
    def bold(self) -> bool:
        """:return: Current bold state"""
        return self.__bold

    @bold.setter
    def bold(self, value: bool) -> None:
        """:param value: New bold state"""
        self.__bold = value

    @property
    def italic(self) -> bool:
        """:return: Current italic state"""
        return self.__italic

    @italic.setter
    def italic(self, value: bool) -> None:
        """:param value: New italic state"""
        self.__italic = value

    # endregion
