"""
_sensors.py
15.04.2026

sensor HUDs

Author:
Nilusink
"""

from icecream import ic

from amoginarium.shared.utility import Vec2
from amoginarium.shared import SensorCIDs
from amoginarium import pv

from ._synced_entities import SyncedGraphicsEntity
from ..render_bindings import renderer


class SensorHUD(SyncedGraphicsEntity):
    """
    sensor entity

    ``param0`` detection range
    ``param3`` detect sectors (x4, 16 bit each)
    ``param4`` detect sectors (x4, 16 bit each)
    """

    __slots__ = ("_sectors",)

    _cid = SensorCIDs.hud

    def __init__(self, sync_id: int, sectors: bool = False) -> None:
        super().__init__(sync_id)

        self._sectors = sectors

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        renderer.draw_dashed_circle(
            self.world_position,
            self.param0,
            64,
            (0.3, 0.3, 1, 0.6),
            thickness=1,
        )
