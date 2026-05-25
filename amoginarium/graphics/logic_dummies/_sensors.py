"""
Sensor HUDs.

| ``Path``: amoginarium/graphics/logic_dummies/_sensors.py
| ``Project``: amoginarium
| ``Created``: 15.04.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from icecream import ic

from amoginarium import pv
from amoginarium.shared import SensorCIDs
from amoginarium.shared.utility import Color, unpack_int

from ..render_bindings import renderer
from ._synced_entities import SyncedGraphicsEntity

if tp.TYPE_CHECKING:
    from amoginarium.shared.utility import Vec2


class SensorHUD(SyncedGraphicsEntity):
    """
    Sensor entity.

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

    @tp.override
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
                        color=Color().from_1(0.3, 0.3, 1, 0.1),
                    )


class MagicSensorHUD(SensorHUD):
    _CID = SensorCIDs.sensor_magic


class RadarSensorHUD(SensorHUD):
    _CID = SensorCIDs.sensor_radar

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)


class VisualSensorHUD(SensorHUD):
    _CID = SensorCIDs.sensor_visual
