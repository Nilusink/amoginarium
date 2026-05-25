"""
Implements weapons for players and turrets.

| ``Path``: amoginarium/logic/entities/_weaponry/_definitions/_weapons/_weapons.py
| ``Project``: amoginarium
| ``Created``: 01.04.2026
| ``Authors``: LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amoginarium.shared import WeaponCIDs
from amoginarium.shared.audio import SoundEffect
from amoginarium.shared.utility import Vec2

from ...templates import BaseWeapon
from .._bullets import Grenade

if TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t


class HandThrownGrenade(BaseWeapon):
    """
    A grenade ... thrown by ...
    your hand.
    """

    _CID = WeaponCIDs.h_grenade

    _default_recoil_factor = 0.5

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
            reload_time=5,
            recoil_time=0.0001,
            mag_size=1,
            inaccuracy=0.06,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=800,
            drop_casings=drop_casings,
            bullet_type=Grenade,
            sound_effect=SoundEffect(("groaning", "hugh_1")).set_volume(0.6),
            # bullet args
            visibility_offset=0.0,
        )
