"""
_logic_entity_hints.py
28.03.2026

type hints for logic entities

Author:
Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from types import EllipsisType

    from . import base_entity_t, CIDType, Coalitions
    from .collision_detection import CollisionEvent
    from .utility import Vec2


class EntityChildViable(tp.Protocol):
    """Minimum requirements for an object to be assigned as a child of a logic entity."""

    def update(self, delta: float) -> None:
        """
        Update function
        :param delta: Tme since the last update
        """
        ...

    def kill(self) -> None:
        """Clean up and terminate the child."""
        ...


class BaseLogicEntityLike(tp.Protocol):
    """
    Protocol for the most basic type of logic entity.
    - Parent/Children relations
    - groups
    - update
    - visibility
    """

    @property
    def id(self) -> int:
        """:return: entity id (+ buffer location)"""
        ...

    @property
    def parent(self) -> BaseLogicEntityLike | None:
        """:return: entities parent if present"""
        ...

    @property
    def root(self) -> BaseLogicEntityLike:
        """:return: root entity; entity parent if present else self"""
        ...

    @property
    def children(self) -> list[EntityChildViable]:
        """:return: list of all children of this entity"""
        ...

    @property
    def _buffer(self) -> base_entity_t:
        """:return: runtime buffer data for this entity"""
        ...

    def _set_bit(self, param: str, bit_index: int, value: bool) -> None:
        """
        set (or reset) on a specified bit
        :param param: what parameter to set the bit at
        :param bit_index: bit to set
        :param value: what to set the bit to
        """
        ...

    def add(self, *groups: tp.Any) -> None:
        """
        add entity to one or more logic groups
        :param groups: to add entity to
        """
        ...

    def remove(self, *groups: tp.Any) -> None:
        """
        remove entity from one or more logic groups
        :param groups: to remove entity from
        """
        ...

    def _kill(self, killed_by: BaseLogicEntityLike | EllipsisType = ...) -> None:
        """
        Kill entity and all its children
        :param killed_by: who killed this entity
        """
        ...

    def kill(self, killed_by: BaseLogicEntityLike | EllipsisType = ...) -> None:
        """
        Kill entity and all its children
        :param killed_by: who killed this entity
        """
        ...

    def _update(self, delta: float) -> None:
        """
        Update function for the entity
        :param delta: time since the last update
        """
        ...

    def update(self, delta: float, recursive: bool = True) -> None:
        """
        Update entity and their children
        :param delta: time since the last update
        :param recursive: Whether to update children recursively
        """
        ...

    def show(self) -> None:
        """Set visibility to 1"""
        ...

    def hide(self) -> None:
        """Set visibility to 0"""
        ...

    def highlight(self) -> None:
        """highlight the graphics entity"""
        ...

    def stop_highlight(self) -> None:
        """stop highlighting the graphics entity"""
        ...


class PositionedLogicEntityLike(BaseLogicEntityLike, tp.Protocol):
    """Protocol for a logic entity with position and size."""
    position: Vec2
    size: Vec2

    @property
    def parent(self) -> PositionedLogicEntityLike | None:
        """:return: entities parent if present"""
        ...

    @classmethod
    def cid(cls) -> CIDType:
        """
        :return: the entities' component ID
        :raises ValueError: if the class has no __cid
        """
        ...

    def _get_ids(self) -> list[int]:
        """:return: list of all entity IDs including this one and its parents recursively"""
        ...


class CollisionLogicEntityLike(PositionedLogicEntityLike, tp.Protocol):
    """
    Protocol for a logic entity that supports collision detection and response.
    Integrates with the global collision_manager to handle hitboxes, collision events,
    and collision filtering via exception IDs.
    """

    @property
    def parent(self) -> CollisionLogicEntityLike | None:
        """:return: entities parent if present"""
        ...

    @property
    def _collision_entity_id(self) -> int | None:
        """:return: Collision Entity ID or None if no collision not created"""
        ...

    @property
    def _collision_group(self) -> int | None:
        """:return: Collision Group ID"""
        ...

    @property
    def _collision_exception_root_ids(self) -> list[int]:
        """:return: Root Collision exceptions rules. Maybe an empty list if they haven't been calculated yet"""
        ...

    @classmethod
    def debug_draw_hitboxes(cls, value: bool) -> None:
        """
        Enables or disables global debug rendering for hitboxes.
        :param value: True to enable, False to disable.
        """
        ...

    def _get_root_collision_exceptions(self) -> list[int]:
        """Calculates root collision exceptions rules"""
        ...

    def _collision_start(self, event: list[CollisionEvent[CollisionLogicEntityLike]]) -> list[bool] | None:
        """
        Called on collision start
        :param event: All details regarding the collisions
        :return: List of bools stating whether each collision is accepted.
        """
        ...

    def collision_start(self, events: list[CollisionEvent[CollisionLogicEntityLike]]) -> list[bool] | None:
        """
        Callback for collision start, called by the collision manager
        :param events: All details regarding the collisions
        :return: List of bools stating whether each collision is accepted.
        """
        ...

    def _collision_end(self, events: list[CollisionEvent[CollisionLogicEntityLike]]) -> None:
        """
        Called on collision end
        :param events: All details regarding the collisions
        """
        ...

    def collision_end(self, events: list[CollisionEvent[CollisionLogicEntityLike]]) -> None:
        """
        Callback on COLLISION_END, called by the collision manager
        :param events: All details regarding the collisions
        """
        ...

    def _create_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...
    ) -> None:
        """
        Registers this entity with the collision manager.
        """
        ...

    def _update_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...,
            shift_history: bool = True
    ) -> None:
        """
        Updates the entity's hitbox parameters in the collision manager.
        """
        ...

    def _delete_collision(self) -> None:
        """
        Removes the entity from the collision manager and cleans up debug visuals.
        """
        ...


class LogicGameEntityLike(CollisionLogicEntityLike, tp.Protocol):
    """
    Protocol for basic game logic entities
    - Parent/Children relations
    - Groups
    - Update
    - Visibility
    - Position, Size
    - Velocity, Acceleration
    - Optional Collision Detection
    - Coalitions
    """
    facing: Vec2
    velocity: Vec2
    acceleration: Vec2

    @property
    def parent(self) -> LogicGameEntityLike | None:
        """:return: entities parent if present"""
        ...

    @property
    def world_position(self) -> Vec2:
        """:return: entity position on screen"""
        ...

    @property
    def coalition(self) -> Coalitions:
        """:return: which coalition the entity belongs to"""
        ...

    @property
    def serializable(self) -> bool:
        """:return: whether the entity is serializable or not"""
        ...

    def to_dict(self) -> dict | None:
        """:return: convert the entity to a dict if possible"""
        ...

    def add_velocity(self, value: Vec2) -> None:
        """
        add velocity to the entity and guarantee that it will be valid (for short bursts)
        :param value: 2D velocity to add
        """
        ...

    def add_acceleration(self, value: Vec2) -> None:
        """
        add acceleration to the entity and guarantee that it will be valid (for long accelerations)
        :param value: 2D acceleration to add
        """
        ...
