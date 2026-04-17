"""
_bullets.py
31.03.2026

implements logic bullets

Author:
Nilusink
"""
from contextlib import suppress
from types import EllipsisType
from time import perf_counter
from ctypes import Array
from icecream import ic
import typing as tp
import pygame as pg
import numpy as np

from amoginarium.shared.cd_old import collision_detection_aabb_aabb_minkowski_raycast
from amoginarium.shared.utility import Vec2, multi_raycast_mask, is_related, convert_coord
from amoginarium.shared import base_entity_t, Coalitions, ProcessCommand
from amoginarium.shared import BaseCommandType, DummyCIDs
from amoginarium import pv


from ..audio import LargeExplosion, DistantPop
from ._logic_groups import Bullets, Updated, GravityAffected, CollisionDestroyed
from ._logic_groups import WallCollider, WallBouncer, Walls
from ._base_entity import LogicGameEntity
from ._collision_groups import GridCell, GridSystem
from ._collisions import collision_manager, collision_group_bullets, collision_group_islands, CollisionEvent
from ._debug_rendering import DebugRenderingEntity

from ._island import Island

SQR2 = np.sqrt(2)


class Bullet(LogicGameEntity):
    """
    basic logic bullet
    """
    __slots__ = [
        "_casing", "_ttl", "_o_ttl", "_initial_velocity", "_explosion_radius",
        "_explosion_damage", "_target_pos", "_visibility_offset", "_start_time",
        "_base_damage", "_last_pos", "_collision_id", "_collision", "_debug_rendering"
    ]

    _base_damage: float
    _hp: int = -1
    _weight: float | None = None
    _cid = DummyCIDs.base_bullet

    _cells: list[GridCell]

    _collision_id: int
    _collision: bool

    _debug_rendering: DebugRenderingEntity | None

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: LogicGameEntity,
            coalition: Coalitions,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 1,
            casing: bool = False,
            time_to_life: float = 2,
            explosion_radius: float = -1,
            explosion_damage: float = 0,
            target_pos: Vec2 | EllipsisType = ...,
            size: Vec2 | int = 10,
            no_gravity=False,
            visibility_offset: float = 0,
    ) -> None:
        if not isinstance(size, Vec2):
            size: Vec2 = Vec2().from_cartesian(size, size)  # type: ignore

        self._casing = casing
        self._base_damage = base_damage
        self._ttl = time_to_life
        self._o_ttl = time_to_life
        self._initial_velocity = initial_velocity
        self._explosion_radius = explosion_radius
        self._explosion_damage = explosion_damage
        self._target_pos = target_pos
        self._visibility_offset = visibility_offset
        self._start_time = perf_counter()

        # load textures
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=initial_position.copy(),
            initial_velocity=initial_velocity.copy(),
            coalition=coalition,
            parent=parent
        )
        runtime_buffer[self.id].param0 = explosion_radius
        self._last_pos = self.position.copy()

        self._collision_id = collision_manager.register_entity(collision_group_bullets, self,
                                                               self.position - (self.size / 2), self.size)
        # self._debug_rendering = DebugRenderingEntity(
        #     runtime_buffer=runtime_buffer,
        #     position=self.position - (self.size / 2),
        #     size=self.size
        # )
        self._collision = False

        self.remove(Updated)
        if not no_gravity:
            self.add(GravityAffected)

        if not casing:
            self.add(Bullets, CollisionDestroyed)

        # spawn dummy
        kwargs = {
            "id": self.id,
            "cid": self.cid(),
            "spawn_time": self._start_time,
            "visibility_offset": self._visibility_offset,
        }
        if not isinstance(self._target_pos, EllipsisType):
            kwargs["target_pos"] = self._target_pos.xy  # ignore: type

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs=kwargs
        ))

    # region properties
    @property
    def on_ground(self) -> bool:
        return self._collision is not False

    @property
    def damage(self) -> float:
        """
        get bullet damage
        """
        if self._casing:
            return 0

        # calculate damage based on base_damage and velocity
        x = max(self._initial_velocity.length, 800)

        speed_mult = 1 + (
                (self.velocity.length - 1300) / x
        ) * .5
        damage = self._base_damage * speed_mult

        return damage

    @property
    def is_bullet(self) -> bool:
        """yes"""
        return True

    @property
    def weight(self) -> float:
        """bullet weight (depending on size if not specified)"""
        if self._weight:
            return self._weight

        return self._weight_from_size(self.size)

    @property
    def recoil_fac(self) -> float:
        """weapons recoil \"dampener\""""
        return self.get_recoil_fac(self.weight, self.velocity.length)

    @property
    def last_pos(self) -> Vec2:
        """bullets previous position"""
        return self._last_pos

    # endregion

    # region class methods
    @classmethod
    def _weight_from_size(cls, size: Vec2 | float) -> float:
        """calculate weight from size"""
        if isinstance(size, Vec2):
            return size.length / 100

        return (size * SQR2) / 100

    @classmethod
    def get_weight(cls, size: Vec2 | float) -> float:
        """bullet weight (depending on size if not specified)"""
        if cls._weight:
            return cls._weight

        return cls._weight_from_size(size)

    @classmethod
    def get_recoil_fac(cls, weight: float, velocity: float) -> float:
        """weapons recoil \"dampener\""""
        return (weight / 2.5) * (velocity / 10)

    # endregion

    def hit(self, _damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        """bullet was hit by someone"""
        if self._hp <= 0 or not issubclass(hit_by.__class__, Bullet):
            self.kill(killed_by=hit_by)

        else:
            self._hp -= _damage
            if self._hp <= 0:
                self.kill(killed_by=hit_by)

    def hit_someone(self, target_hp: float) -> None:
        """bullet has hit someone else"""
        self.kill()

    def _collide_with_island(self, island: Island) -> tuple[float, float] | None:
        for island_rect in island.collision_rects:
            result = collision_detection_aabb_aabb_minkowski_raycast(
                self_size=(0, 0),
                self_position_old=self.position.xy,
                self_position_new=self._last_pos.xy,
                other_size=island_rect.size,
                other_position_old=(island_rect.x, island_rect.y),
                other_position_new=(island_rect.x, island_rect.y),
            )
            if result is not None:
                return result[0]

    def _on_collision(self, event: CollisionEvent) -> None:
        """
        Callback fired by the Cython CollisionManager when this bullet hits something.
        """
        collision_manager.delete_entity(collision_group_bullets, self._collision_id)

        # 1. Snap the bullet exactly to the point of impact to prevent tunneling visually
        self.position.x = event.position.x
        self.position.y = event.position.y

        # 2. Store the collision state so properties like `on_ground` still work
        self._collision = (event.other_entity, self.position.xy)

        # 3. Deal direct damage to the entity we hit (if it can take damage)
        other = event.other_entity
        try:
            dmg = self.damage
        except AttributeError:
            dmg = 0

        if dmg > 0 and hasattr(other, "hit"):
            other.hit(dmg, hit_by=self)

        # 4. Destroy the bullet (this triggers your explosion/recoil logic in `kill()`)
        self.kill(killed_by=other)

    def on_collision(self, event: CollisionEvent) -> None:
        self._on_collision(event)

    def update(self, delta):
        self._ttl -= delta
        self._visibility_offset -= delta

        # double gravity (because why not)
        self.acceleration.y *= 2

        self._last_pos = self.position.copy()

        if any([
            self._ttl <= 0,
            self.on_ground  # This will be True if on_collision was triggered
        ]):
            if self.kill():
                return

        super().update(delta)
        self.facing.angle = self.velocity.angle

        self._collision = False
        collision_manager.update_entity(collision_group_bullets, self._collision_id,
                                        self.position - (self.size / 2), self.size)
        # self._debug_rendering.position = self.position - (self.size / 2)

    def kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> bool:
        if all([
            self._casing,
            not Updated.out_of_bounds_x(self)
        ]):
            self.position.y -= self.size.y / 2
            self.remove(
                Updated,
                CollisionDestroyed,
                GravityAffected
            )
            return True

        # bullet hit knockback
        if all([
            killed_by != self,
            not issubclass(killed_by.__class__, Bullet)
        ]):
            if hasattr(killed_by, "_impulse_resistance_factor"):
                recoil = Vec2().from_polar(
                    self.velocity.angle,
                    self.recoil_fac
                ) * killed_by._impulse_resistance_factor

                killed_by.add_velocity(recoil)

        # explode
        if self._explosion_radius > 0:
            for d, entity in CollisionDestroyed.get_entities_in_circle(
                    self.position,
                    self._explosion_radius * 2
            ):
                if all([
                    entity != self,
                    not issubclass(entity.__class__, Bullet)
                ]):
                    if hasattr(entity, "hit"):
                        entity.hit(
                            (1 - .8 * d / (self._explosion_radius*2))
                            * self._explosion_damage,
                            hit_by=self
                        )

                    if hasattr(entity, "_impulse_resistance_factor"):
                        d -= entity.size.length
                        d = max(d, 1)
                        delta = entity.position - self.position
                        delta = delta.normalize() \
                            * entity._impulse_resistance_factor \
                            * (
                                1 - d / (self._explosion_radius * 1)
                            ) * self._explosion_damage * 4

                        entity.add_velocity(delta)
            #

            if self._explosion_radius > 64:
                exp = LargeExplosion()
                exp.volume = .35
                exp.play(pos=self.position)

            # sounds like shit
            elif self._explosion_radius < 16:
                exp = DistantPop()
                exp.set_volume(.8, .3)
                exp.play(pos=self.position)

        super().kill()

        return True


class MortarShell(Bullet):
    _hp = .5
    _weight = 8
    _cid = DummyCIDs.mortar_bullet

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: LogicGameEntity,
            coalition: Coalitions,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 40,
            casing: bool = False,
            time_to_life: float = 10,
            explosion_radius: float = 200,
            explosion_damage: float = 50,
            target_pos: Vec2 | EllipsisType = ...,
            size=Vec2().from_cartesian(40, 20),
            no_gravity=False,
            **kwargs
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            base_damage,
            casing,
            time_to_life,
            explosion_radius,
            explosion_damage,
            target_pos,
            size,
            no_gravity,
            **kwargs,
        )


class Grenade(Bullet):
    _hp = .05
    _bounce_friction = .7
    _cid = DummyCIDs.grenade

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: LogicGameEntity,
            coalition: Coalitions,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 0,
            casing: bool = False,
            time_to_life: float = 5,
            explosion_radius: float = 150,
            explosion_damage: float = 50,
            target_pos: Vec2 | EllipsisType = ...,
            size=20,
            no_gravity=False,
            **kwargs
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            base_damage,
            casing,
            time_to_life,
            explosion_radius,
            explosion_damage,
            target_pos,
            size,
            no_gravity,
            **kwargs
        )
        self.in_wall = None

    def _on_collision(self, event: CollisionEvent) -> None:
        self.position.x = event.position.x + self.size.x / 2
        self.position.y = event.position.y + self.size.y / 2

        self.in_wall = event.normal
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

        collision_manager.update_entity(
            collision_group_bullets,
            self._collision_id,
            (self.position + event.normal) - self.size / 2,
            self.size
        )

    def _update(self, delta):
        self.in_wall = None
        super()._update(delta)

    def kill(self, killed_by=...):
        if killed_by is not ...:
            if issubclass(killed_by.__class__, Bullet):
                self._ttl = 0

        if self._ttl > 0:
            return False

        return super().kill(killed_by)


class SniperBullet(Bullet):
    _weight = 5


class FlakBullet(Bullet):
    _weight = 5


class CRAMBullet(Bullet):
    _cid = DummyCIDs.cram
