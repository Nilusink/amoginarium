"""
Heat seeking sensor.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/sensors/
            _heat_seeker.py
| ``Project``: amoginarium
| ``Created``: 10.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import WeaponSensorCIDs
from amoginarium.shared.utility import clamp_angle, PI_2, Vec2

from ....._base import DebugPolygonEntity, GameCollisions
from ._base import BaseWeaponsSensor

if tp.TYPE_CHECKING:
    from types import EllipsisType

    from amoginarium.shared import MurderViable
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from ..._bullets import AerodynamicEntity


class HeatSeeker(BaseWeaponsSensor):
    """Heat seeking sensor."""

    __slots__ = (
        "_fov",
        "_max_range",
        "_target_pos",
        "_collision_groups",
        "_coll_poly",
        "_collisions",
    )

    # region ClassVars
    _CID = WeaponSensorCIDs.heat
    # endregion

    # region InstanceVars
    _fov: float
    _max_range: float
    _target_pos: Vec2 | None
    _collision_groups: list[CollisionGroupIDType]
    _coll_poly: list[Vec2]
    _collisions: list[CollisionEvent]
    # endregion

    def __init__(
        self,
        parent: AerodynamicEntity,
        fov: float,
        max_range: float,
        *,
        offset: tuple[float, float] | Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create a heat-seeking sensor.

        :param parent: Parent bullet
        :param fov: Field of view of the sensor
        :param max_range: Maximum range of the sensor
        :param offset: Offset from parent
        :param function_delay: Sensor function delay
        """
        self._fov = fov
        self._max_range = max_range
        self._target_pos: Vec2 | None = None
        self._collision_groups = [
            GameCollisions.collision_group_turrets,
            GameCollisions.collision_group_items,
            GameCollisions.collision_group_players,
        ]
        self._coll_poly = [
            Vec2(),
        ] * 4
        self._collisions = []

        super().__init__(parent, offset=offset, function_delay=function_delay)

        if self._dbe is not None:
            self._dbe.kill(killed_by=self)
            self._dbe = DebugPolygonEntity(self.parent.runtime_buffer)

        GameCollisions.add_extra_calculate_callback(self.__calculate_targets_collisions)

    @tp.override
    def _update_position(self) -> None:
        """Update fuze position."""
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

    def __calculate_targets_collisions(self) -> None:
        """Calculate all potential targets."""
        self._collisions: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                self._collision_groups,
                self._position,
                self._position,
                hitbox_type="polygon",
                start_positions=list(self._coll_poly),
            )
        )

    @tp.override
    def get_target(self) -> Vec2 | None:
        """:return: The sensor target."""
        if self._target_pos:
            return self._target_pos

        return None

    @tp.override
    def _update(self) -> None:
        """Update the heat seeker sensor."""
        # update position
        super()._update()

        largest_rcs: float = 0.0
        for col in self._collisions:
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

    def kill(self, killed_by: MurderViable | EllipsisType) -> None:
        """
        Kills this heat seeker.

        :param killed_by: Who killed this seeker
        """
        GameCollisions.remove_extra_calculate_callback(
            self.__calculate_targets_collisions
        )
        super().kill(killed_by)
