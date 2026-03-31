"""
_bullets.py
31.03.2026

implements logic bullets

Author:
Nilusink
"""
from contextlib import suppress
from time import perf_counter
from ctypes import Array
import typing as tp
import numpy as np

from amoginarium.shared.utility import Vec2, multi_raycast_mask, is_related
from amoginarium.shared import base_entity_t, Coalitions, ProcessCommand
from amoginarium.shared import BaseCommandType, DummyCIDs
from amoginarium import pv

from ..audio import LargeExplosion
from ._logic_groups import Bullets, Updated, GravityAffected, CollisionDestroyed
from ._logic_groups import WallCollider
from ._base_entity import LogicGameEntity


SQR2 = np.sqrt(2)


class Bullet(LogicGameEntity):
    _base_damage: float = 1
    _hp: int = -1
    _weight: float | None = None

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
            target_pos: Vec2 = ...,
            size: Vec2 | int = 10,
            no_gravity=False,
            visibility_offset: float = 0,
    ) -> None:
        if not isinstance(size, Vec2):
            size = Vec2().from_cartesian(size, size)

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
        self._last_pos = self.position.copy()

        self.remove(Updated)
        if not no_gravity:
            self.add(GravityAffected)

        if not casing:
            self.add(Bullets, CollisionDestroyed)

        # spawn dummy
        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={"id": self.id, "cid": DummyCIDs.bullet}
        ))

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

        speed_mult = 1 + (
                (self.velocity.length - 1300) / x
        ) * .5
        damage = self._base_damage * speed_mult

        return damage

    @property
    def is_bullet(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        if self._weight:
            return self._weight

        return self._weight_from_size(self.size)

    @property
    def recoil_fac(self) -> float:
        return self.get_recoil_fac(self.weight, self.velocity.length)

    @property
    def last_pos(self) -> Vec2:
        return self._last_pos

    @classmethod
    def _weight_from_size(cls, size: Vec2 | float) -> float:
        if isinstance(size, Vec2):
            return size.length / 100

        return (size * SQR2) / 100

    @classmethod
    def get_weight(cls, size: Vec2 | float) -> float:
        if cls._weight:
            return cls._weight

        return cls._weight_from_size(size)

    @classmethod
    def get_recoil_fac(cls, weight: float, velocity: float) -> float:
        return (weight / 2.5) * (velocity / 10)

    def hit(self, _damage: float, hit_by: tp.Self = ...) -> None:
        if self._hp <= 0 or not issubclass(hit_by.__class__, Bullet):
            self.kill(killed_by=hit_by)

        else:
            self._hp -= _damage
            if self._hp <= 0:
                self.kill(killed_by=hit_by)

    def hit_someone(self, target_hp: float) -> None:
        self.kill()

    def update(self, delta):
        self._ttl -= delta
        self._visibility_offset -= delta

        if any([
            self._ttl <= 0,
            self.on_ground
        ]):
            if self.kill():
                return

        # double gravity (because why not)
        self.acceleration.y *= 2

        self._last_pos = self.position.copy()
        super().update(delta)
        self.facing.angle = self.velocity.angle

        # check if bullet has hit someone
        if self.velocity.length > 2000:
            entities_hit = multi_raycast_mask(
                self,
                Updated.sprites(),
                self._last_pos,
                self.position,
                10
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

    def kill(self, killed_by: tp.Self = ...) -> bool:
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
            # explosion.draw(
            #     delay=.05,
            #     size=Vec2().from_cartesian(
            #         self._explosion_radius * 2,
            #         self._explosion_radius * 2
            #     ),
            #     position=self.position.copy()
            # )

            if self._explosion_radius > 64:
                exp = LargeExplosion()
                exp.volume = .35
                exp.play()

            # sounds like shit
            # elif self._explosion_radius < 16:
            #     exp = SmallExplosion()
            #     exp.volume = .5
            #     exp.play()

        super().kill()
        return True
