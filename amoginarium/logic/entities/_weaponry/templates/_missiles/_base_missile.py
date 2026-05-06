"""
_base_missile.py
05.05.2026

base missile Type

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared import Coalitions, base_entity_t
from amoginarium.shared.utility import Vec2, get_default

from amoginarium.shared import MissileCIDs
from audio import PresetEffect

from ...._base import LogicGameEntity
from .._bullets import AerodynamicEntity


class BaseMissile(AerodynamicEntity):
    """aerodynamic entity with thrust"""

    __slots__ = (
    )

    _CIDs = MissileCIDs.base

    _default_fuel_mass = 0
    _default_size = [100, 10]

    _default_sound_effect: tp.Type[PresetEffect] | EllipsisType = ...

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        *,
        initial_facing: float | EllipsisType = ...,
        rudder_size: float | EllipsisType = ...,
        rudder_max_angle: float | EllipsisType = ...,
        fuel_mass: float | EllipsisType = ...,
        base_mass: float | EllipsisType = ...,
        collision_exception_ids: list[int] | int | None = None,
        **kwargs,
    ) -> None:
        size: Vec2 | list = self._default_size

        if isinstance(self._default_size, (list, tuple)):
            size: Vec2 = Vec2().from_polar(
                self._default_size[0], self._default_size[1]
            )

        size: Vec2

        kwargs.pop("size", None)
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            size,
            initial_facing=initial_facing,
            rudder_size=rudder_size,
            rudder_max_angle=rudder_max_angle,
            mass=base_mass,
            collision_exception_ids=collision_exception_ids,
            **kwargs,
        )
        self.__fuel_mass = get_default(fuel_mass, self._default_fuel_mass)

        if isinstance(self._default_sound_effect, EllipsisType):
            self._sound = ...

        else:
            self._sound = self._default_sound_effect()
            self._sound.volume = .5

    @property
    def _fuel_mass(self) -> float:
        """current fuel mass"""
        return self.__fuel_mass

    @property
    def thrust(self) -> float:
        """currently produced thrust"""
        return 0

    @property
    def mass(self) -> float:
        return self._mass + self._fuel_mass

    def _kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> bool:
        val = super()._kill(killed_by)

        if not isinstance(self._sound, EllipsisType):
            self._sound.stop()

        return val

    def _update(self, delta: float) -> None:
        self.apply_force(
            Vec2().from_polar(0, self.thrust),
            Vec2().from_cartesian(-self.size.x / 2, 0),
        )

        if not isinstance(self._sound, EllipsisType):
            self._sound.update_position(self.position)

            if self.thrust > 0 and not self._sound.playing:
                self._sound.play()

            elif self.thrust <= 0 and self._sound.playing:
                self._sound.stop()

        super()._update(delta)
