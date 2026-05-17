"""
_weapons.py
01.04.2026

implements weapons for players and turrets

Author:
Nilusink
"""

from ctypes import Array

from amoginarium.shared import base_entity_t, WeaponCIDs
from amoginarium.shared.audio import SoundEffect
from amoginarium.shared.utility import Vec2

from ...templates import BaseWeapon
from .._bullets import Grenade


class HandThrownGrenade(BaseWeapon):
    """
    A grenade ... thrown by ...
    your hand
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
            mag_size=5000,
            inaccuracy=0.5,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=800,
            drop_casings=drop_casings,
            bullet_type=Grenade,
            sound_effect=SoundEffect(("groaning", "hugh_1")).set_volume(0.6),
            # bullet args
            visibility_offset=0.0,
        )
