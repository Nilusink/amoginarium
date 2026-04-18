"""
amoginarium/logic/entities/_weapons/_base_charged_weapon.py

weapons that need to charge before firing (bow)

Project: amoginarium
Created: 14.03.2026
Authors: Nilusink, LukasKrah
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.logic.audio import ContinuousSoundEffect, PresetEffect
from amoginarium.shared import base_entity_t
from amoginarium.shared.utility import Vec2

from ._base_weapon import BaseWeapon
from .._bullets import Bullet

class BaseChargedWeapon(BaseWeapon):
    """
    weapon with ability to charge

    ``param2`` charge state
    """

    def __init__(
            self,
            parent,
            runtime_buffer: Array[base_entity_t],
            reload_time: float,
            recoil_time: float,
            weapon_recoil_factor: tuple[float, float],
            charge_time: float,
            mag_size: int,
            inaccuracy: float,
            bullet_speed: tuple[float, float],  # range
            barrel_length: float,  # where bullets spawn
            parent_position_offset: Vec2 | tuple[float, float],
            bullet_damage: tuple[float, float] = (1, 1),
            bullet_explosion_radius: tuple[float, float] = (-1, -1),
            bullet_explosion_damage: tuple[float, float] = (0, 0),
            drop_casings: bool = False,
            sound_effect: ContinuousSoundEffect | PresetEffect | EllipsisType = ...,
            bullet_type: tp.Type[Bullet] = Bullet,
            **bullet_kwargs
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=reload_time,
            recoil_time=recoil_time,
            mag_size=mag_size,
            inaccuracy=inaccuracy,
            barrel_length=barrel_length,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=0,
            drop_casings=drop_casings,
            sound_effect=sound_effect,
            bullet_type=bullet_type,
            **bullet_kwargs
        )
        self._bullet_speed_range = bullet_speed
        self._bullet_damage_range = bullet_damage
        self._recoil_range = weapon_recoil_factor
        self._explosion_radius_range = bullet_explosion_radius
        self._explosion_damage_range = bullet_explosion_damage
        self._charge_time = charge_time
        self._charging = False
        self._charged = 0  # 0-1

    @staticmethod
    def _speed_curve(value: float) -> float:
        """
        :param value: linear 0-1
        :return: speed factor
        """
        return value

    @staticmethod
    def _recoil_curve(value: float) -> float:
        """
        :param value: linear 0-1
        :return: recoil factor
        """
        return value

    @staticmethod
    def _e_radius_curve(value: float) -> float:
        """
        :param value: linear 0-1
        :return: explosion radius factor
        """
        return value

    @staticmethod
    def _e_damage_curve(value: float) -> float:
        """
        :param value: linear 0-1
        :return: explosion damage factor
        """
        return value

    @property
    def charged(self) -> float:
        """
        amount charged
        """
        return self._charged

    @property
    def muzzle_velocity(self) -> float:
        return self._bullet_speed_range[0] + (
            self._bullet_speed_range[1] - self._bullet_speed_range[0]
        ) * self._speed_curve(self._charged)

    @property
    def recoil_factor(self) -> float:
        return self._recoil_range[0] + (
                self._recoil_range[1] - self._recoil_range[0]
        ) * self._recoil_curve(self._charged)

    @property
    def bullet_explosion_radius(self) -> float:
        return self._explosion_radius_range[0] + (
                self._explosion_radius_range[1] - self._explosion_radius_range[0]
        ) * self._recoil_curve(self._charged)

    @property
    def bullet_explosion_damage(self) -> float:
        return self._explosion_damage_range[0] + (
                self._explosion_damage_range[1] - self._explosion_damage_range[0]
        ) * self._recoil_curve(self._charged)

    @property
    def bullet_damage(self) -> float:
        return self._bullet_damage_range[0] + (
                self._bullet_damage_range[1] - self._bullet_damage_range[0]
        ) * self._recoil_curve(self._charged)

    def _update_kwargs(self) -> None:
        """update weapon params"""
        self._bullet_kwargs["explosion_radius"] = self.bullet_explosion_radius
        self._bullet_kwargs["explosion_damage"] = self.bullet_explosion_damage

    def charge(self) -> None:
        """
        start charging
        """
        self._charging = True

    def stop(self) -> None:
        """
        stop charging (reset to 0)
        """
        self._charging = False
        self._charged = 0

    def _update(self, delta: float) -> None:
        if self._charging:
            # limit charge to 0-1
            self._charged = min(self._charged + delta / self._charge_time, 1)

        if self._mag_state <= 0 and self._current_reload_time == 0:
            self.reload()

        super()._update(delta)
        self._runtime_buffer[self.id].param2 = self._charged

    def shoot(
            self,
            direction: Vec2,
            bullet_tof: float | EllipsisType = ...,
            target_pos: Vec2 | EllipsisType = ...
    ) -> bool:
        self._update_kwargs()
        res = super().shoot(direction, bullet_tof, target_pos)
        self.stop()
        return res
