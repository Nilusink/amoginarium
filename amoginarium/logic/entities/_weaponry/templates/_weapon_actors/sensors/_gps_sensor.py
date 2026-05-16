"""
_gps_sensor.py
14.05.2026

uses the missile's target_pos as sensor target

Author:
Nilusink
"""

from amoginarium.shared import WeaponSensorCIDs
from amoginarium.shared.utility import Vec2

from ._base import BaseWeaponsSensor


class GPSSensor(BaseWeaponsSensor):
    """heat seeking sensor"""

    _CID = WeaponSensorCIDs.gps

    def get_target(self) -> Vec2 | None:
        t_pos = self._parent.target_pos

        if t_pos:
            return (self._parent.position - t_pos) * -1

        return None
