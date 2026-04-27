"""
amoginarium/logic/entities/_debug/_debug_rectangle.py

Project: amoginarium
Created: 25.04.2026
Authors: LukasKrah
"""

from __future__ import annotations


import typing as tp

from amoginarium.shared import GraphicsCIDs, Coalitions
from amoginarium.shared.utility import convert_color
from amoginarium.shared import BaseCommandType, ProcessCommand
from amoginarium import pv

from .._base_entities import LogicGameEntity

if tp.TYPE_CHECKING:
    from types import EllipsisType
    from ctypes import Array

    from amoginarium.shared import base_entity_t, CIDType
    from amoginarium.shared.utility import Vec2, color_t


class DebugRectangleEntity(LogicGameEntity):
    """Logic entity for rendering debug rectangles via the graphics engine."""
    __slots__ = ()

    # region ClassVars
    _CID: tp.ClassVar[CIDType | EllipsisType] = GraphicsCIDs.debug_rectangle

    # endregion

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            position: Vec2,
            size: Vec2,
            *,
            color: color_t = (255, 0, 0),
            convert_global: bool = True,
            centered: bool = False,
            **kwargs: tp.Any
    ) -> None:
        """
        Initializes a debug rectangle and queues a spawn command for the graphics process.
        :param runtime_buffer: C-level memory buffer for entity state.
        :param position: Initial 2D position.
        :param size: Dimensions of the rectangle.
        :param color: RGB color tuple.
        :param convert_global: Whether to use global coordinate space.
        :param centered: Whether to render from the center or top-left.
        """
        super().__init__(runtime_buffer, size=size, position=position, coalition=Coalitions.neutral)
        kwargs["id"] = self.id
        kwargs["coalition"] = Coalitions.neutral
        kwargs["cid"] = self.cid()
        kwargs["color"] = convert_color(color)
        kwargs["convert_global"] = convert_global
        kwargs["centered"] = centered

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs=kwargs
        ))
