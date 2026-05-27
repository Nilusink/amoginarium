"""
Laser sensor and designator.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/sensors/
            _laser.py
| ``Project``: amoginarium
| ``Created``: 10.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import WeaponSensorCIDs
from amoginarium.shared.utility import Vec2

from ....._base import GameCollisions
from ._base import BaseWeaponsSensor

if tp.TYPE_CHECKING:
    from types import EllipsisType

    from amoginarium.shared import CIDType
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from ..._bullets import AerodynamicEntity

_laser_pointers: dict[int, Vec2] = {}


class LaserDesignator:
    """Designate targets for laser sensor."""

    __slots__ = (
        "__code",
        "_collision_groups",
    )

    _code: int
    _collision_groups: list[CollisionGroupIDType]

    def __init__(self, code: int = 1688) -> None:
        """
        Designate targets for laser sensor.

        :param code: laser code
        """
        self.__code: int = code
        self._collision_groups = GameCollisions.all_groups

    @property
    def code(self) -> int:
        """Designator code."""
        return self.__code

    def shine(self, origin: Vec2, direction: Vec2, max_range: float) -> None:
        """
        Shine the laser in a direction.

        :param origin: Origin of the laser
        :param direction: Direction of the laser
        :param max_range: Maximum range of the laser
        """
        entities: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                self._collision_groups,
                origin,
                origin + Vec2().from_polar(direction.angle, max_range),
            )
        )

        if entities:
            _laser_pointers[self.__code] = entities[0].position

        else:
            _laser_pointers.pop(self.__code, None)


class LaserSensor(BaseWeaponsSensor):
    """homes in on a laser."""

    __slots__ = (
        "__code",
        "_target",
    )

    _CID: tp.ClassVar[CIDType] = WeaponSensorCIDs.laser

    __code: int
    _target: Vec2 | None

    def __init__(
        self,
        parent: AerodynamicEntity,
        code: int,
        *,
        offset: tuple[float, float] | Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Homes in on a designated laser.

        :param parent: Parent bullet
        :param code: Laser code
        :param offset: Offset from parent
        :param function_delay: Sensor function delay
        """
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self.__code = code
        self._target = None

    # region properties
    @property
    def code(self) -> int:
        """Designator code."""
        return self.__code

    # endregion

    # region interface
    @tp.override
    def get_target(self) -> Vec2 | None:
        """:return: The sensor target."""
        if self._target:
            return self._parent.position - self._target
        return None

    # endregion

    @tp.override
    def _update(self) -> None:
        """Update the laser sensor."""
        # update position
        super()._update()

        if self.__code in _laser_pointers:
            self._target = _laser_pointers[self.__code].copy()
