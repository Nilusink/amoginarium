"""
amoginarium/ui/_widgets/_text.py

Project: amoginarium
Created: 03.04.2026
Authors: LukasKrah
"""

import typing as tp

from ....shared.utility import coord_t, color_t

from .._types import Positions, Anchor
from .._base import UIEntity, UIEventElement


class Text(UIEventElement):
    __text: str

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

            fg_color: color_t = (255, 255, 255),

            collision_buffer: int = 1,
            use_collision_mask: bool = True,
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
        self.__text = text

    def _gl_draw(self) -> None:
        ...