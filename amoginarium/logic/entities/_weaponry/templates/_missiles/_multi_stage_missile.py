"""
_multi_stage_missile.py
05.05.2026

missile "bullet"

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared import Coalitions, base_entity_t, MissileCIDs
from amoginarium.shared.utility import Vec2

from ...._base import LogicGameEntity
from ._base_missile import BaseMissile


# params are: time for stage, thrust, fuel flow in weight / s
type crude_motor_stage_t = tuple[float, float, tp.Optional[float]]


class MultiStageMissile(BaseMissile):
    """
    thrust defined by stages

    ``flags[14]``: thrust active
    """

    __slots__ = (
        "__current_fuel_weight",
        "__current_thrust",
        "_stages",
        "__current_stage",
        "__current_stage_t"
    )

    _CID = MissileCIDs.multi_stage

    # region motor stages
    _default_motor_start: crude_motor_stage_t = (.5, 0)
    _default_motor_launch: crude_motor_stage_t = (1, 300, 50)
    _default_motor_accel: crude_motor_stage_t = (2, 100, 10)
    _default_motor_march: crude_motor_stage_t = (0, 0)
    _default_motor_inertial: crude_motor_stage_t = (0, 0)
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
        # calculate motor params
        self._stages = [
            self._default_motor_start,
            self._default_motor_launch,
            self._default_motor_accel,
            self._default_motor_march,
            self._default_motor_inertial,
        ]

        self.__current_fuel_weight = 0
        self.__current_stage = 0
        self.__current_stage_t = self._stages[0][0]
        # calculate fuel weight per stage
        for stage in self._stages:
            if len(stage) > 2:
                self.__current_fuel_weight += stage[0] * stage[2]

        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            initial_facing=initial_facing,
            rudder_size=rudder_size,
            rudder_max_angle=rudder_max_angle,
            fuel_mass=self.__current_fuel_weight,
            base_mass=base_mass,
            collision_exception_ids=collision_exception_ids,
            **kwargs
        )

    # region properties
    @property
    def _fuel_mass(self) -> float:
        return self.__current_fuel_weight

    @property
    def thrust(self) -> float:
        return self.__current_thrust

    # endregion

    def __update_stage(self, dt: float) -> None:
        """update thrust and fuel weight based on time delta"""
        if dt <= 0:
            return

        # if stage is -1 motor is done
        if self.__current_stage < 0:
            return

        # increment stage time
        self.__current_stage_t -= dt

        # increment thrust and weight
        self.__current_thrust = self._stages[self.__current_stage][1]
        self._set_bit("flags", 14, self.__current_thrust > 0)

        if len(self._stages[self.__current_stage]) > 2:
            self.__current_fuel_weight -= (
                    self._stages[self.__current_stage][2]
                    * dt
            )  # type: ignore

        # increment stage
        if self.__current_stage_t < 0:
            self.__current_stage += 1
            
            if len(self._stages) <= self.__current_stage:
                self.__current_fuel_weight = 0
                self.__current_thrust = 0
                self.__current_stage = -1
                self._set_bit("flags", 14, False)
                return

            # set next stage time (+ overflow from last stage)
            self.__current_stage_t = (
                self._stages[self.__current_stage][0] + self.__current_stage_t
            )

    def _update(self, delta: float) -> None:
        self.__update_stage(delta)
        super()._update(delta)
