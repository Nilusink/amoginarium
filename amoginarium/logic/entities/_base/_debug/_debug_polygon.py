"""
Contains the DebugPolygonEntity for rendering arbitrary polygons.

Packs vertex data efficiently into the entity buffer for the renderer.

| Path: amoginarium/logic/entities/_base/_debug/_debug_polygon.py
| Project: amoginarium
| Created: 17.04.2026
| Authors: LukasKrah, Nilusink
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from amoginarium import pv
from amoginarium.shared import BaseCommandType, GraphicsCIDs, ProcessCommand
from amoginarium.shared.utility import convert_color, get_default
from amoginarium.shared.utility import MASK16, normalize_angle, Vec2

from ._debug_entity import DebugEntity

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.utility import color_t


class DebugPolygonEntity(DebugEntity):
    """A debug entity used to render arbitrary polygons by packing vertex data into the entity buffer."""

    _CID = GraphicsCIDs.debug_polygon

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        radius: float = 8,
        p1: Vec2 | EllipsisType = ...,
        p2: Vec2 | EllipsisType = ...,
        p3: Vec2 | EllipsisType = ...,
        p4: Vec2 | EllipsisType = ...,
        p5: Vec2 | EllipsisType = ...,
        p6: Vec2 | EllipsisType = ...,
        p7: Vec2 | EllipsisType = ...,
        p8: Vec2 | EllipsisType = ...,
        points: tp.Sequence[Vec2] | EllipsisType = ...,
        *,
        point_color: color_t = (255, 255, 255),
        point_radius: int = 0,
        point_num_segments: int = 8,
        outline_color: color_t = (255, 255, 255),
        outline_thickness: int = 1,
        fill_color: color_t = (255, 0, 0, 128),
        convert_global: bool = True,
        **kwargs: tp.Any,
    ) -> None:
        """
        Initializes the debug polygon with up to 8 vertices.
        :param runtime_buffer: The shared memory buffer.
        :param radius: The collision or culling radius.
        :param p1: Vertex 1.
        :param p2: Vertex 2.
        :param p3: Vertex 3.
        :param p4: Vertex 4.
        :param p5: Vertex 5.
        :param p6: Vertex 6.
        :param p7: Vertex 7.
        :param p8: Vertex 8.
        :param points: Optional sequence to batch set vertices.
        :param point_color: RGB/A color tuple for the vertex points.
        :param point_radius: Radius for vertex points in pixels.
        :param point_num_segments: Resolution for vertex points.
        :param outline_color: RGB/A color tuple for polygon outline.
        :param outline_thickness: Outline thickness in pixels.
        :param fill_color: RGB/A color tuple for filled area.
        :param convert_global: Whether to use global coordinate space.
        """
        super().__init__(runtime_buffer, position=Vec2(), size=Vec2())

        self.p1 = get_default(p1, Vec2())
        self.p2 = get_default(p2, Vec2())
        self.p3 = get_default(p3, Vec2())
        self.p4 = get_default(p4, Vec2())
        self.p5 = get_default(p5, Vec2())
        self.p6 = get_default(p6, Vec2())
        self.p7 = get_default(p7, Vec2())
        self.p8 = get_default(p8, Vec2())

        if not isinstance(points, EllipsisType):
            self.set_points(points)

        kwargs["id"] = self.id
        kwargs["cid"] = self.cid()
        kwargs["radius"] = radius
        kwargs["point_color"] = convert_color(point_color)
        kwargs["point_radius"] = point_radius
        kwargs["point_num_segments"] = point_num_segments
        kwargs["outline_color"] = convert_color(outline_color)
        kwargs["outline_thickness"] = outline_thickness
        kwargs["fill_color"] = convert_color(fill_color)
        kwargs["convert_global"] = convert_global

        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs=kwargs,
            )
        )

    def set_points(self, points: tp.Sequence[Vec2]) -> None:
        """
        Sets the internal vertex positions from a sequence.
        :param points: A sequence of Vec2 objects.
        """
        for i in range(8):
            if i >= (len(points)):
                return

            getattr(self, f"p{i + 1}").xy = points[i].xy

    @tp.override
    def _update(self, delta: float) -> None:
        """
        Packs vertex data into the C-buffer using bitwise operations for the renderer.
        :param delta: Time since last frame.
        """
        # normal points
        self._buffer.pos_x = self.p1.x
        self._buffer.pos_y = self.p1.y

        self._buffer.size_x = int(normalize_angle(self.p2.angle) * 10_000)
        self._buffer.size_y = int(self.p2.length)

        # float points
        self._buffer.param0 = self.p3.angle
        self._buffer.param1 = self.p4.angle
        self._buffer.param2 = self.p5.angle
        self._buffer.facing = int(normalize_angle(self.p6.angle) * 10_000)

        self._buffer.param3 = (
            int(self.p3.length) & MASK16
            | (int(self.p4.length) & MASK16) << 16
            | (int(self.p5.length) & MASK16) << 32
            | (int(self.p6.length) & MASK16) << 48
        )

        # dual-packed variables
        self._buffer.param4 = (
            int(normalize_angle(self.p7.angle) * 10_000) & MASK16
            | (int(self.p7.length) & MASK16) << 16
            | (int(normalize_angle(self.p8.angle) * 10_000) & MASK16) << 32
            | (int(self.p8.length) & MASK16) << 48
        )
