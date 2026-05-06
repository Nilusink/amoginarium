"""
_aero.py
17.04.2026

aerodynamics skeleton entity

Author:
Nilusink
"""

from types import EllipsisType
import math as m

from amoginarium.shared.utility import Color, Vec2
from amoginarium.shared import DummyCIDs

from ..render_bindings import renderer
from ._synced_entities import SyncedGraphicsEntity


class AeroDummy(SyncedGraphicsEntity):
    _CID = DummyCIDs.aero

    def __init__(
        self,
        sync_id: int,
        *,
        spawn_time: float = 0,
        visibility_offset: float = 0,
        target_pos: Vec2 | EllipsisType = ...,
        **kwargs
    ):
        super().__init__(sync_id)

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        # length
        renderer.draw_thick_line(
            self.world_position - self.facing * self.size.x / 2,
            self.world_position + self.facing * self.size.x / 2,
            Color().from_1(1, 1, .0),
            thickness=4
        )

        right = self.facing.copy()
        right.angle += m.pi / 2
        renderer.draw_thick_line(
            self.world_position - right * self.size.y / 2,
            self.world_position + right * self.size.y / 2,
            Color().from_1(.8, .1, .1),
            thickness=4
        )

        # draw velocity vec
        renderer.draw_thick_line(
            self.world_position,
            self.world_position + Vec2().from_polar(self.param2, self.param1 / 10),
            Color().from_1(0, 1, 0),
            thickness=2
        )
