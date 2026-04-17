"""
_aerodynamic_entity.py
17.04.2026

Really simple game-ifyed version of aerodynamics

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
import math as m

from amoginarium.shared import base_entity_t, Coalitions, DummyCIDs, ProcessCommand, BaseCommandType
from amoginarium.shared.utility import Vec2, get_default
from amoginarium import pv

from ._logic_groups import GravityAffected
from ._base_entity import LogicGameEntity


class AerodynamicEntity(LogicGameEntity):
    __slots__ = (
        "_rudder_angle",
        "_rudder_max_angle",
        "_rudder_size",
        "_cd",
        "_wh",
        "_mass",
        "ang_vel",
    )

    _cid = DummyCIDs.aero
    _default_mass: float = 1
    _default_rudder_size: float = 1
    _default_rudder_max_angle: float = 1

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        size: Vec2,
        position: Vec2,
        *,
        initial_velocity: Vec2 | None = None,
        parent: LogicGameEntity | None = None,
        coalition: Coalitions | EllipsisType = ...,
        rudder_size: float | EllipsisType = ...,
        rudder_max_angle: float | EllipsisType = ...,
        mass: float | EllipsisType = ...,
    ) -> None:
        self._rudder_size = get_default(rudder_size, self._default_rudder_size)
        self._rudder_max_angle = get_default(rudder_max_angle, self._default_rudder_max_angle)
        self._mass = get_default(mass, self._default_mass)

        self._rudder_angle = 0
        self.ang_vel = 0

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            initial_velocity=initial_velocity,
            parent=parent,
            coalition=coalition
        )
        self.facing.angle = self.velocity.angle
        self.add(GravityAffected)

        # game drag
        self._wh = self.size.x / self.size.y
        self._cd = 0.15 + (self.size.y / self.size.x) * 0.8
        
        # spawn graphics entity
        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs={"id": self.id, "cid": self.cid()},
            )
        )

    # region properties
    @property
    def mass(self) -> float:
        return self._mass

    @property
    def rudder_angle(self) -> float:
        return self._rudder_angle

    @rudder_angle.setter
    def rudder_angle(self, angle: float) -> None:
        self._rudder_angle = angle

    # endregion

    def _update_rudder(self, delta: float) -> None:
        """update rudder position"""

    def _update(self, delta: float) -> None:
        forward_force = Vec2()

        # common variables
        airflow_d = self.velocity.copy().normalize()
        right = self.facing.copy()
        right.angle += m.pi / 2
        q = self.velocity.length / 1000
        q *= q

        # drag force
        drag_force = airflow_d * (-self._cd * q)
        forward_force += drag_force

        # update rudder position
        self._update_rudder(delta)

        # rudder force
        rudder_force = q * self._rudder_size * self._rudder_angle * .3

        lever = self.size.x * 0.5
        rudder_torque = rudder_force * lever

        # stabilization
        side_slip = right.dot(airflow_d)
        stability_torque = side_slip * q * self._wh * 30

        # rudder drag
        turn_drag = airflow_d * (-q * self._rudder_size * abs(self._rudder_angle) * 0.3)
        forward_force += turn_drag

        # angular motion
        inertia = self.mass * self.size.x * self.size.x * .01
        damping = self.ang_vel * .8

        torque = stability_torque + rudder_torque - damping

        ang_acc = torque / inertia
        self.ang_vel += ang_acc * delta
        self.facing.angle += self.ang_vel * delta

        # ic(self.ang_vel, self.facing.angle, airflow_d.angle, stability_torque, damping, inertia)

        # ic(forward_force)

        # linear motion
        lift_force = right * (q * self._rudder_size * self._rudder_angle * 50)
        forward_force += lift_force
        self.acceleration += forward_force / self.mass
        super()._update(delta)

        # debugging
        self._buff.param0 = self.velocity.angle
        self._buff.param1 = self.velocity.length
