"""
_exacto.py
17.04.2026

Implements both bullet + weapon for the exacto system

Author:
Nilusink
"""

from ctypes import Array
from icecream import ic
import typing as tp
import math as m

from amoginarium.shared.utility import Vec2, normalize_angle, multi_raycast_mask
from amoginarium.shared import base_entity_t, Coalitions
from amoginarium import pv

from ._logic_groups import Updated, Walls
from ._base_entity import LogicGameEntity
from ._aerodynamic_entity import AerodynamicEntity


class ExactoBullet(AerodynamicEntity):

    __slots__ = ("_target_callback", "_guidance_delay")
    
    _default_mass = .1
    _default_rudder_size = 1
    _default_rudder_max_angle = m.pi

    _default_guidance_delay: float = .01
    
    _max_alpha: float = .002

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        target_callback: tp.Callable[[], Vec2],
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            coalition=coalition,
            initial_position=initial_position,
            initial_velocity=initial_velocity,
            size=Vec2().from_cartesian(15, 5),
            **kwargs
        )
        self._target_callback = target_callback
        self._guidance_delay = self._default_guidance_delay

    def _update_rudder(self, delta: float) -> None:
        if self._guidance_delay > 0:
            self._guidance_delay -= delta
            return

        target = self._target_callback()

        delta_pos = self.position - target
        delta_angle = self.velocity.angle - delta_pos.angle

        # normalize to +/- m.pi
        delta_angle = (delta_angle + m.pi) % (2 * m.pi) - m.pi

        # calculate rudder pos
        abs_ang = abs(delta_angle)
        if abs(self.alpha) < self._max_alpha:
            self._rudder_angle = (delta_angle // abs_ang) * min(
                (self._rudder_max_angle, abs_ang * abs_ang)
            )

        else:
            self._rudder_angle = 0
        
        # ic(self._rudder_angle, delta_angle)

    # def _update(self, delta: float) -> None:
    #     multi_raycast_mask(
    #         self,
    #         Walls.spriteS(),
    #         self.position,
    #         Vec2().from_polar(self.facing.angle, self._max_range),
    #     )
