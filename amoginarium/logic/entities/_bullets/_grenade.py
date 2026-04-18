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
from .. import GravityAffected

from .._collision.collision_manager import collision_manager
from .._collision.collision_relations import collision_group_grenades, collision_group_islands, collision_group_bullets, collision_group_players
from .._base_entities import LogicGameEntity
from ._base_bullet import Bullet

if tp.TYPE_CHECKING:
    from .._world import Island
    from .._player import Player


class _GrenadeShrapnel(Bullet):
    _cid = DummyCIDs.base_bullet

    _default_size = 4
    _default_base_damage = 1

    __slots__ = ()


class Grenade(Bullet):
    # region ClassVars
    _cid = DummyCIDs.grenade
    _default_hp = 0.05

    _default_size = 32
    _default_base_damage = 0
    _default_ttl = 500
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

    _collision_group = collision_group_grenades
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

    def __on_collision_island(self, event: CollisionEvent["island"]) -> None:
        self.position.x = event.position.x
        self.position.y = event.position.y

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

    def __on_collision_bullet(self, event: CollisionEvent[Bullet]) -> None:
        self.hit(event.other_entity.damage, event.other_entity)

    def __on_collision_player(self, event: CollisionEvent["Player"]) -> None:
        self.add_velocity(event.other_entity.velocity)
        if self._lifetime > 0.5:
            self.add_velocity(Vec2().from_cartesian(0, -200))

    def _on_collision(self, event: CollisionEvent) -> None:
        if event.group_id == collision_group_islands:
            self.__on_collision_island(event)
        elif event.group_id == collision_group_bullets:
            self.__on_collision_bullet(event)
        elif event.group_id == collision_group_players:
            self.__on_collision_player(event)

    def _update(self, delta: float):
        if collision_group_islands in self.active_normals.keys():
            for n in self.active_normals[collision_group_islands]:
                if n.y < -0.5:
                    self.acceleration.y = 0
                    if self.velocity.y > 0:
                        self.velocity.y = 0
                    self.velocity.x *= 0.98  # slide friction
                elif n.y > 0.5:
                    if self.velocity.y < 0:
                        self.velocity.y = 0
                if abs(n.x) > 0.5 and self.velocity.x * n.x < 0:
                    self.velocity.x = 0

        super()._update(delta)

    def kill(self, killed_by: tp.Any = ...):
        if killed_by is not ...:
            if issubclass(killed_by.__class__, Bullet):
                self._time_to_life = 0

        if self._time_to_life > 0:
            return False

        return super().kill(killed_by)

    def add_velocity(self, value: Vec2) -> None:
        """
        add velocity to the entity and guarantee that it will be valid (for short bursts)
        :param value: 2D velocity to add
        """
        x = value.x
        y = value.y

        if collision_group_islands in self.active_normals.keys():
            for n in self.active_normals[collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._velocity_to_add.x += x
        self._velocity_to_add.y += y

    def add_acceleration(self, value: Vec2) -> None:
        """
        add acceleration to the entity and guarantee that it will be valid (for long accelerations)
        :param value: 2D acceleration to add
        """
        x = value.x
        y = value.y

        if collision_group_islands in self.active_normals.keys():
            for n in self.active_normals[collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._acceleration_to_add.x += x
        self._acceleration_to_add.y += y
