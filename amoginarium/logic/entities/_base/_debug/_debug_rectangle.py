"""
amoginarium/logic/entities/_base/_debug/_debug_rectangle.py

Contains the DebugRectangleEntity for drawing rectangular debug shapes.
Helpful for visualizing bounding boxes or trigger areas on the graphics side.

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

from .._base_entities import PositionedLogicEntity

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, CIDType
    from amoginarium.shared.utility import Vec2, color_t


class DebugRectangleEntity(PositionedLogicEntity):
    """Logic entity for rendering debug rectangles via the graphics engine."""
    __slots__ = ()

    # region ClassVars
    _CID: tp.ClassVar[CIDType] = GraphicsCIDs.debug_rectangle

    # endregion

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            position: Vec2,
            size: Vec2,
            *,
            point_color: color_t = (255, 255, 255),
            point_radius: int = 3,
            point_num_segments: int = 8,
            outline_color: color_t = (255, 255, 255),
            outline_thickness: int = 1,
            fill_color: color_t = (255, 0, 0, 128),
            convert_global: bool = True,
            centered: bool = False,
            **kwargs: tp.Any
    ) -> None:
        """
        Initializes a debug rectangle and queues a spawn command for the graphics process.
        :param runtime_buffer: C-level memory buffer for entity state.
        :param position: Initial 2D position.
        :param size: Dimensions of the rectangle.
        :param point_color: RGB/A color tuple for corner points.
        :param point_radius: Radius for corner points in pixels.
        :param point_num_segments: Resolution for corner points.
        :param outline_color: RGB/A color tuple for rectangle outline.
        :param outline_thickness: Outline thickness in pixels.
        :param fill_color: RGB/A color tuple for filled area.
        :param convert_global: Whether to use global coordinate space.
        :param centered: Whether to render from the center or top-left.
        """
        super().__init__(runtime_buffer, size=size, position=position)
        kwargs["id"] = self.id
        kwargs["coalition"] = Coalitions.neutral
        kwargs["cid"] = self.cid()
        kwargs["point_color"] = convert_color(point_color)
        kwargs["point_radius"] = point_radius
        kwargs["point_num_segments"] = point_num_segments
        kwargs["outline_color"] = convert_color(outline_color)
        kwargs["outline_thickness"] = outline_thickness
        kwargs["fill_color"] = convert_color(fill_color)
        kwargs["convert_global"] = convert_global
        kwargs["centered"] = centered

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs=kwargs
        ))
