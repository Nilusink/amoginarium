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

from ...audio import Minigun as MinigunSound, AK47 as AK47Sound, SoundEffect, Shotgun
from ...audio import Mortar as MortarSound, CRAM as CRAMSound, Cannon, Sniper as SniperSound
from .._bullets import SniperBullet, MortarShell, Grenade, FlakBullet, CRAMBullet
from .._bullets import SkyShieldBullet, ClusterMortarShell
from ._base_weapon import BaseWeapon


class Minigun(BaseWeapon):
    """
    Minigun
    """
    _cid = WeaponCIDs.minigun

    def __init__(
            self,
            parent,
            runtime_buffer: Array[base_entity_t],
            drop_casings: bool = False,
            parent_position_offset: coord_t = Vec2()
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=3,
            recoil_time=.00000002,
            mag_size=8000,
            inaccuracy=1,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=1600,
            drop_casings=drop_casings,
            sound_effect=MinigunSound(),

            # bullet args
            base_damage=2,
            time_to_life=10,
            visibility_offset=.058
        )


class Ak47(BaseWeapon):
    """
    Ak-47
    """
    _cid = WeaponCIDs.ak47

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
            reload_time=2.5,
            recoil_time=.1,
            mag_size=30,
            inaccuracy=0.03,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=1250,
            drop_casings=drop_casings,
            sound_effect=AK47Sound(),

            # bullet args
            base_damage=2.5,
            time_to_life=10,
            visibility_offset=0.043,
        )


class Sniper(BaseWeapon):
    """
    Basic Sniper
    """
    _cid = WeaponCIDs.sniper

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
            recoil_time=0.5,
            mag_size=600000,
            inaccuracy=.00500002,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=20000,
            drop_casings=drop_casings,
            sound_effect=SniperSound(),
            bullet_type=SniperBullet,

            # bullet args
            time_to_life=1000,
            visibility_offset=0.04,
            weapon_recoil_factor=10
        )


class Mortar(BaseWeapon):
    """
    Mortar
    """
    _cid = WeaponCIDs.mortar

    _default_bullet_type = MortarShell

    def __init__(
            self,
            parent,
            runtime_buffer: Array[base_entity_t],
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2(),
            muzzle_velocity=1800,
            cluster: bool = False
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=8,
            recoil_time=.25,
            mag_size=1,
            inaccuracy=.00100002,
            barrel_length=10,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=muzzle_velocity,
            drop_casings=drop_casings,
            sound_effect=MortarSound(),
            bullet_type=ClusterMortarShell if cluster else MortarShell,
            
            # bullet args
            time_to_life=7,
            visibility_offset=.025,
        )


class Flak(BaseWeapon):
    """
    Flak Canon
    """
    _cid = WeaponCIDs.flak

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
            reload_time=3,
            recoil_time=0.15,
            mag_size=4,
            inaccuracy=0.0100002,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=1700,
            drop_casings=drop_casings,
            sound_effect=Cannon(),
            bullet_type=FlakBullet,

            # bullet args
            time_to_life=5,
            visibility_offset=0.13,
        )


class CRAM(BaseWeapon):
    """
    CRAM Minigun
    """
    _cid = WeaponCIDs.cram

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
            reload_time=8,
            recoil_time=.005,
            mag_size=800,
            inaccuracy=.001093606,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=3000,
            drop_casings=drop_casings,
            sound_effect=CRAMSound(),
            bullet_type=CRAMBullet,

            # bullet args
            time_to_life=10,
            visibility_offset=.027,
        )


class HandThrownGrenade(BaseWeapon):
    """
    A grenade ... thrown by ...
    your hand
    """
    _cid = WeaponCIDs.h_grenade

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
            recoil_time=0.000000000001,
            weapon_recoil_factor=.00005,
            mag_size=4000,
            inaccuracy=.5,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=800,
            drop_casings=drop_casings,
            bullet_type=Grenade,
            sound_effect=SoundEffect(("groaning", "hugh_1")).set_volume(.6),

            # bullet args
            visibility_offset=.0,
        )


class SkyShieldWeapon(BaseWeapon):
    """smart munitions weapon"""
    _cid = WeaponCIDs.sky_shield

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
            reload_time=8,
            recoil_time=.1,
            mag_size=100,
            inaccuracy=0.005,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=3000,
            sound_effect=Shotgun(),
            bullet_type=SkyShieldBullet,

            # bullet args
            visibility_offset=.08,
        )
