"""
amoginarium/ui/_widgets/_text.py

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
    __text_id: renderer.TextID

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            text: str,
            *_args: tp.Any,
            parent: UIEntity | None = None,
            placement_anchor: Anchor = Anchor.CENTER,
            absolute_values: bool = False,
            positon_is_relative_to_parent: bool = True,
            size_is_relative_to_parent: bool = True,
            parent_reference_position: Positions = Positions.TOP_LEFT,

            fg_color: color_t = (0, 0, 0),
            bg_color: color_t = (0, 0, 0, 0),
            font_size: int = 64,
            font_family: str = "Arial",
            bold: bool = False,
            italic: bool = False,

            collision_buffer: int = 0,
            use_collision_mask: bool = False,
            on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
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
        )
        self.__text_id = renderer.generate_static_text(
            text,
            fg_color,
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
            convert_global=False
        )