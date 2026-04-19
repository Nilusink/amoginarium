"""
amoginarium/graphics/logic_dummies/_dynamic_debug_rendering.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from icecream import ic
import typing as tp

from amoginarium.shared.utility import Color, Vec2, MASK16
from amoginarium.shared import DebugRendering, GraphicsCIDs
from amoginarium import pv

from ._synced_entities import SyncedGraphicsEntity
from ..entities import Drawn_2, Drawn_0
from ..render_bindings import renderer


class DebugRenderingEntity(SyncedGraphicsEntity):
    _cid = GraphicsCIDs.debug_rendering

    __rendering: DebugRendering
    __convert_global: bool

    def __init__(
            self,
            sync_id: int,
            rendering: DebugRendering,
            color: tuple[int, int, int] | tuple[int, int, int, int],
            centered: bool = False,
            convert_global: bool = False,
            **_kwargs: tp.Any
    ) -> None:
        super().__init__(sync_id)
        self.__rendering = rendering
        self.__convert_global = convert_global
        self.__color = color
        self.__centered = centered

        self.add(Drawn_2)
        self.remove(Drawn_0)

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        pos = self.world_position - self.size / 2 if self.__centered else self.world_position
        match self.__rendering:
            case DebugRendering.RECTANGLE:
                renderer.draw_rect_line(start=pos, size=self.size, thickness=5,
                                        color=self.__color, convert_global=self.__convert_global)


class PolyDebugRenderingEntity(SyncedGraphicsEntity):
    __slots__ = ("p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "radius")
    _cid = GraphicsCIDs.debug_poly

    def __init__(self, radius=8, **kwargs):
        self.p1 = Vec2()
        self.p2 = Vec2()
        self.p3 = Vec2()
        self.p4 = Vec2()
        self.p5 = Vec2()
        self.p6 = Vec2()
        self.p7 = Vec2()
        self.p8 = Vec2()

        super().__init__(**kwargs)
        # self.remove(Drawn_0)
        # self.add(Drawn_2)

        self.radius = radius
        ic("De spawn")

    def _update_from_buffer(self) -> None:
        self.alive = self._get_bit("flags", 0)
        self._logic_visibility = self._get_bit("flags", 1)
        self._highlight = self._get_bit("flags", 2)

        if not self._was_alive:
            if self.alive:
                self._was_alive = True

        else:
            if not self.alive:
                self._logic_visibility = True
                self._visible = True
                self.kill()

        # normal positions
        self.p1.x = self._buff.pos_x
        self.p1.y = self._buff.pos_y

        self.p2.length = self._buff.size_y
        self.p2.angle = float(self._buff.size_x) / 10_000

        # float points
        self.p3.length = self._buff.param3 & MASK16
        self.p4.length = (self._buff.param3 >> 16) & MASK16
        self.p5.length = (self._buff.param3 >> 32) & MASK16
        self.p6.length = (self._buff.param3 >> 48) & MASK16

        self.p3.angle = self._buff.param0
        self.p4.angle = self._buff.param1
        self.p5.angle = self._buff.param2
        self.p6.angle = float(self._buff.facing) / 10_000

        # dual-packed variables
        self.p7.length = (self._buff.param4 >> 16) & MASK16
        self.p7.angle = float(self._buff.param4 & MASK16) / 10_000
        self.p8.length = (self._buff.param4 >> 48) & MASK16
        self.p8.angle = float((self._buff.param4 >> 32) & MASK16) / 10_000

    # noinspection DuplicatedCode
    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        world_pos = pv.global_vars.get_world_position()
        renderer.draw_circle(
            self.p1 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p2 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p3 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p4 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p5 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p6 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p7 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
        renderer.draw_circle(
            self.p8 - world_pos, self.radius, self.radius, Color().from_1(1, 1, 0)
        )
