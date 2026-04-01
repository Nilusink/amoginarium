"""
_weapons.py
01.04.2026

implements weapons for players and turrets

Author:
Nilusink
"""
from random import random
from ctypes import Array
import typing as tp

from amoginarium.shared.utility import Vec2, convert_coord, coord_t
from amoginarium.shared import base_entity_t

from ..audio import ContinuousSoundEffect, PresetEffect, ReloadGeneric
from ..audio import Minigun as MinigunSound, AK47 as AK47Sound, Shotgun
from ..audio import Mortar as MortarSound, CRAM as CRAMSound
from ._base_entity import LogicGameEntity
from ._bullets import Bullet, SniperBullet, MortarShell, Grenade, FlakBullet


class BaseWeapon:
    _no_bullet_gravity: bool = False
    _current_recoil_time: float = 0
    _current_sound_time: float = 0
    _current_reload_time: float = 0
    _mag_state: int = 0
    _recoil_factor: float
    _bullet_speed: float
    _recoil_time: float
    _reload_time: float
    _mag_size: int

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: LogicGameEntity,
            reload_time: float,
            recoil_time: float,
            mag_size: int,
            inaccuracy: float,
            bullet_speed: float,
            barrel_length: float,  # where bullets spawn
            parent_position_offset: Vec2 | tuple[float, float],
            bullet_size: Vec2 | int = 10,
            bullet_damage: float = 1,
            bullet_explosion_radius: float = -1,
            bullet_explosion_damage: float = 0,
            drop_casings: bool = False,
            bullet_lifetime=4,
            sound_effect: ContinuousSoundEffect | PresetEffect = ...,
            bullet_type: tp.Type[Bullet] = Bullet,
            bullet_visibility_offset: float = 0, # time offset
            weapon_recoil_factor: float = 1
    ) -> None:
        self.parent = parent
        self._coalition = parent.coalition
        self._runtime_buffer = runtime_buffer
        self._mag_size = mag_size
        self._inaccuracy = inaccuracy
        self._reload_time = reload_time
        self._recoil_time = recoil_time
        self._reload_time = reload_time
        self._bullet_speed = bullet_speed
        self._drop_casings = drop_casings
        self._recoil_factor = weapon_recoil_factor
        self._bullet_damage = bullet_damage
        self._bullet_size = bullet_size
        self._barrel_length = barrel_length
        self._parent_position_offset = convert_coord(
            parent_position_offset, Vec2
        )
        self._bullet_explosion_radius = bullet_explosion_radius
        self._bullet_explosion_damage = bullet_explosion_damage
        self._bullet_lifetime = bullet_lifetime
        self._sound_effect = sound_effect
        self._bullet_type = bullet_type
        self._bullet_visibility_offset = bullet_visibility_offset

    @property
    def mag_size(self) -> int:
        return self.mag_size

    @property
    def recoil_factor(self) -> float:
        return self._recoil_factor

    @property
    def bullet_speed(self) -> float:
        return self._bullet_speed

    @property
    def bullet_explosion_radius(self) -> float:
        return self._bullet_explosion_radius

    @property
    def bullet_explosion_damage(self) -> float:
        return self._bullet_explosion_damage

    @property
    def parent_position_offset(self) -> Vec2:
        return self._parent_position_offset.copy()

    @property
    def barrel_length(self) -> float:
        return self._barrel_length

    def get_mag_state(
            self,
            max_out: float
    ) -> tuple[float, int] | tuple[float, float]:
        """
        returns the current mag size (rising when reloading)
        :param max_out: output size
        :returns: x out of max_out, value of current state
        """
        if not self._current_reload_time:
            return self._mag_state * (
                    max_out / self._mag_size
            ), self._mag_state

        return (
            (
                    (
                            self._reload_time - self._current_reload_time
                    ) / self._reload_time
            ) * max_out,
            round(self._current_reload_time, 2)
        )

    def update(self, delta: float) -> None:
        """
        update weapon state (like reloading, ...)
        """
        # reload time
        if self._current_reload_time > 0:
            self._current_reload_time -= delta

        if self._current_reload_time < 0 and self._mag_state <= 0:
            self._current_reload_time = 0
            self._mag_state = self._mag_size
            sound_effect = ReloadGeneric()
            sound_effect.play()

        # recoil time
        if self._current_recoil_time > 0:
            self._current_recoil_time -= delta

        if self._current_recoil_time < 0:
            self._current_recoil_time = 0

        # sound
        if self._current_sound_time > 0:
            self._current_sound_time -= delta

        # if self._current_sound_time < 0:
        #     self._current_sound_time = 0

    def stop_shooting(self):
        if hasattr(self._sound_effect, "done"):
            if self._sound_effect.playing:
                self._sound_effect.done()

    def shoot(
            self,
            direction: Vec2,
            bullet_tof: float = ...,
            target_pos: Vec2 = ...
    ) -> bool:
        """
        shoot a bullet and check for recoil and reload

        :returns: true if shot
        """
        # check if mag is empty
        if self._mag_state <= 0:
            if self._current_reload_time == 0:
                self._current_reload_time = self._reload_time
                self.stop_shooting()

            return False

        # audio
        if self._sound_effect is not ...:
            self._current_sound_time = self._recoil_time

        if self._current_recoil_time > 0:
            return False

        if self._sound_effect is not ...:
            if not self._sound_effect.playing:
                self._sound_effect.play()

            elif not hasattr(self._sound_effect, "stage_one_done"):
                self._sound_effect.play()

            if hasattr(self._sound_effect, "stage_one_done"):
                if not self._sound_effect.stage_one_done:
                    return False

        # inaccuracy
        offset = (random() * 2) - 1  # random between -1 - 1
        offset *= self._inaccuracy
        direction.angle += offset

        # recoil
        if hasattr(self.parent, "_impulse_resistance_factor"):
            recoil = Vec2().from_polar(
                direction.angle,
                self._bullet_type.get_recoil_fac(
                    self._bullet_type.get_weight(self._bullet_size),
                    self.bullet_speed + self.parent.velocity.length
                )
            ) * -self.parent._impulse_resistance_factor

            recoil *= self.recoil_factor
            self.parent.add_velocity(recoil)

        self._current_recoil_time = self._recoil_time

        self._mag_state -= 1

        # actual bullet
        if bullet_tof is ...:
            bullet_lifetime = self._bullet_lifetime

        else:
            bullet_lifetime = bullet_tof

        self._bullet_type(
            runtime_buffer=self._runtime_buffer,
            parent=self.parent,
            coalition=self._coalition,
            initial_position=(
                self.parent.position + self._parent_position_offset
                + direction.normalize() * self._barrel_length * .45
            ),
            initial_velocity=direction.normalize() * self.bullet_speed + self.parent.velocity,
            base_damage=self._bullet_damage,
            size=self._bullet_size,
            explosion_radius=self.bullet_explosion_radius,
            explosion_damage=self.bullet_explosion_damage,
            time_to_life=bullet_lifetime,
            target_pos=target_pos,
            no_gravity=self._no_bullet_gravity,
            visibility_offset=self._bullet_visibility_offset
        )

        # TODO: casings
        # if self._drop_casings:

        return True

    def reload(self, instant: bool = False) -> None:
        """
        reload the weapon
        """
        if hasattr(self._sound_effect, "done"):
            if 0 < self._sound_effect.playing < 3:
                self._sound_effect.done()

        self._current_reload_time = 0 if instant else self._reload_time

        if instant:
            self._mag_state = self._mag_size

        else:
            self._mag_state = 0

    def stop(self) -> None:
        """
        stop all running effects
        """
        if self._sound_effect is not ...:
            self._sound_effect.stop()


class Minigun(BaseWeapon):
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
            recoil_time=.02,
            mag_size=80,
            inaccuracy=.01093606,
            bullet_speed=1600,
            bullet_damage=2,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=MinigunSound(),
            bullet_visibility_offset=.058
        )


class Ak47(BaseWeapon):
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
            bullet_size=11,
            bullet_speed=1250,
            bullet_damage=2.5,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=AK47Sound(),
            bullet_visibility_offset=.043
        )


class Sniper(BaseWeapon):
    def __init__(
            self,
            parent,
            runtime_buffer: Array[base_entity_t],
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        s = Shotgun()
        s.volume = .7
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=5,
            recoil_time=2,
            mag_size=6,
            inaccuracy=.00500002,
            bullet_size=15,
            bullet_speed=2500,
            bullet_damage=15,
            barrel_length=0,
            bullet_lifetime=10,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=s,
            bullet_visibility_offset=.04,
            bullet_type=SniperBullet
        )


class Mortar(BaseWeapon):
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
            reload_time=4,
            recoil_time=0,
            mag_size=1,
            inaccuracy=.00100002,
            bullet_size=Vec2().from_cartesian(40, 20),
            bullet_speed=1400,
            bullet_damage=40,
            barrel_length=10,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_radius=200,
            bullet_explosion_damage=50,
            bullet_lifetime=7,
            sound_effect=MortarSound(),
            bullet_type=MortarShell,
            bullet_visibility_offset=.025
        )

class Flak(BaseWeapon):
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
            recoil_time=.15,
            mag_size=4,
            inaccuracy=.0100002,
            bullet_size=18,
            # bullet_speed=1400*2,  # can shoot down bullets, but is too op
            bullet_speed=1700,
            bullet_damage=30,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_radius=100,
            bullet_explosion_damage=40,
            bullet_lifetime=5,
            sound_effect=Shotgun().set_volume(.8),
            bullet_visibility_offset=.13,
            bullet_type=FlakBullet
        )


class CRAM(BaseWeapon):
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
            bullet_speed=3000,
            bullet_damage=.1,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_size=9,
            bullet_lifetime=1,
            bullet_explosion_damage=.1,
            bullet_explosion_radius=15,
            sound_effect=CRAMSound(),
            bullet_visibility_offset=.027  # TODO: smart target tap (max)
        )


class HandThrownGrenade(BaseWeapon):
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
            recoil_time=2,
            weapon_recoil_factor=.5,
            mag_size=1,
            inaccuracy=.01,
            bullet_speed=800,
            bullet_damage=0,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_size=32,
            bullet_lifetime=5,
            bullet_explosion_damage=50,
            bullet_explosion_radius=150,
            bullet_visibility_offset=.0,
            bullet_type=Grenade
        )
