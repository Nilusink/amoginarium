"""
amoginarium/logic/entities/_bullets/grenade.py.

Project: amoginarium
Created: 31.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

import numpy as np

from amoginarium.shared import DummyCIDs
from amoginarium.shared.utility import Vec2

from ...._base import GameCollisions
from ...templates import Bullet

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, Coalitions
    from amoginarium.shared.collision_detection import CollisionEvent

    from ...._base import LogicGameEntity
    from ...._items import Shield
    from ...._player import Player
    from ...._world import Island


class _GrenadeShrapnel(Bullet):
    _CID = DummyCIDs.base_bullet

    _default_size = 4
    _default_base_damage = 1

    _col_expection_grenade_cluster = GameCollisions.add_exception()
    __slots__ = ()

    def __init__(self, *args, **kwargs) -> None:
        kwargs["collision_exception_ids"] = [
            _GrenadeShrapnel._col_expection_grenade_cluster
        ]
        super().__init__(*args, **kwargs)


class Grenade(Bullet):
    # region ClassVars
    _CID = DummyCIDs.grenade
    _default_hp = 0.05

    _default_size = 32
    _default_base_damage = 0
    _default_ttl = 5
    _default_explosion_radius = 150
    _default_explosion_damage = 50
    _default_recoil_factor = 0.5

    _default_cluster_depth = 1
    _default_cluster_amount = 32
    _default_cluster_spread = np.pi * 2
    _default_cluster_bullet_type = _GrenadeShrapnel
    _default_cluster_step_inertia = 1000
    _default_cluster_step_explosion = 150
    _default_cluster_fuze_ttl_mult = 0.001
    _default_cluster_last_step_ttl = 0.2
    _default_cluster_size_mult = 0.1

    _bounce_friction: tp.ClassVar[float] = 0.7

    _DEFAULT_COLLISION_EXCEPTION_ROOT = True
    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_grenades
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

    def __on_collision_island(self, event: CollisionEvent[Island]) -> None:
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

    def __on_collision_player(self, event: CollisionEvent[Player]) -> None:
        if self._lifetime > 0.5:
            self.add_velocity(event.other_entity.velocity)
            self.add_velocity(Vec2().from_cartesian(0, -200))

    def __on_collision_shield(self, event: CollisionEvent[Shield]) -> None:
        self.position.x = event.position.x
        self.position.y = event.position.y

        # Calculate relative velocity (Grenade - Shield)
        vx = self.velocity.x - event.other_entity.parent.velocity.x
        vy = self.velocity.y - event.other_entity.parent.velocity.y
        nx, ny = event.normal.x, event.normal.y

        # Calculate dot product of relative velocity and surface normal
        dot_product = (vx * nx) + (vy * ny)

        # If moving towards the shield surface (relatively), reflect the velocity
        if dot_product < 0:
            # Reflection vector: R = V - 2 * (V . N) * N
            rx = vx - 2 * dot_product * nx
            ry = vy - 2 * dot_product * ny

            # Apply bounce friction and restore world-space velocity by adding shield velocity back
            self.velocity.x = (
                rx * self._bounce_friction
            ) + event.other_entity.parent.velocity.x
            self.velocity.y = (
                ry * self._bounce_friction
            ) + event.other_entity.parent.velocity.y
        else:
            # If already moving away but still colliding, ensure the shield's velocity is inherited
            self.velocity.x += event.other_entity.parent.velocity.x
            self.velocity.y += event.other_entity.parent.velocity.y

    def _collision_start(self, events: list[CollisionEvent]) -> list[bool] | None:
        for event in events:
            if event.group_id == GameCollisions.collision_group_islands:
                self.__on_collision_island(event)
            elif event.group_id == GameCollisions.collision_group_bullets:
                self.__on_collision_bullet(event)
            elif event.group_id == GameCollisions.collision_group_players:
                self.__on_collision_player(event)
            elif event.group_id == GameCollisions.collision_group_shields:
                self.__on_collision_shield(event)
        if event.group_id == GameCollisions.collision_group_shields:
            return [False for _ in events]
        return None

    def _update(self, delta: float) -> None:
        if GameCollisions.collision_group_islands in self._active_normals:
            for n in self._active_normals[GameCollisions.collision_group_islands]:
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

    def _kill(self, killed_by: tp.Any = ...):
        if killed_by is not ... and issubclass(killed_by.__class__, Bullet):
            self._time_to_life = 0

        if self._time_to_life > 0:
            return False

        return super()._kill(killed_by)

    def add_velocity(self, value: Vec2) -> None:
        """
        Add velocity to the entity and guarantee that it will be valid (for short bursts)
        :param value: 2D velocity to add.
        """
        x = value.x
        y = value.y

        if GameCollisions.collision_group_islands in self._active_normals:
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._velocity_to_add.x += x
        self._velocity_to_add.y += y

    def add_acceleration(self, value: Vec2) -> None:
        """
        Add acceleration to the entity and guarantee that it will be valid (for long accelerations)
        :param value: 2D acceleration to add.
        """
        x = value.x
        y = value.y

        if GameCollisions.collision_group_islands in self._active_normals:
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._acceleration_to_add.x += x
        self._acceleration_to_add.y += y
