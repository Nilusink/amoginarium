"""
_items.py
12.03.2026

various items that are not weapons

Author:
Nilusink
"""
from types import EllipsisType
from ctypes import Array
from icecream import ic
import typing as tp
import pygame as pg
import math as m

from amoginarium.shared.utility import normalize_angle, Vec2
from amoginarium.shared import base_entity_t, ItemCIDs
from amoginarium import pv

from ..audio import RocketSound
from ._logic_groups import CollisionDestroyed, Updated, GravityAffected, WallCollider
from ._base_entity import LogicGameEntity
from ._base_item import Item


class BaseItem(Item):
    __slots__ = ("_uses_left", "_parent_position_offset", "_used_callback")

    _max_uses: int = 1

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            parent_position_offset: Vec2
    ) -> None:
        super().__init__(runtime_buffer, size)
        self._uses_left = self._max_uses
        self._parent_position_offset = parent_position_offset
        self._used_callback = None

    # region properties
    # noinspection PyTypeChecker
    @property
    def max_uses(self) -> int:
        return self._max_uses

    @property
    def uses_left(self) -> int:
        return self._uses_left

    # endregion

    def add_used_callback(self, callback: tp.Callable[[int], bool]) -> None:
        self._used_callback = callback

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x,
            self.position.y,
            self.size.x,
            self.size.y
        )

    def _update(self, delta: float, *, keep_position: bool = False) -> None:
        super()._update(delta, keep_position=keep_position)
        self._runtime_buffer[self.id].param1, _ = self.get_mag_state(1)

    # region interface
    def get_mag_state(
            self,
            max_out: float
    ) -> tuple[float, int] | tuple[float, float]:
        """
        returns the current uses (rising when reloading)
        naming borrowed from BaseWeapon for compatability

        :param max_out: output size
        :returns: x out of max_out, value of current state
        """
        return self._uses_left * (
                max_out / self._max_uses
        ), self._uses_left

    def use(self) -> None:
        """use the item"""
        raise NotImplementedError

    def stop_use(self) -> None:
        """stop using the item"""
        raise NotImplementedError

    def stop(self) -> None:
        """stop ... again?"""
        ...

    def kill(self, killed_by=...) -> None:
        if self._used_callback and self._used_callback(1):
            self._uses_left = self._max_uses

        else:
            super().kill()

    def reset(self) -> None:
        """reset the item"""
        self._uses_left = self._max_uses

    # endregion


class Shield(BaseItem):
    __slots__ = ("_in_use",)

    _image_name: tuple[str, str] | str = ("Shield_6", "4")
    _image_size: tuple[int, int] = (45, 80)
    _max_uses: int = 200  # acts as HP for shield
    _cid = ItemCIDs.shield

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent_position_offset: Vec2
    ) -> None:
        super().__init__(
            runtime_buffer,
            Vec2().from_cartesian(*self._image_size),
            parent_position_offset,
        )
        self._generate_collision_mask()

        self._in_use = False
        self._update_mask()

    @property
    def hp(self) -> float:
        return self._uses_left

    def use(self) -> None:
        """
        start using the item
        """
        if not self._in_use:
            self._in_use = True
            self.add(CollisionDestroyed)

    def stop_use(self) -> None:
        """
        stop using the item
        """
        if self._in_use:
            self._in_use = False
            self.remove(CollisionDestroyed)

    def _update_mask(self) -> None:
        # angle = self.facing.angle * 180 / m.pi
        # angle = angle % 360
        #
        # if 90 < angle < 270:
        #     surf = pg.transform.rotate(
        #         self._mask_left_surf,
        #         -(angle - 180)
        #     )
        #
        # else:
        #     surf = pg.transform.rotate(
        #         self._mask_right_surf,
        #         -angle
        #     )
        #
        # offset = (surf.size[0] - self.size.x) / 2
        #
        # surf = surf.subsurface(
        #     (offset, offset),
        #     self.size.xy
        # )

        super()._generate_collision_mask()
        # self.mask = pg.mask.Mask(surf)

    def hit(self, damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        if not self.parent:
            super().hit(damage, hit_by)

        self._uses_left -= damage

        if self._uses_left <= 0:
            self.kill(hit_by)

    def _update(self, delta: float, **_) -> None:
        if self.parent:
            d = Vec2().from_polar(self.facing.angle, self._parent_position_offset.length)
            if self._in_use:
                self.size.xy = self._image_size
                self.position = self.parent.position + d - self.size / 2

            else:
                self.size.xy = self._image_size[0] * .1, self._image_size[1] * .3
                self.position = self.parent.position

            super()._update(delta, keep_position=True)
            return

        else:
            self.size.xy = self._image_size

            # move shield out of way
            self.position.xy = (-1, -1)

        super()._update(delta)


class HealingPotion(BaseItem):
    """
    healing potion

    ``param0``: f_tilt
    """

    __slots__ = ("_drinking", "_f_velocity", "_f_tilt", "_target_rotation")

    _cid = ItemCIDs.healing_potion
    _heal_per_sec = 20
    _max_uses = 80

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent_position_offset: Vec2,
    ) -> None:
        super().__init__(
            runtime_buffer, Vec2().from_cartesian(32, 32), parent_position_offset
        )
        self._drinking = False

        self._target_rotation = 0
        self._f_velocity: float = 0
        self._f_tilt: float = 0

    def use(self) -> None:
        self._drinking = True

    def stop_use(self) -> None:
        self._drinking = False

    def _update(self, delta: float, **_) -> None:
        if not self.parent:
            super()._update(delta)
            return

        if self._drinking:
            # noinspection PyTypeChecker
            heal = min(
                self._uses_left,
                self._heal_per_sec * delta
            )
            if self.parent.heal(heal):
                self._uses_left -= heal

            if self._uses_left <= 0:
                self.kill()

        stiffness = .2
        damping = .9

        self._target_rotation = self.facing.angle * (180/m.pi)
        target = -self._target_rotation
        acceleration = (target - self._f_tilt) * stiffness

        # acceleration influence
        acc_mag, acc_angle = self.parent.acceleration.polar
        acc_angle *= 180 / m.pi

        acceleration += (
            m.sin(m.radians(acc_angle))
            * acc_mag
            * self.parent.acceleration.length
            / 500
        )

        self._f_velocity += acceleration
        self._f_velocity *= damping
        self._f_tilt += self._f_velocity

        super()._update(delta)
        self._runtime_buffer[self.id].param0 = self._f_tilt


class JetBag(BaseItem):
    """makes you flyyyyyy"""

    __slots__ = ("_in_use", "_facing", "_size_fac", "_sound")

    _cid = ItemCIDs.jetbag
    _reload_per_second: float = .2
    _acceleration = 19
    _max_uses: int = 5

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent_position_offset: Vec2,
    ) -> None:
        super().__init__(
            runtime_buffer,
            Vec2().from_cartesian(32, 64),
            parent_position_offset=parent_position_offset,
        )

        self._sound = RocketSound()
        self._in_use = False
        self._facing = True
        self._size_fac = 1

    def use(self) -> None:
        self._in_use = True
        if not self._sound.playing:
            self._sound.play(pos=self.position)

    def stop_use(self) -> None:
        self._in_use = False
        if self._sound.playing:
            self._sound.stop()

    def _update(self, delta: float, **_) -> None:
        if not self.parent:
            self._set_bit("flags", 14, False)  # set use to false
            super()._update(delta)
            return

        # set in use
        self._set_bit("flags", 14, self._in_use)

        # adjust position
        self.facing.angle = self.parent.facing.angle

        if self.facing.x > 0:
            self.position = self.parent.position + self._parent_position_offset
            self.position -= self.size / 2

        else:
            self.position = self.parent.position - self._parent_position_offset
            self.position -= self.size / 2

        if self._in_use:
            if self._uses_left > 0:
                self._uses_left -= delta

                if self._sound.playing:
                    self._sound.update_position(self.position)

                if hasattr(self.parent, "_impulse_resistance_factor"):
                    # noinspection PyProtectedMember
                    recoil = Vec2().from_cartesian(
                        0,
                        -self.parent._impulse_resistance_factor
                    )
                    recoil.length *= (
                        self._acceleration * pv.global_vars.get_acceleration_factor()
                    )
                    self.parent.add_acceleration(recoil)

            else:
                if self._sound.playing:
                    self._sound.stop()

                self._set_bit("flags", 14, False)  # set use to false

        elif self.parent.on_ground:
            if self._uses_left < self._max_uses:
                self._uses_left = min(
                    self._uses_left + self._reload_per_second * delta,
                    self._max_uses
                )

        super()._update(delta, keep_position=True)
