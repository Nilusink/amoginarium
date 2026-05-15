"""
_sensors.py
15.04.2026

sensor HUDs

Author:
Nilusink
"""

from types import EllipsisType
from icecream import ic  # noqa: F401

from amoginarium.shared.utility import Vec2, Color, unpack_int
from amoginarium.shared import SensorCIDs
from amoginarium import pv

from ._synced_entities import SyncedGraphicsEntity
from ..render_bindings import renderer


class SensorHUD(SyncedGraphicsEntity):
    """
    sensor entity

    ``param0`` detection range
    ``param1`` target x
    ``param2`` target y
    ``param3`` detect sectors (x4, 16 bit each)
    ``param4`` detect sectors (x4, 16 bit each)
    """

    __slots__ = ("_sectors", "_min_rcs", "_vpp")

    _CID = SensorCIDs.hud

    def __init__(
        self,
        sync_id: int,
        sectors: list[Vec2] | EllipsisType = ...,
        min_rcs: float = 0,
        vpp: int = 4,
    ) -> None:
        if isinstance(sectors, EllipsisType):
            sectors: list[Vec2] = []

        super().__init__(sync_id)

        self._sectors = sectors
        self._min_rcs = min_rcs
        self._vpp = vpp

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        world_pos = pv.global_vars.get_world_position()

        renderer.draw_dashed_circle(
            self.pos - world_pos,
            self.param0,
            64,
            (0.3, 0.3, 1, 0.6),
            thickness=1,
        )

        if self._sectors:
            highlighted_sectors: list[int] = [
                *unpack_int(64, self._vpp, self.param3),
                *unpack_int(64, self._vpp, self.param4),
            ]

            for sector in highlighted_sectors:
                if sector < len(self._sectors):
                    t1 = self._sectors[sector]
                    t2 = self._sectors[(sector + 1) % len(self._sectors)]

                    renderer.draw_polygon(
                        (
                            self.world_position,
                            (self.pos + t1) - world_pos,
                            (self.pos + t2) - world_pos,
                        ),
                        color=Color().from_1(0.2, 0.2, 1, 0.5),
                    )


class MagicSensorHUD(SensorHUD):
    _CID = SensorCIDs.sensor_magic


class RadarSensorHUD(SensorHUD):
    _CID = SensorCIDs.sensor_radar

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)
        return

        # t_pos = Vec2().from_cartesian(self.param1, self.param2)
        #
        # if t_pos.length != 0:
        #     world_pos = pv.global_vars.get_world_position()
        #
        #     direction = t_pos - self.pos
        #
        #     dir_1 = direction.copy()
        #     dir_1.angle += self._min_rcs / 2
        #     dir2 = direction.copy()
        #     dir2.angle -= self._min_rcs / 2
        #
        #     renderer.draw_polygon(
        #         (
        #             self.world_position,
        #             (self.pos + dir_1) - world_pos,
        #             (self.pos + dir2) - world_pos,
        #         ),
        #         color=Color().from_1(.2, .2, 1, .5)
        #     )


class VisualSensorHUD(SensorHUD):
    _CID = SensorCIDs.sensor_visual
