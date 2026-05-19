"""
Base missile Type.

Path: amoginarium/logic/entities/_weaponry/templates/_missiles/_base_missile.py
Project: amoginarium
Created: 05.05.2026
Authors: Nilusink
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from amoginarium.shared import MissileCIDs
from amoginarium.shared.utility import get_default, normalize_angle_neg, Vec2

from ...._base import DebugPolygonEntity
from .._bullets import AerodynamicEntity

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, Coalitions
    from amoginarium.shared.audio import PresetEffect

    from ...._base import LogicGameEntity


class BaseMissile(AerodynamicEntity):
    """aerodynamic entity with thrust."""

    __slots__ = ()

    # region ClassVars
    _CIDs = MissileCIDs.base
    _DEBUG: tp.ClassVar[bool] = False

    _default_fuel_mass: tp.ClassVar[float] = 0
    _default_size: tp.ClassVar[tuple[float, float] | list[float]] = [100, 10]

    _default_sound_effect: tp.ClassVar[type[PresetEffect] | EllipsisType] = ...

    # endregion

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
        **kwargs,  # noqa: ANN003
    ) -> None:
        size: Vec2 | list | tuple = self._default_size

        if isinstance(self._default_size, (list, tuple)):
            size: Vec2 = Vec2().from_polar(self._default_size[0], self._default_size[1])

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
            self._sound.volume = 0.5

        if self._DEBUG:
            self._dbe = DebugPolygonEntity(runtime_buffer, fill_color=(255, 0, 0, 20))

    # region properties
    @property
    def _fuel_mass(self) -> float:
        """Current fuel mass."""
        return self.__fuel_mass

    @property
    def thrust(self) -> float:
        """Currently produced thrust."""
        return 0

    @property
    def mass(self) -> float:
        return self._mass + self._fuel_mass

    @property
    def alpha(self) -> float:
        return normalize_angle_neg(self.velocity.angle - self.facing.angle)

    # endregion

    def _kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> bool:
        val = super()._kill(killed_by)

        if not isinstance(self._sound, EllipsisType):
            self._sound.stop()

        if self._DEBUG:
            self._dbe.kill()

        return val

    def _update(self, delta: float, apply_thrust: bool = True) -> None:  # noqa: FBT002
        # apply thrust force at rear of missile
        if self.thrust != 0 and apply_thrust:
            self.apply_force(
                Vec2().from_polar(0, self.thrust),
                Vec2().from_cartesian(-self.size.x / 2, 0),
            )

        # update sound state
        if not isinstance(self._sound, EllipsisType):
            self._sound.update_position(self.position)

            if self.thrust > 0 and not self._sound.playing:
                self._sound.play()

            elif self.thrust <= 0 and self._sound.playing:
                self._sound.stop()

        # update position
        super()._update(delta)

        # update debug entity
        if self._DEBUG:
            self._dbe.p1 = self.position.copy()
            self._dbe.p2 = self.position + Vec2().from_polar(self.velocity.angle, 300)
            self._dbe.p3 = self.position + Vec2().from_polar(self.facing.angle, 300)
