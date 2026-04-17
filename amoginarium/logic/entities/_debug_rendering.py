"""
amoginarium/logic/entities/_static_debug_rendering.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from types import EllipsisType
from ctypes import Array, c_int
import typing as tp

from amoginarium.shared.utility import coord_t, Vec2, color_t, convert_coord, convert_color
from amoginarium.shared import DebugRendering, GraphicsCIDs, base_entity_t, Coalitions
from amoginarium.shared import BaseCommandType, ProcessCommand, CIDType
from amoginarium import pv

from ._base_entity import LogicGameEntity

class DebugRenderingEntity(LogicGameEntity):
    _cid = GraphicsCIDs.debug_rendering

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            position: Vec2,
            size: Vec2,
            *,
            rendering: DebugRendering = DebugRendering.RECTANGLE,
            color: color_t = (255, 0, 0),
            convert_global: bool = True,
            centered: bool = False,
            **kwargs: tp.Any
    ) -> None:
        super().__init__(runtime_buffer, size=size, position=position, coalition=Coalitions.neutral)
        kwargs["id"] = self.id
        kwargs["coalition"] = Coalitions.neutral
        kwargs["cid"] = self.cid()
        kwargs["color"] = convert_color(color)
        kwargs["convert_global"] = convert_global
        kwargs["rendering"] = rendering
        kwargs["centered"] = centered

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs=kwargs
        ))
