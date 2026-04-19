"""
amoginarium/logic/entities/_static_debug_rendering.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared import DebugRendering, GraphicsCIDs, base_entity_t, Coalitions
from amoginarium.shared.utility import Vec2, color_t, convert_color, MASK16, get_default, normalize_angle
from amoginarium.shared import BaseCommandType, ProcessCommand
from amoginarium import pv

from .._base_entities import LogicGameEntity


class DebugRenderingEntity(LogicGameEntity):
    _cid = GraphicsCIDs.debug_rendering

    __slots__ = ()

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


class PolyDebugRenderingEntity(LogicGameEntity):
    _cid = GraphicsCIDs.debug_poly

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
    ) -> None:
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

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={"id": self.id, "cid": self.cid(), "radius": radius},
        ))

    def set_points(self, points: tp.Sequence[Vec2]) -> None:
        """set all points"""
        for i in range(1, 9):
            getattr(self, f"p{i}").xy = points[i].xy

    def _update(self, delta: float) -> None:
        # normal points
        self._buff.pos_x = self.p1.x
        self._buff.pos_y = self.p1.y

        self._buff.size_x = int(normalize_angle(self.p2.angle) * 10_000)
        self._buff.size_y = int(self.p2.length)

        # float points
        self._buff.param0 = self.p3.angle
        self._buff.param1 = self.p4.angle
        self._buff.param2 = self.p5.angle
        self._buff.facing = int(normalize_angle(self.p6.angle) * 10_000)

        self._buff.param3 = (
            int(self.p3.length) & MASK16
            | (int(self.p4.length) & MASK16) << 16
            | (int(self.p5.length) & MASK16) << 32
            | (int(self.p6.length) & MASK16) << 48
        )

        # dual-packed variables
        self._buff.param4 = (
            int(normalize_angle(self.p7.angle) * 10_000) & MASK16
            | (int(self.p7.length) & MASK16) << 16
            | (int(normalize_angle(self.p8.angle) * 10_000) & MASK16) << 32
            | (int(self.p8.length) & MASK16) << 48
        )
