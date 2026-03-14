"""
_charged_weapon.py
14.03.2026

weapons that need to charge before firing (bow)

Author:
Nilusink
"""
import typing as tp

from ..base._textures import textures
from ..audio import ContinuousSoundEffect, PresetEffect
from ._weapons import BaseWeapon, Bullet
from ..logic import Vec2, coord_t


class ChargedWeapon(BaseWeapon):
    _image_name: str = "amogus64right"
    _image_size: tuple[int, int] = (16, 16)
    _image_mirror: bool = False
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(8, 8)

    def __init__(
            self,
            parent,
            reload_time: float,
            recoil_time: float,
            recoil_factor: tuple[float, float],
            charge_time: float,
            mag_size: int,
            inaccuracy: float,
            bullet_speed: tuple[float, float],  # range
            barrel_length: float,  # where bullets spawn
            parent_position_offset: Vec2 | tuple[float, float],
            bullet_size: Vec2 | int = 10,
            bullet_damage: float = 1,
            bullet_explosion_radius: tuple[float, float] = (-1, -1),
            bullet_explosion_damage: tuple[float, float] = (0, 0),
            drop_casings: bool = False,
            bullet_lifetime=4,
            sound_effect: ContinuousSoundEffect | PresetEffect = ...,
            bullet_type: tp.Type[Bullet] = Bullet,
            bullet_visibility_offset: float = 0  # time offset
    ) -> None:
        super().__init__(
            parent,
            reload_time,
            recoil_time,
            0,
            mag_size,
            inaccuracy,
            0,
            barrel_length,
            parent_position_offset,
            bullet_size,
            bullet_damage,
            0,
            0,
            drop_casings,
            bullet_lifetime,
            sound_effect,
            bullet_type,
            bullet_visibility_offset
        )
        self._bullet_speed_range = bullet_speed
        self._recoil_range = recoil_factor
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
    def bullet_speed(self) -> float:
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

    def update(self, delta: float) -> None:
        if self._charging:
            self._charged = min(self._charged + delta / self._charge_time, 1)

        if self._mag_state <= 0 and self._current_reload_time == 0:
            self.reload()

        super().update(delta)

    def shoot(
            self,
            direction: Vec2,
            bullet_tof: float = ...,
            target_pos: Vec2 = ...
    ) -> bool:
        res = super().shoot(direction, bullet_tof, target_pos)
        self.stop()
        return res


class Bow(ChargedWeapon):

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: coord_t = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=3,
            recoil_time=.02,
            recoil_factor=(.5, 10),
            charge_time=2,
            mag_size=80,
            inaccuracy=.01093606,
            bullet_speed=(500, 1600),
            bullet_damage=2,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_visibility_offset=.058,
        )


class RailGun(ChargedWeapon):
    _image_name = ...
    _image_scope = "railgun"
    _image_size = (128, 64)
    _image_rotate_anchor = Vec2().from_cartesian(24, 32)

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: coord_t = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=30,
            recoil_time=.1,
            recoil_factor=(.5, 50),
            charge_time=10,
            mag_size=1,
            inaccuracy=.01093606,
            bullet_speed=(2500, 4000),
            bullet_damage=2,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_visibility_offset=.058,
            bullet_explosion_damage=(10, 150),
            bullet_explosion_radius=(5, 512)
        )

        self._images = [t[0] for t in textures.get_all_from_scope(
            self._image_scope,
            self._image_size,
            mirror="x"
        )]
        self._images_m = [t[0] for t in textures.get_all_from_scope(
            self._image_scope,
            self._image_size,
        )]

    @staticmethod
    def _recoil_curve(value: float) -> float:
        return value**2

    @property
    def texture_id_r(self) -> int:
        return self._images[round(self.charged * (len(self._images)-1))]

    @property
    def texture_id_l(self) -> int:
        return self._images_m[round(self.charged * (len(self._images)-1))]
