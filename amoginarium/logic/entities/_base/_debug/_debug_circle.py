"""
amoginarium/logic/entities/_base/_debug/_debug_circle.py

Contains the DebugCircleEntity class for rendering debug circles on the graphics side.
Useful for visualizing hitboxes, blast radii, or other circular areas.

Project: amoginarium
Created: 25.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import GraphicsCIDs, Coalitions
from amoginarium.shared.utility import convert_color, Vec2
from amoginarium.shared import BaseCommandType, ProcessCommand
from amoginarium import pv

from .._base_entities import PositionedLogicEntity

if tp.TYPE_CHECKING:
    from types import EllipsisType
    from ctypes import Array

    from amoginarium.shared import base_entity_t, CIDType
    from amoginarium.shared.utility import color_t


class DebugCircleEntity(PositionedLogicEntity):
    """
    A logic-side debug entity representing a circle.
    Communicates with the graphics engine to render a debug shape.
    """

    __slots__ = ()

    # region ClassVars
    _CID: tp.ClassVar[CIDType | EllipsisType] = GraphicsCIDs.debug_circle

    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        position: Vec2,
        radius: float,
        *,
        point_color: color_t = (255, 255, 255),
        point_radius: int = 3,
        point_num_segments: int = 32,
        outline_color: color_t = (255, 255, 255),
        outline_thickness: int = 1,
        fill_color: color_t = (255, 0, 0, 128),
        convert_global: bool = True,
        centered: bool = False,
        **kwargs: tp.Any,
    ) -> None:
        """
        Initializes the DebugCircleEntity and sends a spawn command to the graphics process.
        :param runtime_buffer: The C-level memory buffer for entity state.
        :param position: Initial 2D position vector.
        :param radius: Radius of the circle.
        :param point_color: RGB/A color tuple for the center point.
        :param point_radius: Radius for center point in pixels.
        :param point_num_segments: Resolution for center point.
        :param outline_color: RGB/A color tuple for circle outline.
        :param outline_thickness: Outline thickness in pixels.
        :param fill_color: RGB/A color tuple for filled area.
        :param convert_global: Whether to convert coordinates to global space.
        :param centered: Whether the shape should be rendered centered on position.
        """
        super().__init__(
            runtime_buffer, size=Vec2().from_cartesian(radius, 0), position=position
        )
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

        pv.COQ.put(ProcessCommand(type=BaseCommandType.spawn_dummy, kwargs=kwargs))

    @property
    def radius(self) -> float:
        """
        Gets the radius of the circle.
        :return: The radius value.
        """
        return self.size.x

    @radius.setter
    def radius(self, value: float) -> None:
        """
        Sets the radius of the circle.
        :param value: The new radius value.
        """
        self.size.x = value
