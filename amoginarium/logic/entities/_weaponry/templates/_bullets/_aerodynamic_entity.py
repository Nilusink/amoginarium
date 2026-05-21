"""
Really simple game-ifyed version of aerodynamics.

Path: amoginarium/logic/entities/_weaponry/templates/_bullets/_aerodynamic_entity.py
Project: amoginarium
Created: 17.04.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import math as m
import typing as tp

from amoginarium.shared import DummyCIDs
from amoginarium.shared.utility import get_default, normalize_angle, Vec2

from ...._base import GameCollisions, GravityAffected
from ._base_bullet import Bullet

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t, Coalitions
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from ...._base import LogicGameEntity


class AerodynamicEntity(Bullet):
    __slots__ = (
        "_rudder_angle",
        "_rudder_max_angle",
        "_rudder_size",
        "_cd",
        "_wh",
        "_mass",
        "ang_vel",
        "_alpha",  # slip angle
        "_forces_to_add",
    )

    _CID = DummyCIDs.aero

    _default_ttl: float = 20

    _default_mass: float = 1
    _default_rudder_size: float = 1
    _default_rudder_max_angle: float = 1

    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionGroupIDType] = (
        GameCollisions.collision_group_aerodynamic_entity
    )

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        size: Vec2,
        *,
        initial_facing: float | EllipsisType,
        rudder_size: float | EllipsisType = ...,
        rudder_max_angle: float | EllipsisType = ...,
        mass: float | EllipsisType = ...,
        collision_exception_ids: list[int] | int | None = None,
        **kwargs,
    ) -> None:
        self._rudder_size = get_default(rudder_size, self._default_rudder_size)
        self._rudder_max_angle = get_default(
            rudder_max_angle, self._default_rudder_max_angle
        )
        self._mass = get_default(mass, self._default_mass)

        self._forces_to_add: list[tuple[Vec2, Vec2]] = []
        self._rudder_angle = 0
        self._alpha = 0
        self.ang_vel = 0

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            initial_position=initial_position,
            initial_velocity=initial_velocity,
            initial_facing=initial_facing,
            parent=parent,
            coalition=coalition,
            collision_exception_ids=collision_exception_ids,
            **kwargs,
        )
        self.add(GravityAffected)

        # game drag
        self._wh = self.size.x / self.size.y
        self._cd = 0.15 + (self.size.y / self.size.x) * 10

    # region properties
    @property
    def mass(self) -> float:
        """Current entity mass."""
        return self._mass

    @property
    def rudder_angle(self) -> float:
        """Current rudder angle."""
        return self._rudder_angle

    @rudder_angle.setter
    def rudder_angle(self, angle: float) -> None:
        self._rudder_angle = angle

    @property
    def alpha(self) -> float:
        """Slip angle (facing vs. velocity)."""
        return self._alpha

    # endregion

    # def velocity interface
    def apply_force(self, relative_force: Vec2, relative_position: Vec2) -> None:
        """Add a force to the entity resulting in acceleration + turning."""
        self._forces_to_add.append((relative_force, relative_position))

    def _update_rudder(self, delta: float) -> None:
        """Update rudder position."""

    def _update(self, delta: float) -> None:
        forward_force = Vec2()

        # common variables
        airflow_d = self.velocity.copy().normalize()
        right = self.facing.copy()
        right.angle += m.pi / 2
        q = self.velocity.length / 1000
        q *= q

        # drag force
        alpha_drag = 500 * (m.sin(self.alpha) ** 2)
        cd_total = self._cd + alpha_drag
        drag_force = airflow_d * (-cd_total * q)
        forward_force += drag_force

        # update rudder position
        self._update_rudder(delta)

        # rudder force
        rudder_force = q * self._rudder_size * self._rudder_angle * 0.3

        lever = self.size.x * 0.5
        rudder_torque = rudder_force * lever

        # stabilization
        side_slip = right.dot(airflow_d)
        stability_torque = side_slip * q * self._wh * 30

        # rudder drag
        turn_drag = airflow_d * (-q * self._rudder_size * abs(self._rudder_angle) * 8)
        forward_force += turn_drag

        # angular motion
        inertia = self.mass * self.size.x * self.size.x * 0.01
        damping = self.ang_vel * 0.8

        torque = stability_torque + rudder_torque - damping

        forces = self._forces_to_add.copy()
        self._forces_to_add.clear()
        for F, r in forces:
            # rotate forces into local space
            F.angle += self.facing.angle
            r.angle += self.facing.angle

            # linear force:
            forward_force += F

            # rotational force
            t = r.x * F.y - r.y * F.x
            torque += t

        ang_acc = torque / inertia
        self.ang_vel += ang_acc * delta
        self.facing.angle += self.ang_vel * delta

        # lift from rudder + body
        lift_force = right * (
            q * self._rudder_size * self._rudder_angle * 50
        )  # rudder lift
        forward_force += lift_force

        body_force = right * (-self.alpha * q * self.size.x * 0.2)  # body lift gain
        forward_force += body_force

        # linear motion
        self.acceleration += forward_force / self.mass
        super()._update(delta, update_facing=False)

        # update alpha
        self._alpha = normalize_angle(self.facing.angle - airflow_d.angle)

        # debugging
        self._buffer.param2 = self.velocity.angle
        self._buffer.param1 = self.velocity.length

    def _update_collision(  # type: ignore
        self,
        *,
        position: Vec2 | EllipsisType = ...,
        size: Vec2 | EllipsisType = ...,
        rotation: float = 0.0,
        positions: list[Vec2] | None = None,
        centered: bool | EllipsisType = ...,
        radius: float | None = None,
        collision_active: bool | EllipsisType = ...,
        shift_history: bool = True,
    ) -> None:
        super()._update_collision(
            position=position,
            size=size,
            rotation=self.facing.angle,
            positions=positions,
            centered=centered,
            radius=radius,
            collision_active=collision_active,
            shift_history=shift_history,
        )
