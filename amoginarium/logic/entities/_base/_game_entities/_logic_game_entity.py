"""
Defines the core LogicGameEntity.

Combines spatial data, physics (velocity/acceleration), and collision detection,
serving as the base class for standard game objects.

Path: amoginarium/logic/entities/_base/_game_entities/_logic_game_entity.py
Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium import pv
from amoginarium.shared import Coalitions, DynamicEntityParentViable
from amoginarium.shared import LogicGameEntityLike
from amoginarium.shared.debugging import CC, print_ic_style
from amoginarium.shared.utility import get_default, normalize_angle, Vec2

from ._collision_logic_entity import CollisionLogicEntity

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t

    from .._collision import CollisionType


class LogicGameEntity(
    CollisionLogicEntity, LogicGameEntityLike, DynamicEntityParentViable
):
    """
    Implements all basic stuff for logic entities.

    - Parent/Children relations
    - Groups
    - Update
    - Visibility
    - Positon, Size
    - Velocity, Acceleration
    - Optional Collision Detection
    - Coalitions.
    """

    __slots__ = (
        "facing",
        "velocity",
        "acceleration",
        "last_delta",
        "last_position",
        "_coalition",
        "_velocity_to_add",
        "_acceleration_to_add",
        "__world_position",
        "_tags",
    )

    # region ClassVars
    _default_mass: tp.ClassVar[float] = (
        0.0  # if set, will be used to calculate impulse_resistance_factor
    )
    _impulse_resistance_factor: tp.ClassVar[float] = -1  # 0 = completely resistant
    # endregion

    # region InstanceVars
    facing: Vec2  # public / no property for faster access
    velocity: Vec2  # public / no property for faster access
    acceleration: Vec2  # public / no property for faster access

    _coalition: Coalitions
    _velocity_to_add: Vec2
    _acceleration_to_add: Vec2
    __world_position: Vec2

    _tags: dict[str, None]

    # endregion

    def __init_subclass__(cls, **kwargs: tp.Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls._default_mass > 0:
            cls._impulse_resistance_factor = 1 / cls._default_mass

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        size: Vec2,
        position: Vec2,
        *,
        initial_velocity: Vec2 | None = None,
        parent: LogicGameEntity | None = None,
        coalition: Coalitions | EllipsisType = ...,
        centered: bool = False,
        collision_group: CollisionType.GroupID | EllipsisType | None = ...,
        collision_exception_ids: list[int] | int | None = None,
        collision_exception_root: bool | EllipsisType = ...,
        collision_exception_root_additive: bool | EllipsisType = ...,
        tags: list[str] | None = None,
        collision_active: bool = True,
    ) -> None:
        """
        Basic logic game entity that implements all basic stuff for logic entities
        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param initial_velocity: Optional 2D initial velocity of the entity
        :param parent: Optional parent entity
        :param coalition: Coalition of the entity. Defaults to Coalitions.neutral
        :param centered: Whether the position is center or top left (relevant for
            collision detection) Edit afterward with self._centered
        :param collision_group: Collision Group ID. Defaults to
            cls._DEFAULT_COLLISION_GROUP.
        :param collision_exception_ids: Optional list of collision exception rules.
            Edit afterward with self._collision_exception_ids
        :param collision_exception_root: Groups this entity and all its children recursive to a collision exception
            rule. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT.
        :param collision_exception_root_additive: Whether root collision exception rules created from parents are also
            added to this entity and its children recursive. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE.
            Recurses until the next parents sets this to false
        :param tags: Optional list of tags for the entity
        :param collision_active: Whether the collision detection is active.
        """
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            parent=parent,
            centered=centered,
            collision_group=collision_group,
            collision_exception_ids=collision_exception_ids,
            collision_exception_root=collision_exception_root,
            collision_exception_root_additive=collision_exception_root_additive,
            collision_active=collision_active,
        )
        # region default parameters
        self._velocity_to_add = Vec2()
        self._acceleration_to_add = Vec2()
        self.last_position = self.position.copy()
        self.last_delta = 0

        self.velocity = (
            initial_velocity if initial_velocity is not None else Vec2()
        )  # do not use get_default here
        self._coalition = get_default(coalition, Coalitions.neutral)

        self.acceleration = Vec2()
        self.__world_position = Vec2()  # actual world position
        self.facing = Vec2().from_polar(0, 1)

        self._tags = {}
        if tags is not None:
            self._tags.update(dict.fromkeys(tags))
        # endregion

    # region Properties
    @property
    def world_position(self) -> Vec2:
        """:return: entity position on screen"""
        return self.position - self.__world_position

    @property
    def coalition(self) -> Coalitions:
        """:return: which coalition the entity belongs to"""
        return self._coalition

    @property
    def serializable(self) -> bool:
        """:return: whether the entity is serializable or not"""
        return self._CID is not ...

    # endregion

    # region methods
    def to_dict(self) -> dict | None:
        """:return: convert the entity to a dict if possible"""
        if not self.serializable:
            print_ic_style(
                f"{CC.fg.RED}Entity of type {self.__class__.__name__} is not"
                f"serializable{CC.ctrl.ENDL}",
            )

        return {"type": self.cid(), "pos": self.position}

    def add_impulse(self, impulse: Vec2) -> None:
        """
        Add an impulse force to the entity.

        :param impulse: impulse to add.
        """
        if self._impulse_resistance_factor > 0:
            self._velocity_to_add += impulse * self._impulse_resistance_factor

    def add_velocity(self, value: Vec2) -> None:
        """
        Add velocity to the entity and guarantee that it will be valid (for short bursts).

        :param value: 2D velocity to add.
        """
        if self._impulse_resistance_factor > 0:
            self._velocity_to_add += value

    def add_acceleration(self, value: Vec2) -> None:
        """
        Add acceleration to the entity and guarantee that it will be valid (for long accelerations).

        :param value: 2D acceleration to add.
        """
        if self._impulse_resistance_factor > 0:
            self._acceleration_to_add += value

    def _update(self, delta: float) -> None:
        """
        Update logic game entity.

        :param delta: time since the last update.
        """
        self.last_delta = delta

        self.__world_position = pv.global_vars.get_world_position()

        self.velocity += (
            self._acceleration_to_add + self.acceleration
        ) * delta + self._velocity_to_add

        # update position
        self.last_position = self.position.copy()
        self.position += self.velocity * delta

        self.acceleration.x *= 0

        self._velocity_to_add *= 0
        self._acceleration_to_add *= 0

        # update timer
        super()._update(delta)

        # update runtime buffer
        self._runtime_buffer[self.id].facing = int(
            normalize_angle(self.facing.angle) * 10_000
        )

    # endregion
