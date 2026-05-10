"""
_guided_multi_stage_missile.py
10.05.2026

a multi-stage missile with guidance

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
from icecream import ic
import typing as tp
import numpy as np
import math as m

from amoginarium.shared.utility import Vec2, M_2_PI, PIDController, normalize_angle_neg
from amoginarium.shared import MissileCIDs, base_entity_t, Coalitions

from ...._base import LogicGameEntity
from .._weapon_actors.sensors import BaseWeaponsSensor
from ._multi_stage_missile import MultiStageMissile


class GuidedMultiStageMissile(MultiStageMissile):
    """
    a multi-stage missile with guidance
    """

    _CID = MissileCIDs.guided_multi_stage

    # region ClassVars
    _sensors_list: tp.ClassVar[list[dict[str, tp.Any]]] = []
    
    _default_guidance_max_alpha: tp.ClassVar[float] = np.inf
    _default_guidance_function_delay: tp.ClassVar[float] = 0
    # endregion

    # region InstanceVars
    _sensor: BaseWeaponsSensor
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
            **kwargs
        )
        
        # set defaults
        sensor_args = self._sensors_list[0].copy()
        sensor_type = sensor_args.pop("type")

        # create PID controller
        self._pid = PIDController(4, 0, 1.5)

        self._sensor = sensor_type(parent=self, **sensor_args)

    @property
    def alpha(self) -> float:
        return normalize_angle_neg(self._alpha)

    def _kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> bool:
        super()._kill(killed_by)
        self._sensor.kill(self)

    def __update_guidance(self, delta: float) -> None:
        target_delta = self._sensor.get_target()

        if target_delta:
            facing = self.velocity.copy().normalize()
            target = target_delta.copy().normalize()

            # calculate angular error
            error = -m.atan2(
                facing.x * target.y - facing.y * target.x,
                facing.x * target.x + facing.y * target.y,
            )

            # PD-controller
            rudder = error * 1.5 - (-self.ang_vel * .5)

            # clamp rudder
            rudder = min(max(rudder, -self._rudder_max_angle), self._rudder_max_angle)

            if abs(self.alpha) < self._default_guidance_max_alpha:
                self._rudder_angle = rudder

            else:
                self._rudder_angle = 0

            self._target_pos = self.position + target_delta

        else:
            self._rudder_angle = 0

    def _update(self, delta: float) -> None:
        super()._update(delta)

        # update sensor
        self._sensor.update()
        
        # update guidance
        if self._lifetime >= self._default_guidance_function_delay:
            self.__update_guidance(delta)
