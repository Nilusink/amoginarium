"""
_multi_thruster_missile.py
11.05.2026

missile that maneuvers by applying small thrusters

Author:
Nilusink
"""

from ctypes import Array
from types import EllipsisType

import numpy as np

from amoginarium.shared import base_entity_t, Coalitions, MissileCIDs
from amoginarium.shared.utility import normalize_angle_neg, PI, PI_2, Vec2

from ...._base import LogicGameEntity
from ._guided_multi_stage_missile import GuidedMultiStageMissile


class MultiThrusterMissile(GuidedMultiStageMissile):
    _CID = MissileCIDs.multi_thruster
    _DEBUG = True

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
        base_mass: float | EllipsisType = ...,
        collision_exception_ids: list[int] | int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            initial_facing=initial_facing,
            rudder_size=rudder_size,
            rudder_max_angle=rudder_max_angle,
            base_mass=base_mass,
            collision_exception_ids=collision_exception_ids,
            **kwargs,
        )

        self._directional_thrust_values: list[float] = [0] * 4
        self._directional_thrust_amount = 5_000
        self._directional_tolerance = 0.0

        self._rotational_thrust_values: list[float] = [0] * 2
        self._rotational_thrust_amount = 500
        self._rotational_tolerance = 0.01

        # pause thrust until ready
        self._apply_thrust = False

    def _update_guidance(self, dt: float, target_delta: Vec2 | None = None) -> None:
        if self._current_stage != 0:
            self._directional_thrust_values = [0] * 4
            self._rotational_thrust_values = [0] * 2
            super()._update_guidance(dt, target_delta)

            if target_delta:
                self._dbe.p5 = self.position + target_delta

            return

        # rotational thrust
        angular_velocity = self.ang_vel

        # rotate towards target
        angle_delta = np.inf
        if target_delta:
            if self._current_stage == 0:
                target_delta.y = min(0, target_delta.y)

            angle_delta = normalize_angle_neg(target_delta.angle - self.facing.angle)
            angular_target_velocity = np.sign(angle_delta) * max(0.2, abs(angle_delta))

        else:
            angular_target_velocity = normalize_angle_neg(-self.facing.angle)
            self._dbe.p5 = Vec2()

        if angular_velocity > angular_target_velocity + self._rotational_tolerance:
            self._rotational_thrust_values[0] = self._rotational_thrust_amount
            self._rotational_thrust_values[1] = 0

        elif angular_velocity < angular_target_velocity - self._rotational_tolerance:
            self._rotational_thrust_values[1] = self._rotational_thrust_amount
            self._rotational_thrust_values[0] = 0

        else:
            self._rotational_thrust_values[0] = 0
            self._rotational_thrust_values[1] = 0

        # directional thrust
        # apply space stabilization if not rotated enough, else apply main thruster
        # rotate velocity into local coordinate system
        velocity = self.velocity.copy()

        if target_delta:
            desired_velocity = Vec2()
            if abs(angle_delta) <= self._rotational_tolerance and velocity.length <= 1:
                self._apply_thrust = True

        else:
            desired_velocity = Vec2().from_cartesian(1000, 0)

            if self.position.y > 0:
                desired_velocity.y = -100

            self._apply_thrust = False

        desired_velocity.angle -= self.facing.angle
        velocity.angle -= self.facing.angle

        # update thrusters
        if velocity.y > desired_velocity.y + self._directional_tolerance:
            self._directional_thrust_values[3] = self._directional_thrust_amount
            self._directional_thrust_values[1] = 0

        elif velocity.y < desired_velocity.y - self._directional_tolerance:
            self._directional_thrust_values[1] = self._directional_thrust_amount
            self._directional_thrust_values[3] = 0

        else:
            self._directional_thrust_values[1] = 0
            self._directional_thrust_values[3] = 0

        if velocity.x > desired_velocity.x + self._directional_tolerance:
            self._directional_thrust_values[2] = self._directional_thrust_amount
            self._directional_thrust_values[0] = 0

        elif velocity.x < desired_velocity.x - self._directional_tolerance:
            self._directional_thrust_values[0] = self._directional_thrust_amount
            self._directional_thrust_values[2] = 0

        else:
            self._directional_thrust_values[0] = 0
            self._directional_thrust_values[2] = 0

        if target_delta:
            self._dbe.p5 = self.position + target_delta

    def _update(self, delta: float, apply_thrust: bool = True) -> None:
        # update stuff
        # noinspection PyArgumentEqualDefault
        super()._update(delta, True)

        # ic(self._apply_thrust)

        # cheat
        # self.facing.x = 1
        # self.facing.y = 1

        # apply rotational thrust
        if self._rotational_thrust_values[0] != 0:
            self.apply_force(
                Vec2().from_polar(PI_2, self._rotational_thrust_values[0]),
                Vec2().from_cartesian(-self.size.x / 3, 0),  # apply at back of missile
            )

        if self._rotational_thrust_values[1] != 0:
            self.apply_force(
                Vec2().from_polar(PI_2 * 3, self._rotational_thrust_values[1]),
                Vec2().from_cartesian(-self.size.x / 3, 0),  # apply at back of missile
            )

        # apply directional thrust
        for direction in range(4):
            self.apply_force(
                Vec2().from_polar(
                    PI_2 * direction, self._directional_thrust_values[direction]
                ),
                Vec2(),
            )

        # update debug entity
        if self._DEBUG:
            self._dbe.p1 = self.position + Vec2().from_polar(
                self.facing.angle + 0,
                max(
                    200
                    * (
                        self._directional_thrust_values[0]
                        / self._directional_thrust_amount
                    ),
                    1,
                ),
            )
            self._dbe.p2 = self.position + Vec2().from_polar(
                self.facing.angle + PI_2,
                max(
                    200
                    * (
                        self._directional_thrust_values[1]
                        / self._directional_thrust_amount
                    ),
                    1,
                ),
            )
            self._dbe.p3 = self.position + Vec2().from_polar(
                self.facing.angle + PI,
                max(
                    200
                    * (
                        self._directional_thrust_values[2]
                        / self._directional_thrust_amount
                    ),
                    1,
                ),
            )
            self._dbe.p4 = self.position + Vec2().from_polar(
                self.facing.angle + PI_2 * 3,
                max(
                    200
                    * (
                        self._directional_thrust_values[3]
                        / self._directional_thrust_amount
                    ),
                    1,
                ),
            )
