"""
amoginarium/logic/entities/_weapons/_base_weapon.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from types import EllipsisType
from random import random
from ctypes import Array
from icecream import ic
import typing as tp

from amoginarium.shared.audio import ContinuousSoundEffect, ReloadGeneric
from amoginarium.shared.audio import RandomizedEffect, SoundEffect
from amoginarium.shared.utility import Vec2, convert_coord, get_default
from amoginarium.shared import base_entity_t, WeaponCIDs
from amoginarium.shared import Coalitions

from .._bullets import Bullet
from ...._base import Updated, LogicGameEntity, GameCollisions
from ...._items import Item


class BaseWeapon(Item):
    """
    basic functionality of all weapons
    """
    _no_bullet_gravity: bool = False
    _current_recoil_time: float = 0
    _current_sound_time: float = 0
    _current_reload_time: float = 0
    _mag_state: int = 0

    _default_mag_size: int = 1
    _default_reload_time: float = 1
    _default_recoil_time: float = 1
    _default_inaccuracy: float = 1
    _default_muzzle_velocity: float = 1
    _default_recoil_factor: float = 1
    _default_sound_effect: tp.Type[
        ContinuousSoundEffect | SoundEffect | RandomizedEffect | EllipsisType
    ] = ...

    _default_bullet_type: tp.Type[Bullet] = Bullet
    _default_bullet_mount_point: tuple[int, int] | EllipsisType = ...
    _default_cluster_bullet_type: tp.Type[Bullet] | EllipsisType = ...

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        parent_position_offset: Vec2 | tuple[float, float],
        *,
        mag_size: int | EllipsisType = ...,
        reload_time: float | EllipsisType = ...,
        recoil_time: float | EllipsisType = ...,
        inaccuracy: float | EllipsisType = ...,
        muzzle_velocity: float | EllipsisType = ...,
        recoil_factor: float | EllipsisType = ...,
        sound_effect: ContinuousSoundEffect | SoundEffect | RandomizedEffect | EllipsisType = ...,
        bullet_type: tp.Type[Bullet] | EllipsisType = ...,
        weapon_size: Vec2 | EllipsisType = ...,
        drop_casings: bool = False,
        cluster: bool = False,
        spawn_args: dict[str, tp.Any] | EllipsisType = ...,
        **bullet_kwargs,
    ) -> None:

        if weapon_size is ...:
            weapon_size: Vec2 = Vec2().from_cartesian(20, 20)

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=weapon_size,
            spawn_args=spawn_args
        )

        self._e_id = GameCollisions.add_exception()

        # unless you want the sniper to kill its own bullet
        self.remove(Updated)  # CollisionDestroyed

        self._drop_casings = drop_casings

        if not isinstance(sound_effect, EllipsisType):
            self._sound_effect = sound_effect

        elif not isinstance(self._default_sound_effect, EllipsisType):
            self._sound_effect = self._default_sound_effect()

        else:
            self._sound_effect = ...

        self._bullet_kwargs = bullet_kwargs
        self._default_mag_size = get_default(mag_size, self._default_mag_size)
        self._inaccuracy = get_default(inaccuracy, self._default_inaccuracy)
        self._recoil_time = get_default(recoil_time, self._default_recoil_time)
        self._reload_time = get_default(reload_time, self._default_reload_time)
        self._recoil_factor = get_default(recoil_factor, self._default_recoil_factor)
        if cluster:
            if isinstance(self._default_cluster_bullet_type, EllipsisType):
                raise RuntimeError(
                    f"No cluster munition defined for {self.__class__.__name__}"
                )

            self._bullet_type = get_default(
                bullet_type, self._default_cluster_bullet_type
            )

        else:
            self._bullet_type = get_default(bullet_type, self._default_bullet_type)

        self._muzzle_velocity = get_default(
            muzzle_velocity, self._default_muzzle_velocity
        )
        # noinspection PyTypeChecker
        self._parent_position_offset: Vec2 = convert_coord(
            parent_position_offset, Vec2
        )

        self._spawned_graphics = False

        self._runtime_buffer[self.id].param0 = 1

        if isinstance(self._default_bullet_mount_point, EllipsisType):
            self._bullet_offset: Vec2 = Vec2()

        else:
            self._bullet_offset: Vec2 = convert_coord(self._default_bullet_mount_point, Vec2)  # ignore: type

    # region properties
    @property
    def coalition(self) -> Coalitions:
        return self.parent.coalition

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
    def inaccuracy(self) -> float:
        """weapon inaccuracy in rad"""
        return self._inaccuracy

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
                    max_out / self._default_mag_size
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
            self._mag_state = self._default_mag_size
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
        self._set_bit("flags", 13, self._mag_state > 0)

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

        direction.normalize()
        bof = self._bullet_offset.copy()

        if direction.x < 0:
            bof.y *= -1

        bullet_offset = Vec2().from_polar(
            bof.angle + direction.angle,
            bof.length
        )

        self._bullet_type(
            runtime_buffer=self._runtime_buffer,
            parent=self.parent,
            coalition=self.coalition,
            initial_position=(
                self.parent.position
                + self._parent_position_offset
                + bullet_offset
            ),
            initial_velocity=Vec2().from_polar(
                direction.angle, self.muzzle_velocity
            )
            + self.parent.velocity,
            weapon_collision_exception_id=self._e_id,
            initial_facing=direction.angle,
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
            self._mag_state = self._default_mag_size

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


class FileLoadedWeapon(BaseWeapon):
    _CID = WeaponCIDs.base

    def __init__(
            self,
            parent,
            runtime_buffer: Array[base_entity_t],
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2(),
            **kwargs
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            parent_position_offset=parent_position_offset,
            **kwargs
        )
