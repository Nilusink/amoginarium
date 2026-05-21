"""
Base class for bullet entities handling physics, collisions, and clustering.

Path: amoginarium/logic/entities/_weaponry/templates/_bullets/_base_bullet.py
Project: amoginarium
Created: 31.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import inspect
import typing as tp
from time import perf_counter
from types import EllipsisType

import numpy as np
from icecream import ic

from amoginarium import pv
from amoginarium.shared import BaseCommandType, DummyCIDs, ProcessCommand
from amoginarium.shared.audio import DistantPop, LargeExplosion
from amoginarium.shared.debugging import print_ic_style
from amoginarium.shared.utility import get_default, Vec2

from ...._base import BaseGroup, Bullets, GameCollisions
from ...._base import GravityAffected, LogicGameEntity, Updated
from .._weapon_actors.fuzes import FUZES

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, CIDType, Coalitions, MurderViable
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionExceptionIDType
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from ...._items import Shield
    from ...._player import Player
    from ...._world import Island
    from ..._definitions import Grenade
    from .._turrets import BaseTurret, RideableTurret
    from .._weapon_actors.fuzes import BaseFuze
    from ._aerodynamic_entity import AerodynamicEntity


SQR2: tp.Final[np.float64] = np.sqrt(2)


class Bullet(LogicGameEntity):
    """
    Base logic bullet entity handling physics, collision, and clustering.
    Manages lifecycle states including Time-To-Life, explosive payloads, and
    recursive cluster fragmentation.
    """

    # region ClassVars
    _CID: tp.ClassVar[CIDType] = DummyCIDs.base_bullet

    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionGroupIDType] = (
        GameCollisions.collision_group_bullets
    )

    _default_hp: tp.ClassVar[int] = -1

    _default_base_damage: tp.ClassVar[float] = 1
    _default_ttl: tp.ClassVar[float] = 2
    _default_explosion_radius: tp.ClassVar[float] = -1
    _default_explosion_damage: tp.ClassVar[float] = 0
    _default_cluster_depth: tp.ClassVar[int] = 0
    _default_cluster_amount: tp.ClassVar[int] = 0
    _default_cluster_spread: tp.ClassVar[float] = np.pi / 4
    _default_cluster_chain_ttl: tp.ClassVar[bool] = True
    _default_cluster_step_explosion: tp.ClassVar[float] = 10
    _default_cluster_size_mult: tp.ClassVar[float] = 1
    _default_cluster_last_step_ttl: tp.ClassVar[float] = -1
    _default_cluster_bullet_type: tp.ClassVar[type[Bullet] | EllipsisType] = ...
    _default_cluster_step_inertia: tp.ClassVar[float] = 0
    _default_size: tp.ClassVar[Vec2 | int] = 10
    _default_visibility_offset: tp.ClassVar[float] = 0
    _default_invincibility_offset: tp.ClassVar[float] = 0
    _default_weight: float = None

    _default_fuze: tp.ClassVar = []
    # endregion

    __slots__ = (
        "_casing",
        "_time_to_life",
        "_o_time_to_life",
        "_initial_velocity",
        "_explosion_radius",
        "_explosion_damage",
        "_target_pos",
        "_visibility_offset",
        "_start_time",
        "_base_damage",
        "_last_pos",
        "_cluster_depth",
        "_cluster_amount",
        "_cluster_spread",
        "_o_dist",
        "_invincibility_offset",
        "_coll_sibling",
        "_cluster_step_explosion",
        "_cluster_size_mult",
        "_cluster_last_step_ttl",
        "_cluster_bullet_type",
        "_cluster_step_inertia",
        "_hp",
        "_cluster_args",
        "_weight",
        "_left_root",
        "_initial_root_collision_exception",
        "_root_entity",
    )

    # region InstanceVars
    _start_time: float
    _initial_velocity: Vec2

    _casing: bool
    _coll_sibling: bool

    _base_damage: float
    _time_to_life: float
    _o_time_to_life: float
    _explosion_radius: float
    _explosion_damage: float
    _cluster_depth: int
    _cluster_amount: int
    _cluster_spread: float
    _cluster_chain_ttl: bool
    _cluster_step_explosion: float
    _cluster_size_mult: float
    _cluster_last_step_ttl: float
    _cluster_bullet_type: type[Bullet]
    _cluster_step_inertia: float
    _visibility_offset: float
    _invincibility_offset: float
    _last_pos: Vec2
    _fuzes: list[BaseFuze]

    _left_root: bool
    _initial_root_collision_exception: CollisionGroupIDType | None
    _root_entity: LogicGameEntity | None

    _target_pos: Vec2 | EllipsisType
    _o_dist: float

    _hp: int

    _ignore_collision_id: int | None = None

    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        weapon_collision_exception_id: int,
        *,
        initial_facing: float | EllipsisType = ...,
        centered: bool = True,
        collision_group: CollisionGroupIDType | EllipsisType | None = ...,
        collision_exception_ids: list[int] | int | None = None,
        collision_exception_root: bool | EllipsisType = ...,
        collision_exception_root_additive: bool | EllipsisType = ...,
        casing: bool = False,
        no_gravity: bool = False,
        collide_siblings: bool = True,
        base_damage: float | EllipsisType = ...,
        time_to_life: float | EllipsisType = ...,
        explosion_radius: float | EllipsisType = ...,
        explosion_damage: float | EllipsisType = ...,
        cluster_depth: int | EllipsisType = ...,
        cluster_amount: int | EllipsisType = ...,
        cluster_spread_angle: float | EllipsisType = ...,
        cluster_step_explosion: float | EllipsisType = ...,
        cluster_size_mult: float | EllipsisType = ...,
        cluster_last_step_ttl: float | EllipsisType = ...,
        cluster_bullet_type: type[Bullet] | EllipsisType = ...,
        cluster_step_inertia: float | EllipsisType = ...,
        target_pos: Vec2 | EllipsisType = ...,
        size: Vec2 | int | EllipsisType = ...,
        visibility_offset: float | EllipsisType = ...,
        invincibility_offset: float | EllipsisType = ...,
        spawn_cid: str | None = None,
        graphics_spawn_args: dict[str, tp.Any] | EllipsisType = ...,
    ) -> None:
        """
        Base logic bullet
        :param runtime_buffer: logic runtime buffer
        :param parent: weapon the bullet was fired from
        :param coalition: Coalition
        :param initial_position: spawn pos
        :param initial_velocity: spawn speed
        :param centered: Whether the position is center or top left (relevant for collision detection)
            Edit afterward with self._centered
        :param collision_group: Collision Group ID. Defaults to cls._DEFAULT_COLLISION_GROUP.
        :param collision_exception_ids: Optional list of collision exception rules.
            Edit afterward with self._collision_exception_ids
        :param collision_exception_root: Groups this entity and all its children recursive to a collision exception
            rule. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT.
        :param collision_exception_root_additive: Whether root collision exception rules created from parents are also
            added to this entity and its children recursive. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE.
            Recurses until the next parents sets this to false
        :param casing: is casing
        :param no_gravity: ignore gravity
        :param collide_siblings: collide with bullets from same gun
        :param base_damage: base damage used for damage calculation
        :param time_to_life: max ttl
        :param explosion_radius: explosion radius
        :param explosion_damage: explosion size
        :param cluster_depth: n of cluster steps
        :param cluster_amount: n of bullets per cluster step
        :param cluster_spread_angle: spread of bullets
        :param cluster_step_explosion: explosion size per cluster step (0 if None)
        :param cluster_size_mult: size multiplier per cluster step
        :param cluster_last_step_ttl: last cluster step bullet ttl (-1 if dynamic)
        :param target_pos: target position
        :param size: bullet size
        :param visibility_offset: visibility offset
        :param invincibility_offset: invincibility offset.
        """
        self._start_time = perf_counter()

        self._hp = self._default_hp
        self._weapon_ceid = weapon_collision_exception_id

        size = get_default(size, self._default_size)
        if not isinstance(size, Vec2):
            size: Vec2 = Vec2().from_cartesian(size, size)  # type: ignore

        # required params
        self._initial_velocity = initial_velocity

        self._casing = casing
        self._coll_sibling = collide_siblings

        # default params
        self._base_damage = get_default(base_damage, self._default_base_damage)
        self._time_to_life = get_default(time_to_life, self._default_ttl)
        self._o_time_to_life = self._time_to_life
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
        self._cluster_step_explosion = get_default(
            cluster_step_explosion, self._default_cluster_step_explosion
        )
        self._cluster_size_mult = get_default(
            cluster_size_mult, self._default_cluster_size_mult
        )
        self._cluster_last_step_ttl = get_default(
            cluster_last_step_ttl, self._default_cluster_last_step_ttl
        )
        bullet_default = get_default(self._default_cluster_bullet_type, self.__class__)
        self._cluster_bullet_type: type[Bullet] = get_default(
            cluster_bullet_type, bullet_default
        )
        self._cluster_step_inertia = get_default(
            cluster_step_inertia, self._default_cluster_step_inertia
        )
        self._cluster_args = {}
        self._visibility_offset = get_default(
            visibility_offset, self._default_visibility_offset
        )
        self._invincibility_offset = get_default(
            invincibility_offset, self._default_invincibility_offset
        )
        self._weight = self._default_weight

        # optional params
        if target_pos == ...:
            self._target_pos = ...
            self._o_dist = 0.0

        else:
            self._target_pos = target_pos.copy()
            self._o_dist = (initial_position - self._target_pos).length

        # init superclass
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=initial_position.copy(),
            initial_velocity=initial_velocity.copy(),
            coalition=coalition,
            parent=parent,
            centered=centered,
            collision_group=collision_group,
            collision_exception_ids=collision_exception_ids,
            collision_exception_root=collision_exception_root,
            collision_exception_root_additive=collision_exception_root_additive,
            tags=["bullet"],
        )

        self._left_root = False
        self._root_entity = self.root
        self._initial_root_collision_exception = None
        if self._root_entity is not None:
            if hasattr(self._root_entity, "get_initial_root_collision_exception"):
                self._initial_root_collision_exception = (
                    self._root_entity.get_initial_root_collision_exception()
                )
                if self._initial_root_collision_exception is not None:
                    self._collision_exception_ids.append(
                        self._initial_root_collision_exception
                    )

        self._collision_exception_ids.append(weapon_collision_exception_id)

        # create default fuzes
        self._fuzes: list[BaseFuze] = []

        # create fuzes
        for fuze in self._default_fuze:
            kwargs = fuze.copy()
            fuze_name = kwargs.pop("type", None)

            if fuze_name in FUZES:
                fuze_type = FUZES[fuze_name]

                # insert required arguments to kwargs
                params = inspect.signature(fuze_type.__init__).parameters

                to_insert = {
                    "ttl": self._o_time_to_life,
                    "parent": self,
                    "position": self._target_pos,
                    "collision_exception_id": weapon_collision_exception_id,
                }

                # check if any of to_insert is required by params and not in kwargs
                done = False
                name = ""
                for name in params:
                    if name in to_insert and name not in kwargs:
                        if isinstance(to_insert[name], EllipsisType):
                            break

                        kwargs[name] = to_insert[name]

                else:
                    done = True

                if not done:
                    print_ic_style(
                        f'couldn\'t pass argument "{name}" to fuze '
                        f'"{fuze_name}" at time of creation '
                        f"({self._parent.__class__.__name__} -> "
                        f"{self.__class__.__name__})",
                        warning=True,
                    )
                    continue

                # add fuze
                try:
                    self._fuzes.append(fuze_type(**kwargs))

                except TypeError:
                    # list all specified arguments (+self)
                    spec = set(list(kwargs.keys()) + ["self"])

                    # list all arguments without default value
                    req = {p for p in params if params[p].default == inspect._empty}

                    debug_str = (
                        f'invalid params for fuze type "{fuze_type.__name__}" '
                        f"({self.__class__.__name__})"
                    )

                    miss = req - spec
                    if miss:
                        debug_str += f", missing: {miss}"

                    add = spec - req
                    if add:
                        debug_str += f", additional: {add}"

                    if not miss and not add:
                        debug_str += ", argument list OK"

                    print_ic_style(debug_str, error=True)

            else:
                print_ic_style(f'Invalid fuze type: "{fuze_name}"', error=True)

        # set facing
        self.facing.angle = get_default(initial_facing, self.velocity.angle)

        self._create_collision()
        runtime_buffer[self.id].param0 = self._explosion_radius

        if self._cluster_depth > 0:
            if self._cluster_step_explosion:
                self._runtime_buffer[self.id].param0 = self._cluster_step_explosion

            else:
                self._runtime_buffer[self.id].param0 = -1

        self._last_pos = self.position.copy()

        self.remove(Updated)

        # toggles
        if not no_gravity:
            self.add(GravityAffected)

        if not casing:
            self.add(Bullets)

        # spawn dummy
        kwargs = get_default(graphics_spawn_args, {})
        kwargs.update(
            {
                "id": self.id,
                "cid": spawn_cid or self.cid(),
                "spawn_time": self._start_time,
                "visibility_offset": self._visibility_offset,
                "position": self.position.xy,
            }
        )

        if self._target_pos != ...:
            kwargs["target_pos"] = self._target_pos.xy

        pv.COQ.put(ProcessCommand(type=BaseCommandType.spawn_dummy, kwargs=kwargs))

    # region Properties
    @property
    def damage(self) -> float:
        """:return: bullet damage"""
        if self._casing:
            return 0

        # calculate damage based on base_damage and velocity
        x = max(self._initial_velocity.length, 800)

        speed_mult = 1 + ((self.velocity.length - 1300) / x) * 0.5
        return self._base_damage * speed_mult

    @property
    def weight(self) -> float:
        """:return: bullet weight (depending on size if not specified)"""
        if self._weight:
            return self._weight

        return self._weight_from_size(self.size)

    @property
    def recoil_fac(self) -> float:
        r""":return: weapons recoil \"dampener\""""
        return self.get_recoil_fac(self.weight, self.velocity.length)

    @property
    def last_pos(self) -> Vec2:
        """:return: bullets previous position"""
        return self._last_pos.copy()

    @property
    def ttl(self) -> float:
        """:returns: time left to life"""
        return self._time_to_life

    @property
    def target_pos(self) -> Vec2 | None:
        if not isinstance(self._target_pos, EllipsisType):
            return self._target_pos.copy()

        return None

    # endregion

    def hit(self, _damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        """Bullet was hit by someone."""
        if self._hp <= 0 or not issubclass(hit_by.__class__, Bullet):
            self.kill(killed_by=hit_by)

        else:
            self._hp -= _damage
            if self._hp <= 0:
                self.kill(killed_by=hit_by)

    def hit_someone(self, target_hp: float) -> None:
        """Bullet has hit someone else."""
        self.kill()

    # region Collision
    def __collision_island(self, events: list[CollisionEvent[Island]]) -> None:
        """
        Collision reaction to islands: Bullet dies
        :param events: All details regarding the collisions.
        """
        event: CollisionEvent[Island] = events[0]
        self.position = event.position
        self.acceleration *= 0
        self.velocity *= 0
        self.kill(killed_by=event.other_entity)

    def __collision_general_hit(
        self,
        events: list[
            CollisionEvent[BaseTurret | Player | Grenade | Shield | RideableTurret]
        ],
    ) -> None:
        """
        General collision reaction is to try to hit the other entity
        and if it can be hit, the bullet will be killed
        :param events: All details regarding the collisions.
        """
        if not self._alive:
            return

        for event in events:
            if hasattr(event.other_entity, "hit"):
                # noinspection PyNoneFunctionAssignment
                hit_success: bool | None = event.other_entity.hit(
                    self.damage,
                    hit_by=self,
                )
                if hit_success is None or hit_success is True:
                    self.position.x = event.position.x
                    self.position.y = event.position.y

                    self.kill(killed_by=event.other_entity)
                    break

    def __collision_bullet_or_aerodynamic_entity(
        self,
        events: list[CollisionEvent[Bullet | AerodynamicEntity]],
    ) -> None:
        """
        Bullet/Aerodynamic entities hit each other
        :param events: All details regarding the collisions.
        """
        for event in events:
            self.hit(event.other_entity.damage, event.other_entity)

    def _collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[
            CollisionEvent[
                Island
                | Bullet
                | Player
                | BaseTurret
                | Grenade
                | Shield
                | RideableTurret
                | AerodynamicEntity
            ]
        ],
    ) -> list[bool] | None:
        """
        Distribute collision start events to different methods.

        Note: This function takes into account
            that it gets also called as an AerodynamicEntity.

        - Island: Bullet kills itself
        - Bullet: Bullets hit each other
        - Player: Bullet hits the player and either pierces through or dies
        - BaseTurret: Bullet hits the turret and either pierces through or dies
        - Grenade: Bullet hits the grenade and either pierces through or dies
        - Shield: Bullet hits the shield and either pierces through or dies
        - RideableTurret: Bullet hits the turret and either pierces through or dies
        - AerodynamicEntity: Bullets and Aerodynamic entities hit each other

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        :return: List of booleans stating whether each collision is accepted.
        """
        if (
            group_id == GameCollisions.collision_group_grenades
            or group_id == GameCollisions.collision_group_shields
        ):
            events: list[CollisionEvent[Grenade | Shield]]
            self.__collision_general_hit(events)

        elif (
            group_id == GameCollisions.collision_group_players
            or group_id == GameCollisions.collision_group_turrets
            or group_id == GameCollisions.collision_group_rideable_turrets
        ):
            events: list[CollisionEvent[BaseTurret | Player | RideableTurret]]
            if self._left_root:
                self.__collision_general_hit(events)

        elif group_id == GameCollisions.collision_group_islands:
            events: list[CollisionEvent[Island]]
            self.__collision_island(events)

        elif (
            group_id == GameCollisions.collision_group_bullets
            or group_id == GameCollisions.collision_group_aerodynamic_entity
        ):
            events: list[CollisionEvent[Bullet | AerodynamicEntity]]
            self.__collision_bullet_or_aerodynamic_entity(events)

        return None

    # endregion

    def _update(self, delta, update_facing: bool = True) -> None:
        self._time_to_life -= delta
        self._visibility_offset -= delta
        self._invincibility_offset -= delta

        if not self._left_root:
            root = self.root
            if root is not None:
                offset: int = 10
                if (
                    self.position.x + self.size.x <= root.position.x - offset
                    or self.position.x >= root.position.x + root.size.x + offset
                    or self.position.y + self.size.y <= root.position.y - offset
                    or self.position.y >= root.position.y + root.size.y + offset
                ):
                    self._left_root = True
                    if (
                        self._initial_root_collision_exception is not None
                        and self._initial_root_collision_exception
                        in self._collision_exception_ids
                    ):
                        self._collision_exception_ids.remove(
                            self._initial_root_collision_exception
                        )

        if self._time_to_life <= 0:
            self.kill()
            return

        # double gravity (because why not)
        self.acceleration.y *= 2

        self._last_pos = self.position.copy()

        super()._update(delta)

        if update_facing:
            self.facing.angle = self.velocity.angle

        # update fuzes
        for fuze in self._fuzes:
            fuze.update()

        # update velocity
        self._runtime_buffer[self.id].param1 = self.velocity.length

    def _before_kill(
        self,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> bool:
        if killed_by != ... and killed_by != self:
            if killed_by.parent == self.parent and not self._coll_sibling:
                return False

        if self._invincibility_offset > 0:
            return False

        # check if casing
        if all([self._casing, not Updated.out_of_bounds_x(self)]):
            self.position.y -= self.size.y / 2
            self.remove(Updated, GravityAffected)
            return False

        return True

    @tp.override
    def _kill(
        self,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> None:
        for fuze in self._fuzes:
            fuze.kill(killed_by)

        # bullet hit knockback
        if all([killed_by != self, not issubclass(killed_by.__class__, Bullet)]):
            if hasattr(killed_by, "_impulse_resistance_factor"):
                recoil = (
                    Vec2().from_polar(self.velocity.angle, self.recoil_fac)
                    * killed_by._impulse_resistance_factor
                )

                killed_by.add_velocity(recoil)

        # cluster
        if (
            self._cluster_depth > 0 and self._cluster_amount > 0
        ):  # and killed_by == self:
            if self._cluster_amount > 1:
                kill_children = False
                # cluster step explosion:
                if self._cluster_step_explosion:
                    self._explosion_radius = self._cluster_step_explosion

                    # exp = DistantPop()
                    # exp.set_volume(1, 0.6)
                    # exp.play(pos=self.position)

                angle_spread = self._cluster_spread / (self._cluster_amount - 1)
                current_angle = self.velocity.angle - self._cluster_spread / 2

                if self._cluster_depth > 1:
                    ttl = self._time_to_life

                elif self._default_cluster_last_step_ttl >= 0:
                    ttl = self._default_cluster_last_step_ttl

                else:
                    ttl = self._time_to_life

                sibling_collision_exception: CollisionExceptionIDType = (
                    GameCollisions.add_exception()
                )
                for _bi in range(self._cluster_amount):
                    self._cluster_bullet_type(
                        self._runtime_buffer,
                        self,
                        self.coalition,
                        self.position.copy(),
                        Vec2().from_polar(
                            current_angle,
                            self.velocity.length + self._cluster_step_inertia,
                        ),
                        # base_damage=self._base_damage,
                        time_to_life=ttl,
                        # explosion_radius=self._explosion_radius,
                        # explosion_damage=self._explosion_damage,
                        cluster_depth=self._cluster_depth - 1,
                        # cluster_amount=self._cluster_amount,
                        # cluster_spread_angle=self._cluster_spread,
                        target_pos=self._target_pos,
                        size=self.size * self._cluster_size_mult,
                        collide_siblings=False,
                        collision_exception_ids=sibling_collision_exception,
                        weapon_collision_exception_id=self._weapon_ceid,
                    )
                    current_angle += angle_spread

        # explode (only if not cluster)
        if self._explosion_radius > 0:
            for d, entity in BaseGroup.entities_in_circle(
                entities=Updated.entities(),
                center=self.position,
                radius=self._explosion_radius * 2,
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

            if self._explosion_radius > 64:
                exp = LargeExplosion()
                exp.volume = 0.35
                exp.play(pos=self.position)

            # sounds like shit
            elif self._explosion_radius < 16:
                exp = DistantPop()
                exp.set_volume(0.8, 0.3)
                exp.play(pos=self.position)

        super()._kill(killed_by=killed_by, kill_children=kill_children)

    # region Static/Class-Methods
    @staticmethod
    def _weight_from_size(size: Vec2 | float) -> float:
        """
        Calculate bullet weight from size
        :param size: bullet size
        :return: calculated weight from size.
        """
        if isinstance(size, Vec2):
            return size.length / 100

        return (size * SQR2) / 100

    @classmethod
    def get_weight(cls, size: Vec2 | float) -> float:
        """
        Bullet weight getter
        :param size: bullet size
        :return: bullet weight (depending on size if not specified).
        """
        if cls._default_weight:
            return cls._default_weight

        return cls._weight_from_size(size)

    @classmethod
    def get_recoil_fac(cls, weight: float, velocity: float) -> float:
        r"""
        Recoil \"dampener\" getter
        :param weight: bullet weight
        :param velocity: bullet velocity
        :return: weapons recoil \"dampener\
        """
        return (weight / 2.5) * (velocity / 10)

    # endregion
