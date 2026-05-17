"""
_heat_seeker.py
10.05.2026

heat seeking sensor

Author:
Nilusink
"""

import typing as tp
from types import EllipsisType

from amoginarium.shared import WeaponSensorCIDs
from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.utility import clamp_angle, PI_2, Vec2

from ....._base import DebugPolygonEntity, GameCollisions
from ._base import BaseWeaponsSensor

if tp.TYPE_CHECKING:
    from ..._bullets import AerodynamicEntity


class HeatSeeker(BaseWeaponsSensor):
    """heat seeking sensor"""

    _CID = WeaponSensorCIDs.heat

    def __init__(
        self,
        parent: "AerodynamicEntity",
        fov: float,
        max_range: float,
        *,
        offset: tuple[float, float] | Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        homes in on a designated laser

        :param parent: parent bullet
        :param offset: offset from parent
        :param function_delay: sensor function delay
        """
        self._fov = fov
        self._max_range = max_range
        self._target_pos: Vec2 | None = None
        self._collision_groups = [
            GameCollisions.collision_group_turrets,
            GameCollisions.collision_group_items,
            GameCollisions.collision_group_players,
        ]
        self._coll_poly: list[Vec2] = [
            Vec2(),
        ] * 4

        super().__init__(parent, offset=offset, function_delay=function_delay)

        if self._dbe is not None:
            self._dbe.kill(self)
            self._dbe = DebugPolygonEntity(self.parent.runtime_buffer)

    def _update_position(self) -> None:
        super()._update_position()

        self._coll_poly[0] = self._position
        self._coll_poly[1] = self._position + Vec2().from_polar(
            self.parent.facing.angle + self._fov / 2, self._max_range
        )
        self._coll_poly[2] = self._position + Vec2().from_polar(
            self.parent.facing.angle, self._max_range
        )
        self._coll_poly[3] = self._position + Vec2().from_polar(
            self.parent.facing.angle - self._fov / 2, self._max_range
        )

        if isinstance(self._dbe, DebugPolygonEntity):
            self._dbe.p1 = self._coll_poly[0]
            self._dbe.p2 = self._coll_poly[1]
            self._dbe.p3 = self._coll_poly[2]
            self._dbe.p4 = self._coll_poly[3]

    def get_target(self) -> Vec2 | None:
        if self._target_pos:
            return self._target_pos

        return None

    def _update(self) -> None:
        # update position
        super()._update()

        # update target
        collisions: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                self._collision_groups,
                self._position,
                self._position,
                hitbox_type="polygon",
                start_positions=list(self._coll_poly),
            )
        )

        largest_rcs = 0
        for col in collisions:
            other = col.other_entity

            if other is self.parent.parent:
                continue

            delta = self.parent.position - other.position
            min_delta = self.parent.position - (
                other.position
                + Vec2().from_polar(delta.angle - PI_2, other.size.length)
            )
            max_delta = self.parent.position - (
                other.position
                + Vec2().from_polar(delta.angle + PI_2, other.size.length)
            )

            min_angle = clamp_angle(min_delta.angle, delta.angle, self._fov / 2)
            max_angle = clamp_angle(max_delta.angle, delta.angle, self._fov / 2)

            rcs = abs(min_angle - max_angle)

            if rcs > largest_rcs:
                largest_rcs = rcs
                self._target_pos = delta * -1

        if largest_rcs == 0:
            self._target_pos = None
