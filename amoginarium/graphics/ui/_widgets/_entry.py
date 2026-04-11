"""
amoginarium/ui/_widgets/_entry.py

Project: amoginarium
Created: 03.04.2026
Authors: LukasKrah
"""

import typing as tp

from ...logic_dummies import GraphicsSoundEffect
from ....shared.utility import coord_t

from .._animations import anim_color_values_t, anim_float_values_t, anim_vec2_values_t
from .._types import Positions, Anchor
from ._rectangle import Rectangle
from .._base import UIEntity


class UIEntry(Rectangle):
    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            *_args: tp.Any,

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

            bg_color: anim_color_values_t = (56, 254, 255),
            border_color: anim_color_values_t = (33, 133, 163),
            border_width: anim_float_values_t = 5,
            radius: anim_float_values_t = 10,
            size_extend: anim_vec2_values_t = 0,

            on_enter_sound: GraphicsSoundEffect | None = None,
            on_leave_sound: GraphicsSoundEffect | None = None,
            on_click_sound: GraphicsSoundEffect | None = None
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