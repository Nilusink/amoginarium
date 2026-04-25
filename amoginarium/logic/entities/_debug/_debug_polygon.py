"""
amoginarium/logic/entities/_debug/_debug_polygon.py

Project: amoginarium
Created: 25.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared import GraphicsCIDs
from amoginarium.shared.utility import Vec2, MASK16, get_default, normalize_angle
from amoginarium.shared import BaseCommandType, ProcessCommand
from amoginarium import pv

from .._base_entities import LogicGameEntity

if tp.TYPE_CHECKING:
    from types import EllipsisType
    from ctypes import Array

    from amoginarium.shared import base_entity_t


class DebugPolygonEntity(LogicGameEntity):
    """A debug entity used to render arbitrary polygons by packing vertex data into the entity buffer. """
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
        """
        super().__init__(
            runtime_buffer=runtime_buffer,
            position=Vec2(),
            size=Vec2()
        )

        self.p1 = get_default(p1, Vec2())
        self.p2 = get_default(p2, Vec2())
        self.p3 = get_default(p3, Vec2())
        self.p4 = get_default(p4, Vec2())
        self.p5 = get_default(p5, Vec2())
        self.p6 = get_default(p6, Vec2())
        self.p7 = get_default(p7, Vec2())
        self.p8 = get_default(p8, Vec2())
        if points is not ...:
            self.set_points(points)

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={"id": self.id, "cid": self.cid(), "radius": radius},
        ))

    def set_points(self, points: tp.Sequence[Vec2]) -> None:
        """
        Sets the internal vertex positions from a sequence.
        :param points: A sequence of Vec2 objects.
        """
        for i in range(8):
            if i >= (len(points)):
                return

            getattr(self, f"p{i + 1}").xy = points[i].xy

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
