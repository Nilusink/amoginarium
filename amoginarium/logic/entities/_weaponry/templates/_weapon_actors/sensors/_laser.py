"""
_sensors.py
10.05.2026

laser sensor and designator

Author:
Nilusink
"""

import typing as tp
from types import EllipsisType

from amoginarium.shared import WeaponSensorCIDs
from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.utility import Vec2

from ....._base import GameCollisions
from ._base import BaseWeaponsSensor

if tp.TYPE_CHECKING:
    from ..._bullets import AerodynamicEntity

_LASER_POINTERS: dict[int, Vec2] = {}


class LaserDesignator:
    """designate targets for laser sensor"""

    def __init__(self, code: int = 1688) -> None:
        """
        Designate targets for laser sensor

        :param code: laser code
        """
        self.__code: int = code
        self._collision_groups = GameCollisions.all_groups

    @property
    def code(self) -> int:
        """Designator code"""
        return self.__code

    def shine(self, origin: Vec2, direction: Vec2, max_range: float) -> None:
        """Shine the laser in a direction"""
        entities: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                self._collision_groups,
                origin,
                origin + Vec2().from_polar(direction.angle, max_range),
            )
        )

        if entities:
            _LASER_POINTERS[self.__code] = entities[0].position

        else:
            _LASER_POINTERS.pop(self.__code, None)


class LaserSensor(BaseWeaponsSensor):
    """homes in on a laser"""

    _CID = WeaponSensorCIDs.laser

    def __init__(
        self,
        parent: "AerodynamicEntity",
        code: int,
        *,
        offset: tuple[float, float] | Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Homes in on a designated laser

        :param parent: parent bullet
        :param code: laser code
        :param offset: offset from parent
        :param function_delay: sensor function delay
        """
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self.__code: int = code
        self._target: Vec2 | None = None

    # region properties
    @property
    def code(self) -> int:
        """Designator code"""
        return self.__code

    # endregion

    # region interface
    def get_target(self) -> Vec2 | None:
        """Get sensor target"""
        if self._target:
            return self._parent.position - self._target

        return None

    # endregion

    def _update(self) -> None:
        # update position
        super()._update()

        if self.__code in _LASER_POINTERS:
            self._target = _LASER_POINTERS[self.__code].copy()
