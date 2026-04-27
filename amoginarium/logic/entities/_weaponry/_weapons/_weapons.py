"""
_weapons.py
01.04.2026

implements weapons for players and turrets

Author:
Nilusink
"""

from ctypes import Array

from amoginarium.shared.utility import Vec2, coord_t
from amoginarium.shared import base_entity_t, WeaponCIDs

from amoginarium.shared.audio import Minigun as MinigunSound, AK47 as AK47Sound, SoundEffect, Shotgun
from amoginarium.shared.audio import Mortar as MortarSound, CRAM as CRAMSound, Cannon, Sniper as SniperSound
from ._base_weapon import BaseWeapon
from .._bullets import Grenade


class HandThrownGrenade(BaseWeapon):
    """
    A grenade ... thrown by ...
    your hand
    """
    _CID = WeaponCIDs.h_grenade

    _default_recoil_factor = .5

    def __init__(
            self,
            parent,
            runtime_buffer: Array[base_entity_t],
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=5,
            recoil_time=0.000005,
            mag_size=10,
            inaccuracy=.0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=800,
            drop_casings=drop_casings,
            bullet_type=Grenade,
            sound_effect=SoundEffect(("groaning", "hugh_1")).set_volume(.6),

            # bullet args
            visibility_offset=.0,
        )

