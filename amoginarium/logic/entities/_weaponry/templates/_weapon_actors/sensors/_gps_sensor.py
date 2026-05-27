"""
Uses the missile's target_pos as a sensor target.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/
            _weapon_actors/sensors/_gps_sensor.py
| ``Project``: amoginarium
| ``Created``: 14.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import WeaponSensorCIDs

from ._base import BaseWeaponsSensor

if tp.TYPE_CHECKING:
    from amoginarium.shared import CIDType
    from amoginarium.shared.utility import Vec2


class GPSSensor(BaseWeaponsSensor):
    """GPS sensor."""

    __slots__ = ()

    _CID: tp.ClassVar[CIDType] = WeaponSensorCIDs.gps

    @tp.override
    def get_target(self) -> Vec2 | None:
        """:return: The sensor target."""
        t_pos = self._parent.target_pos

        if t_pos:
            return (self._parent.position - t_pos) * -1

        return None
