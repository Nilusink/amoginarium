"""
Base for all vehicle types.

| Path: amoginarium/logic/entities/_weaponry/templates/_vehicles/_base_vehicle.py
| Project: amoginarium
| Created: 19.05.2026
| Authors: Nilusink
"""

from __future__ import annotations

import typing as tp

from icecream import ic

from amoginarium import pv
from amoginarium.shared import VehicleCIDs
from amoginarium.shared.utility import Vec2

from ...._base import FrictionXAffected, GameCollisions, GravityAffected
from .._turrets import RideableTurret

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t, Coalitions


class Vehicle(RideableTurret):
    """Base class for all vehicle types."""

    _CID = VehicleCIDs.base
    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_vehicles

    __slots__ = ()

    # region ClassVars
    _default_engine_power: tp.ClassVar[float] = 1
    _impulse_resistance_factor: tp.ClassVar[float] = 1  # 0 = completely resistant
    _default_max_speed: tp.ClassVar[float] = 1500

    _default_size: tp.ClassVar[tuple[int, int] | list[int]] = (256, 128)
    # endregion

    # region InstanceVars
    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        coalition: Coalitions,
        position: Vec2,
        *,
        size: Vec2 | float | tuple[float, float] | list[float] | EllipsisType = ...,
        weapon_kwargs: dict[str, tp.Any] | EllipsisType = ...,
    ) -> None:
        super().__init__(
            runtime_buffer,
            size=size,
            position=position,
            coalition=coalition,
            weapon_kwargs=weapon_kwargs,
        )
        self.add(GravityAffected, FrictionXAffected)
        self._on_ground = False

    # region rideable interface
    @property
    def camera_centered(self) -> bool:
        return False

    # endregion

    @tp.override
    def _update(self, delta: float, *, set_facing: bool = True) -> None:
        # update movement
        # update keys
        controller = self._controller
        if controller and self._player:
            acc_fac = pv.global_vars.get_acceleration_factor()
            acc_fac *= self._default_engine_power

            # horizontal movement
            if controller.joy_x > 0.3 and self.velocity.x <= self._default_max_speed:
                self.velocity.x += self._impulse_resistance_factor * delta * acc_fac

            elif (
                controller.joy_x < -0.3 and self.velocity.x >= -self._default_max_speed
            ):
                self.velocity.x -= self._impulse_resistance_factor * delta * acc_fac

            # vertical movement
            if controller.jump:
                self.add_acceleration(
                    Vec2().from_cartesian(0, -GravityAffected.gravity * 1.1)
                )

        # check if on floor
        if GameCollisions.collision_group_islands in self._active_normals:
            for normal in self._active_normals[GameCollisions.collision_group_islands]:
                if (normal.y < 0.1 and self.velocity.y > 0) or (
                    normal.y > 0.1 and self.velocity.y < 0
                ):
                    self.velocity.y = 0
                    self.acceleration.y = 0
                    self._on_ground = True

                else:
                    self._on_ground = False

                # fmt: off
                # if (
                #     (normal.x > 0.1 and self.velocity.x > 0)
                #     or (normal.x < 0.1 and self.velocity.x < 0)
                # ):
                #     # fmt: on
                #     self.velocity.x *= -1

        super()._update(delta, set_facing=set_facing)
