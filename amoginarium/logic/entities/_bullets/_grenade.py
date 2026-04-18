"""
amoginarium/logic/entities/_bullets/grenade.py

Project: amoginarium
Created: 31.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations
from ctypes import Array
import typing as tp
import numpy as np

from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared import base_entity_t, Coalitions
from amoginarium.shared.utility import Vec2
from amoginarium.shared import DummyCIDs

from .._base_entities import LogicGameEntity

from ._base_bullet import Bullet


class _GrenadeShrapnel(Bullet):
    _cid = DummyCIDs.base_bullet

    _default_size = 4
    _default_base_damage = 1

    __slots__ = ()


class Grenade(Bullet):
    # region ClassVars
    _cid = DummyCIDs.grenade
    _hp = 0.05

    _default_size = 32
    _default_base_damage = 0
    _default_ttl = 5
    _default_explosion_radius = 150
    _default_explosion_damage = 50

    _default_cluster_depth = 1
    _default_cluster_amount = 32
    _default_cluster_spread = np.pi * 2
    _default_cluster_bullet_type = _GrenadeShrapnel
    _default_cluster_step_inertia = 1000
    _default_cluster_step_explosion = 150
    _default_cluster_fuze_ttl_mult = .001
    _default_cluster_last_step_ttl = .2
    _default_cluster_size_mult = .1

    _bounce_friction: tp.ClassVar[float] = 0.7
    # endregion

    __slots__ = ()

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: LogicGameEntity,
            coalition: Coalitions,
            initial_position: Vec2,
            initial_velocity: Vec2,
            **kwargs: tp.Any,
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            **kwargs,
        )

    def _on_collision(self, event: CollisionEvent) -> None:
        self.position.x = event.position.x
        self.position.y = event.position.y

        self._collision = (event.other_entity, self.position.xy)

        vx = self.velocity.x
        vy = self.velocity.y
        nx = event.normal.x
        ny = event.normal.y

        dot_product = (vx * nx) + (vy * ny)

        if dot_product < 0:
            rx = vx - 2 * dot_product * nx
            ry = vy - 2 * dot_product * ny

            self.velocity.x = rx * self._bounce_friction
            self.velocity.y = ry * self._bounce_friction

            if ny < -0.5 and abs(self.velocity.y) < 30:
                self.velocity.y = 0

    def _update(self, delta: float):
        super()._update(delta)

    def kill(self, killed_by: tp.Any = ...):
        if killed_by is not ...:
            if issubclass(killed_by.__class__, Bullet):
                self._time_to_life = 0

        if self._time_to_life > 0:
            return False

        return super().kill(killed_by)
