"""
Type hints for logic entities.

| ``Path``: amoginarium/shared/_logic_entity_hints.py
| ``Project``: amoginarium
| ``Created``: 28.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from ._entity_hints import DynamicEntityParentViable

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from . import base_entity_t, CIDType, Coalitions
    from .collision_detection import CollisionEvent, CollisionGroupIDType
    from .utility import Vec2


class EntityChildViable(tp.Protocol):
    """
    Minimum requirements for an object to be assigned as the child of a logic entity.
    """

    def update(self, delta: float) -> None:
        """
        Update function.

        :param delta: Tme since the last update
        """

    def kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
        force_kill: bool = False,
    ) -> bool | None:
        """
        Kill the entity and all its children.

        :param killed_by: Who killed this entity
        :param kill_children: Whether to kill children as well as recursively
        :param force_kill: Whether to kill even if before kill returns False
        :return: Whether the entity was killed or not. May be denied by _before_kill.
            None if the entity is already dead.
        """

    def parent_died(self) -> None:
        """Call when the parent dies."""


class MurderViable(tp.Protocol):
    """Can kill someone."""

    @property
    def parent(self) -> tp.Any:
        """Parent."""


class BaseLogicEntityLike(EntityChildViable, tp.Protocol):
    """
    Protocol for the most basic type of logic entity.

    - Parent/Children relations
    - Groups
    - Update
    - Visibility
    """

    @property
    def alive(self) -> bool:
        """:return: Whether the entity is alive."""

    @property
    def id(self) -> int:
        """:return: Entity id (+ buffer location)"""

    @property
    def parent(self) -> BaseLogicEntityLike | None:
        """:return: Entity parent if present."""

    def parent_died(self) -> None:
        """Call when the parent dies."""

    @property
    def root(self) -> BaseLogicEntityLike:
        """:return: Root entity; entity parent if present else self"""

    @property
    def children(self) -> list[EntityChildViable]:
        """:return: List of all children of this entity"""

    @property
    def lifetime(self) -> float:
        """Time since entity spawn."""

    @property
    def runtime_buffer(self) -> Array[base_entity_t]:
        """Entity runtime buffer."""

    def add(self, *groups: tp.Any) -> None:
        """
        Add entity to one or more logic groups.

        :param groups: To add entity to
        """

    def remove(self, *groups: tp.Any) -> None:
        """
        Remove entity from one or more logic groups.

        :param groups: To remove entity from
        """

    def kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
        force_kill: bool = False,
    ) -> bool | None:
        """
        Kill the entity and all its children.

        :param killed_by: Who killed this entity
        :param kill_children: Whether to kill children as well as recursively
        :param force_kill: Whether to kill even if before kill returns False
        :return: Whether the entity was killed or not. May be denied by _before_kill.
            None if the entity is already dead.
        """

    def update(self, delta: float, *, recursive: bool = True) -> None:
        """
        Update entity and their children.

        :param delta: Time since the last update
        :param recursive: Whether to update children recursively
        """
        ...

    def show(self) -> None:
        """Set visibility to 1."""

    def hide(self) -> None:
        """Set visibility to 0."""

    def highlight(self) -> None:
        """Highlight the graphics entity."""

    def stop_highlight(self) -> None:
        """Stop highlighting the graphics entity."""


class PositionedLogicEntityLike(
    BaseLogicEntityLike, DynamicEntityParentViable, tp.Protocol
):
    """
    Protocol for a logic entity with position and size.

    :ivar position: The 2D position of the entity. Public for faster access
        Do not modify freely!
    :ivar size: The 2D size of the entity. Public for faster access.
        Do not modify freely!
    """

    position: Vec2
    size: Vec2

    @classmethod
    def has_cid(cls) -> bool:
        """:return: Return True if the entity has a CID."""

    @classmethod
    def cid(cls) -> CIDType:
        """
        Return CID.

        :return: The entities' component ID
        :raise ValueError: if the class has no __cid
        """

    @property
    def parent(self) -> PositionedLogicEntityLike | None:
        """:return: Entity parent if present."""
        ...


class CollisionLogicEntityLike(PositionedLogicEntityLike, tp.Protocol):
    """
    Protocol for a logic entity that supports collision detection and response.

    Integrates with the global collision_manager to handle hitboxes, collision events,
    and collision filtering via exception IDs.
    """

    @classmethod
    def debug_draw_hitboxes(cls, *, value: bool) -> None:
        """
        Enable or disable global debug rendering for hitboxes.

        :param value: True to enable, False to disable.
        """

    def collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntityLike]],
    ) -> list[bool] | None:
        """
        Collision start callback, called by the collision manager.

        Shouldn't be overwritten in inheritance. Instead, use _collision_start

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        :return: List of booleans stating whether each collision is accepted.
           If false, the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again
           if there still is a collision in the next update.
        """

    def collision_end(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntityLike]],
    ) -> None:
        """
        Collision end callback, called by the collision manager.

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collisions.
        """


class LogicGameEntityLike(CollisionLogicEntityLike, tp.Protocol):
    """
    Protocol for the core logic game entity.

    - Parent/Children relations
    - Groups
    - Update
    - Visibility
    - Positon, Size
    - Velocity, Acceleration
    - Optional Collision Detection
    - Coalitions.

    :ivar facing: The 2D direction the entity is looking/facing.
    :ivar velocity: The current 2D velocity of the entity.
    :ivar acceleration: The current 2D acceleration of the entity.
    :ivar last_delta: The time delta of the last update.
    :ivar last_position: The position of the entity before the last movement.
    """

    facing: Vec2
    velocity: Vec2
    acceleration: Vec2
    last_delta: float
    last_position: Vec2

    @property
    def world_position(self) -> Vec2:
        """:return: Entity position on the screen."""

    @property
    def coalition(self) -> Coalitions:
        """:return: Which coalition the entity belongs to."""

    @property
    def serializable(self) -> bool:
        """:return: Whether the entity is serializable or not."""

    def to_dict(self) -> tp.MutableMapping[str, tp.Any] | None:
        """:return: Convert the entity to a dict if possible."""

    def add_impulse(self, impulse: Vec2) -> None:
        """
        Add an impulse force to the entity.

        :param impulse: Impulse to add.
        """

    def add_velocity(self, value: Vec2) -> None:
        """
        Add velocity to the entity and guarantee it will be valid (for short bursts).

        :param value: 2D velocity to add.
        """

    def add_acceleration(self, value: Vec2) -> None:
        """
        Add acceleration to the entity and guarantee it will be valid (for long acc).

        :param value: 2D acceleration to add.
        """
