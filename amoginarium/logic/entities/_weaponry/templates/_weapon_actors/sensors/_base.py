"""
Base weapons sensor used in weapons guidance.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/sensors/
            _base.py
| ``Project``: amoginarium
| ``Created``: 10.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp
from abc import ABC, abstractmethod

from amoginarium.shared import DynamicEntityParentViable, WeaponSensorCIDs

from .._base_actor import BaseActor

if tp.TYPE_CHECKING:
    from amoginarium.shared import CIDType
    from amoginarium.shared.utility import Vec2


class BaseWeaponsSensor(DynamicEntityParentViable, BaseActor, ABC):
    """Sensor for weapons guidance."""

    __slots__ = ()

    _CID: tp.ClassVar[CIDType] = WeaponSensorCIDs.base

    # region class methods
    @classmethod
    def has_cid(cls) -> bool:
        """return: Whether the sensor has a component ID."""
        return True

    @classmethod
    def cid(cls) -> str:
        """:return: Component ID."""
        return cls._CID.value

    # endregion

    # region interface
    @abstractmethod
    def get_target(self) -> Vec2 | None:
        """:return: The sensor target."""

    # endregion
