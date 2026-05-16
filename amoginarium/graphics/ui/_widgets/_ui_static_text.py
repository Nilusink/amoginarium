"""
amoginarium/graphics/ui/_widgets/_ui_static_text.py

Project: amoginarium
Created: 03.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared.utility import coord_t, color_t

from .._base import UIEntity, UIEventElement
from ...render_bindings import renderer
from .._types import Positions, Anchor


class UIStaticText(UIEventElement):
    """Static text UI widget - text values can't be changed after creation"""

    __text_id: renderer.StaticTextID

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
        :param on_buffer_callbacks: List of callbacks to be called when a cursor buffers the component

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
        self.__text_id = renderer.generate_static_text(
            text,
            text_color,
            bg_color,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
        )

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)

        renderer.draw_static_text(
            self.center.absolute_global,
            self.__text_id,
            centered=True,
            convert_global=False,
        )
