"""
A rideable turret that calculates bullet launch angle.

Path: amoginarium/logic/entities/_weaponry/
      templates/_turrets/_calculated_rideable_turret.py
Project: amoginarium
Created: 14.05.2026
Authors: LukasKrah
"""

from __future__ import annotations

import ctypes
import typing as tp
from contextlib import suppress
from types import EllipsisType

from amoginarium.shared import TurretCIDs
from amoginarium.shared.utility import calculate_launch_angle, get_default, MASK32, Vec2

from ...._base import GravityAffected
from ._base_turret import TargetSolution
from ._rideable_turret import RideableTurret

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, Coalitions


class CalculatedRideableTurret(RideableTurret):
    _CID = TurretCIDs.rideable_calculated

    # region ClassVars
    _default_max_error: tp.ClassVar[float | EllipsisType] = ...
    _default_engagement_aim_type: tp.ClassVar[tp.Literal["low", "high"]] = "low"
    # endregion

    __slots__ = ("_max_error", "_target_solution")

    # region InstanceVars
    _max_error: float
    _target_solution: TargetSolution | None

    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        coalition: Coalitions,
        position: Vec2,
        *,
        cluster: bool = False,
        size: Vec2 | float | tuple[float, float] | list[float] | EllipsisType = ...,
        weapon_kwargs: dict[str, tp.Any] | EllipsisType = ...,
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            coalition=coalition,
            position=position,
            cluster=cluster,
            size=size,
            weapon_kwargs=weapon_kwargs,
        )

        self._weapon_static = not isinstance(
            self._default_weapon_static_facing, EllipsisType
        )

        if self._weapon_static:
            self.weapon.facing.angle = self._default_weapon_static_facing

        # params
        self._max_error = get_default(self._default_max_error, self.weapon.inaccuracy)
        self._target_solution = None

    @property
    def weapon_pos(self) -> Vec2:
        """Position of weapon."""
        return self.position + self.weapon.parent_position_offset

    def _get_firing_solution(
        self,
        target_pos: Vec2,
        *,
        velocity: Vec2 | EllipsisType = ...,
        acceleration: Vec2 | EllipsisType = ...,
        recalc: int = 5,
    ) -> TargetSolution | None:
        """Try to get a firing solution for target pos."""
        position_delta = self.weapon_pos - target_pos
        vel = get_default(velocity, Vec2())
        acc = get_default(acceleration, Vec2())

        # mirror y-axis (because in pygame, + is down)
        position_delta.y *= -1
        vel.y *= -1
        acc.y *= -1

        # mirror x if < 0 because calculate_launch_angle is weird and it works this ways
        mirror = False
        if position_delta.x < 0:
            position_delta.x *= -1
            vel.x *= -1
            acc.x *= -1
            mirror = True

        with suppress(ValueError):
            aiming_angle, tof, predict = calculate_launch_angle(
                position_delta,
                vel,
                acc,
                self.weapon.muzzle_velocity,
                recalc,
                self._default_engagement_aim_type,
                g=GravityAffected.gravity * 2,
            )

            # mirror back y-axis
            aiming_angle.y *= -1
            predict.y *= -1

            if mirror:
                aiming_angle.x *= -1
                predict.x *= -1

            target_predict = self.weapon_pos + predict

            return TargetSolution(
                track=object,  # type: ignore[not-used]
                target_predict=target_predict,
                angle=aiming_angle,
                tof=tof,
            )

        return None

    @tp.override
    def _shoot_at(
        self,
        target_angle: Vec2,
        tof: float | EllipsisType = ...,
        target_pos: Vec2 | EllipsisType = ...,
        **bullet_args: tp.Any,
    ) -> None:
        # check if static facing
        if self._weapon_static or self._default_engagement_ignore_solution:
            # check if there is a target
            if not self._target_solution:
                return

            super()._shoot_at(
                target_angle=self.weapon.facing,
                target_pos=self._target_solution.target_predict,
            )
            return

        # check if solution is valid
        if not self._target_solution:
            return

        # check if position is inside error
        if (
            abs(self._target_solution.angle.angle - self.facing.angle)
            <= self._max_error
        ):
            super()._shoot_at(
                target_angle,
                tof=self._target_solution.tof,
                target_pos=self._target_solution.target_predict,
            )

    @tp.override
    def _update(self, delta: float, *, set_facing: bool = True) -> None:
        super()._update(delta, set_facing=False)

        # calculate target position
        if self._target_angle.length != 0:
            target_delta = self._target_angle.copy()
            self._target_solution = self._get_firing_solution(
                self.position - target_delta, recalc=20
            )

            target: Vec2 | None = None
            if (
                self._weapon_static and target_delta
            ) or self._default_engagement_ignore_solution:
                target: Vec2 = self.position + target_delta
                self._target_solution = TargetSolution(
                    target,
                    Vec2(),
                    -1,
                    track=object,  # type: ignore[unused]
                )

                if not self._weapon_static:
                    self._turn_at(target_delta.angle, delta)

            elif self._target_solution:
                self._turn_at(self._target_solution.angle.angle, delta)

                target = self._target_solution.target_predict

            if target:
                x32 = ctypes.c_int32(int(target.x)).value
                y32 = ctypes.c_int32(int(target.y)).value
                self._runtime_buffer[self.id].param3 = ctypes.c_uint64(
                    x32 & MASK32
                ).value | (ctypes.c_uint64(y32 & MASK32).value << 32)
