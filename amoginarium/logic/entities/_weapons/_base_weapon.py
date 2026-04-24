"""
amoginarium/logic/entities/_weapons/_base_weapon.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from typing_extensions import deprecated
from types import EllipsisType
from random import random
from ctypes import Array
import typing as tp

from amoginarium.shared.utility import Vec2, convert_coord, get_default
from amoginarium.shared import base_entity_t, WeaponCIDs

from ...audio import ContinuousSoundEffect, ReloadGeneric, RandomizedEffect, SoundEffect
from .._bullets import Bullet
from .._groups import Updated
from .._base_entities import LogicGameEntity
from .._items import Item

# todo - mytodo - collisiondestroyed

class BaseWeapon(Item):
    """
    basic functionality of all weapons
    """
    _CID = WeaponCIDs.base
    _no_bullet_gravity: bool = False
    _current_recoil_time: float = 0
    _current_sound_time: float = 0
    _current_reload_time: float = 0
    _mag_state: int = 0
    _recoil_factor: float
    _muzzle_velocity: float
    _recoil_time: float
    _reload_time: float
    _mag_size: int

    _default_bullet_type: tp.Type[Bullet] = Bullet

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        reload_time: float,
        recoil_time: float,
        mag_size: int,
        inaccuracy: float,
        parent_position_offset: Vec2 | tuple[float, float],
        muzzle_velocity: float,
        *,
        barrel_length: float = 0,  # where bullets spawn
        drop_casings: bool = False,
        sound_effect: ContinuousSoundEffect | SoundEffect | RandomizedEffect | EllipsisType = ...,
        bullet_type: tp.Type[Bullet] | EllipsisType = ...,
        weapon_recoil_factor: float = 1,
        weapon_size: Vec2 | EllipsisType = ...,
        spawn_args: dict[str, tp.Any] | EllipsisType = ...,
        **bullet_kwargs,
    ) -> None:
        if weapon_size is ...:
            weapon_size: Vec2 = Vec2().from_cartesian(20, 20)

        super().__init__(runtime_buffer=runtime_buffer, size=weapon_size, spawn_args=spawn_args)

        # unless you want the sniper to kill its own bullet
        self.remove(Updated)  # CollisionDestroyed

        self._coalition = parent.coalition
        self._mag_size = mag_size
        self._inaccuracy = inaccuracy
        self._reload_time = reload_time
        self._recoil_time = recoil_time
        self._reload_time = reload_time
        self._drop_casings = drop_casings
        self._recoil_factor = weapon_recoil_factor
        self._barrel_length = barrel_length
        self._parent_position_offset: Vec2 = convert_coord(
            parent_position_offset, Vec2
        )
        self._sound_effect = sound_effect
        self._bullet_type = get_default(bullet_type, self._default_bullet_type)
        self._muzzle_velocity = muzzle_velocity
        self._spawned_graphics = False
        self._bullet_kwargs = bullet_kwargs

        self._runtime_buffer[self.id].param0 = 1

    # region properties
    @property
    def parent(self) -> LogicGameEntity:
        """
        Weapon parent (player / turret)
        """
        return self._parent

    @property
    def mag_size(self) -> int:
        """
        max mag size
        """
        return self.mag_size

    @property
    def recoil_factor(self) -> float:
        """
        recoil modifier
        """
        return self._recoil_factor

    @property
    def parent_position_offset(self) -> Vec2:
        """
        offset to parent center
        """
        return self._parent_position_offset.copy()

    @property
    def muzzle_velocity(self) -> float:
        """the weapons muzzle velocity"""
        return self._muzzle_velocity

    @property
    @deprecated("replaced by bullet_visibility_offset")
    def barrel_length(self) -> float:
        """
        length of weapon barrel (unused)
        """
        return self._barrel_length

    # endregion

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

    def _update(self, delta: float) -> None:
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
            sound_effect.play(pos=self.position)

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

        if self.parent:
            self.position = self.parent.position + self._parent_position_offset

        super()._update(delta, keep_position=True)
        self._runtime_buffer[self.id].param1, _ = self.get_mag_state(1)

    def stop_shooting(self):
        """
        stop shooting the weapon (sound)
        """
        if hasattr(self._sound_effect, "done"):
            if self._sound_effect.playing:
                self._sound_effect.done()

    def shoot(
            self,
            direction: Vec2,
            bullet_tof: float | EllipsisType = ...,
            target_pos: Vec2 | EllipsisType = ...,
            **bullet_args
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
                self._sound_effect.play(pos=self.position)

            elif not hasattr(self._sound_effect, "stage_one_done"):
                self._sound_effect.play(pos=self.position)

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
                    self._bullet_type.get_weight(self._bullet_type._default_size),
                    self.muzzle_velocity + self.parent.velocity.length
                )
            ) * -self.parent._impulse_resistance_factor

            recoil *= self.recoil_factor
            self.parent.add_velocity(recoil)

        self._current_recoil_time = self._recoil_time

        self._mag_state -= 1

        # actual bullet
        kwargs = self._bullet_kwargs.copy()

        kwargs.update(bullet_args)

        if not isinstance(bullet_tof, EllipsisType):
            kwargs["time_to_life"] = bullet_tof

        self._bullet_type(
            runtime_buffer=self._runtime_buffer,
            parent=self.parent,
            coalition=self._coalition,
            initial_position=(
                self.parent.position
                + self._parent_position_offset
                + direction.normalize() * self._barrel_length * 0.45
            ),
            initial_velocity=Vec2().from_polar(
                direction.angle, self.muzzle_velocity
            )
            + self.parent.velocity,
            target_pos=target_pos,
            no_gravity=self._no_bullet_gravity,
            **kwargs
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
        self._current_recoil_time = 0

        if instant:
            self._mag_state = self._mag_size

        else:
            self._mag_state = 0

    def _stop_recoil(self) -> None:
        self._current_recoil_time = 0

    def stop(self) -> None:
        """
        stop all running effects
        """
        if self._sound_effect is not ...:
            if hasattr(self._sound_effect, "stage_one_done"):
                self._sound_effect.stop()
