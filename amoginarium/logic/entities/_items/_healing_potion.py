"""
amoginarium/logic/entities/_items/_healing_potion.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from ctypes import Array
import typing as tp
import math as m

from amoginarium.shared.utility import Vec2
from amoginarium.shared import base_entity_t, ItemCIDs

from ...audio import PotionDrink, ContinuousSoundEffect
from ._base_item import BaseItem


class HealingPotion(BaseItem):
    """
    healing potion

    ``param0``: f_tilt
    """

    _COMPONENT_ID = ItemCIDs.healing_potion
    _max_uses = 80

    _heal_per_sec: tp.ClassVar[int] = 20

    __slots__ = ("_drinking", "_f_velocity", "_f_tilt", "_target_rotation", "_sound")

    _drinking: bool
    _f_velocity: float
    _f_tilt: float
    _target_rotation: float
    _sound: ContinuousSoundEffect

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent_position_offset: Vec2,
    ) -> None:
        super().__init__(
            runtime_buffer, Vec2().from_cartesian(32, 32), parent_position_offset
        )
        self._drinking = False

        self._sound = PotionDrink()
        self._sound.volume = 1
        self._target_rotation = 0
        self._f_velocity = 0
        self._f_tilt = 0

    def use(self) -> None:
        self._drinking = True

    def stop_use(self) -> None:
        self._drinking = False
        if self._sound.playing:
            self._sound.done()

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
                if not self._sound.playing:
                    self._sound.play()

            else:
                self.stop_use()

            if self._uses_left <= 0:
                self.stop_use()
                self.kill()

        stiffness = .2
        damping = .9

        self._target_rotation = self.facing.angle * (180 / m.pi)
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
