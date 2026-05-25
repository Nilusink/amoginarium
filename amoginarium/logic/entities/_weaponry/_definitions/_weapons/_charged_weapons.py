"""
Weapons that need to charge before firing (bow).

| ``Path``: amoginarium/logic/entities/_weaponry/_definitions/_weapons/
            _charged_weapons.py
| ``Project``: amoginarium
| ``Created``: 14.03.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import WeaponCIDs
from amoginarium.shared.audio import SmallExplosion
from amoginarium.shared.utility import Vec2

from ...templates import BaseChargedWeapon

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t


class RailGun(BaseChargedWeapon):
    _CID = WeaponCIDs.railgun

    def __init__(
        self,
        parent,
        runtime_buffer: Array[base_entity_t],
        drop_casings: bool = False,
        parent_position_offset: Vec2 | tuple[float, float] = Vec2(),
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=30,
            recoil_time=1,
            weapon_recoil_factor=(0.5, 3),
            charge_time=10,
            mag_size=1,
            inaccuracy=0.01093606,
            bullet_speed=(2500, 4000),
            bullet_damage=(1, 10),
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_damage=(10, 200),
            bullet_explosion_radius=(5, 512),
            sound_effect=SmallExplosion(),
            time_to_life=10,
            visibility_offset=0.058,
        )

    @tp.override
    @staticmethod
    def _recoil_curve(value: float) -> float:
        return value**2
