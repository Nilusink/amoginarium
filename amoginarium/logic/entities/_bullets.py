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
from icecream import ic
from ctypes import Array
import numpy as np

from amoginarium.shared.utility import Vec2, multi_raycast_mask, is_related
from amoginarium.shared.utility import get_default
from amoginarium.shared import base_entity_t, Coalitions, ProcessCommand
from amoginarium.shared import BaseCommandType, DummyCIDs
from amoginarium import pv

from ..audio import LargeExplosion, DistantPop
from ._logic_groups import Bullets, Updated, GravityAffected, CollisionDestroyed
from ._logic_groups import WallCollider, WallBouncer
from ._base_entity import LogicGameEntity


SQR2 = np.sqrt(2)


class Bullet(LogicGameEntity):
    """
    basic logic bullet
    """
    __slots__ = [
        "_casing", "_ttl", "_o_ttl", "_initial_velocity", "_explosion_radius",
        "_explosion_damage", "_target_pos", "_visibility_offset", "_start_time",
        "_base_damage", "_last_pos"
    ]

    _base_damage: float
    _hp: int = -1
    _weight: float | None = None
    _cid = DummyCIDs.base_bullet

    _default_base_damage: float = 1
    _default_ttl: float = 2
    _default_explosion_radius: float = -1
    _default_explosion_damage: float = 0
    _default_cluster_depth: int = 0
    _default_cluster_amount: int = 0
    _default_cluster_spread: float = np.pi / 4
    _default_cluster_fuze_mult: float = .5
    _default_size: Vec2 | int = 10
    _default_visibility_offset: float = 0
    _default_invincibility_offset: float = 0

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        *,
        casing: bool = False,
        no_gravity: bool = False,
        base_damage: float | EllipsisType = ...,
        time_to_life: float | EllipsisType = ...,
        explosion_radius: float | EllipsisType = ...,
        explosion_damage: float | EllipsisType = ...,
        cluster_depth: int | EllipsisType = ...,
        cluster_amount: int | EllipsisType = ...,
        cluster_spread_angle: float | EllipsisType = ...,
        cluster_fuze_mult: float | EllipsisType = ...,
        target_pos: Vec2 | EllipsisType = ...,
        size: Vec2 | int | EllipsisType = ...,
        visibility_offset: float | EllipsisType = ...,
        invincibility_offset: float | EllipsisType = ...
    ) -> None:
        self._start_time = perf_counter()

        if not isinstance(size, Vec2):
            size: Vec2 = Vec2().from_cartesian(size, size)  # type: ignore

        # required params
        self._initial_velocity = initial_velocity

        self._casing = casing

        # default params
        self._base_damage = get_default(base_damage, self._default_base_damage)
        self._ttl = get_default(time_to_life, self._default_ttl)
        self._o_ttl = self._ttl
        self._explosion_radius = get_default(
            explosion_radius, self._default_explosion_radius
        )
        self._explosion_damage = get_default(
            explosion_damage, self._default_explosion_damage
        )
        self._cluster_depth = get_default(cluster_depth, self._default_cluster_depth)
        self._cluster_amount = get_default(cluster_amount, self._default_cluster_amount)
        self._cluster_spread = get_default(
            cluster_spread_angle, self._default_cluster_spread
        )
        self._cfm = get_default(cluster_fuze_mult, self._default_cluster_fuze_mult)
        self._visibility_offset = get_default(
            visibility_offset, self._default_visibility_offset
        )
        self._invincibility_offset = get_default(
            invincibility_offset, self._default_invincibility_offset
        )

        # optional params
        if isinstance(target_pos, EllipsisType):
            self._target_pos = ...
            self._o_dist = 0

        else:
            self._target_pos = target_pos.copy()
            self._o_dist = (initial_position - self._target_pos).length

        # load textures
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=initial_position.copy(),
            initial_velocity=initial_velocity.copy(),
            coalition=coalition,
            parent=parent,
        )
        runtime_buffer[self.id].param0 = self._explosion_radius
        self._last_pos = self.position.copy()

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

        pv.COQ.put(ProcessCommand(type=BaseCommandType.spawn_dummy, kwargs=kwargs))

    # region properties
    @property
    def on_ground(self) -> bool:
        return WallCollider.collides_with(self)

    @property
    def damage(self) -> float:
        """
        get bullet damage
        """
        if self._casing:
            return 0

        # calculate damage based on base_damage and velocity
        x = max(self._initial_velocity.length, 800)

        speed_mult = 1 + ((self.velocity.length - 1300) / x) * 0.5
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

    def _update(self, delta):
        self._ttl -= delta
        self._visibility_offset -= delta
        self._invincibility_offset -= delta

        if any([self._ttl <= 0, self.on_ground]):
            if self.kill():
                return

        # double gravity (because why not)
        self.acceleration.y *= 2

        self._last_pos = self.position.copy()
        super()._update(delta)
        self.facing.angle = self.velocity.angle

        # check if bullet has hit someone
        if self.velocity.length > 2000:
            entities_hit = multi_raycast_mask(
                self, CollisionDestroyed.sprites(), self._last_pos, self.position, 10
            )

            for other, pos in entities_hit:
                if not is_related(self, other):
                    self.position = pos

                    try:
                        dmg = other.damage

                    except AttributeError:
                        dmg = 0

                    self.hit(dmg, other)

                    with suppress(AttributeError):
                        hp = other.hp
                        if dmg != 0:
                            self.hit_someone(target_hp=hp)

                    # bullet is sprite
                    try:
                        dmg = self.damage

                    except AttributeError:
                        dmg = 0

                    with suppress(AttributeError):
                        other.hit(dmg, self)

        # check if cluster detonate
        if self._cluster_depth > 0:
            if (self.position - self._target_pos).length < self._o_dist * self._cfm:
                self.kill(self)

        # update velocity
        self._runtime_buffer[self.id].param1 = self.velocity.length

    def kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> bool:
        if not isinstance(killed_by, EllipsisType):
            if self._invincibility_offset > 0 and killed_by.parent == self.parent:
                return True

        # check if casing
        if all([self._casing, not Updated.out_of_bounds_x(self)]):
            self.position.y -= self.size.y / 2
            self.remove(Updated, CollisionDestroyed, GravityAffected)
            return True

        # bullet hit knockback
        if all([killed_by != self, not issubclass(killed_by.__class__, Bullet)]):
            if hasattr(killed_by, "_impulse_resistance_factor"):
                recoil = (
                    Vec2().from_polar(self.velocity.angle, self.recoil_fac)
                    * killed_by._impulse_resistance_factor
                )

                killed_by.add_velocity(recoil)

        # cluster
        if self._cluster_depth > 0 and self._cluster_amount > 0 and killed_by == self:
            if self._cluster_amount > 1:
                angle_spread = self._cluster_spread / (self._cluster_amount - 1)

                current_angle = self.velocity.angle - self._cluster_spread / 2
                for bi in range(self._cluster_amount):
                    self.__class__(
                        self._runtime_buffer,
                        self.parent,
                        self.coalition,
                        self.position.copy(),
                        Vec2().from_polar(current_angle, self.velocity.length),
                        base_damage=self._base_damage,
                        time_to_life=self._ttl,
                        explosion_radius=self._explosion_radius,
                        explosion_damage=self._explosion_damage,
                        cluster_depth=self._cluster_depth-1,
                        cluster_amount=self._cluster_amount,
                        cluster_spread_angle=self._cluster_spread,
                        target_pos=self._target_pos,
                        size=self.size.copy(),
                        invincibility_offset=(self.size.x / self.velocity.length) * 3,
                    )
                    current_angle += angle_spread

        # explode (only if not cluster)
        elif self._explosion_radius > 0:
            for d, entity in CollisionDestroyed.get_entities_in_circle(
                self.position, self._explosion_radius * 2
            ):
                if all([entity != self, not issubclass(entity.__class__, Bullet)]):
                    if hasattr(entity, "hit"):
                        entity.hit(
                            (1 - 0.8 * d / (self._explosion_radius * 2))
                            * self._explosion_damage,
                            hit_by=self,
                        )

                    if hasattr(entity, "_impulse_resistance_factor"):
                        d -= entity.size.length
                        d = max(d, 1)
                        delta = entity.position - self.position
                        delta = (
                            delta.normalize()
                            * entity._impulse_resistance_factor
                            * (1 - d / (self._explosion_radius * 1))
                            * self._explosion_damage
                            * 4
                        )

                        entity.add_velocity(delta)
            #

            if self._explosion_radius > 64:
                exp = LargeExplosion()
                exp.volume = 0.35
                exp.play(pos=self.position)

            # sounds like shit
            elif self._explosion_radius < 16:
                exp = DistantPop()
                exp.set_volume(0.8, 0.3)
                exp.play(pos=self.position)

        else:
            ic(self._explosion_radius)


        super().kill()
        return True


class MortarShell(Bullet):
    _hp = .5
    _weight = 8
    _cid = DummyCIDs.mortar_bullet

    _default_base_damage = 40
    _default_ttl = 10
    _default_explosion_radius = 150
    _default_explosion_damage = 50
    _default_size = Vec2().from_cartesian(40, 20)

    _default_cluster_depth = 2
    _default_cluster_amount = 3

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            **kwargs,
        )


class Grenade(Bullet):
    _hp = .05
    _bounce_friction = .7
    _cid = DummyCIDs.grenade

    _default_base_damage = 0
    _default_ttl = 5
    _default_explosion_radius = 150
    _default_explosion_damage = 50
    _default_size = 20

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            **kwargs,
        )

        self.in_wall = None
        self.add(WallBouncer)

    def _update(self, delta):
        if self.in_wall is not None:
            pi4 = np.pi / 4
            if 7 * pi4 <= self.in_wall.angle or self.in_wall.angle < pi4:
                self.acceleration.y = 0

        super()._update(delta)

    def kill(self, killed_by=...):
        # can only be killed by bullets and ttl
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

    # _default_cluster_depth = 1
    # _default_cluster_amount = 3
    # _default_cluster_fuze_mult = .06
    # _default_cluster_spread = .6
