"""
amoginarium/shared/collision_detection/collision_types.py

Defines common type aliases and enumerations used throughout the collision system.

Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""

from enum import StrEnum
import typing as tp

from ._collision_event import CollisionEvent


CollisionEventIDType: tp.TypeAlias = int
CollisionEntityIDType: tp.TypeAlias = int
CollisionGroupIDType: tp.TypeAlias = int
CollisionRelationIDType: tp.TypeAlias = int
CollisionExceptionIDType: tp.TypeAlias = int


CollisionHitboxType: tp.TypeAlias = tp.Literal[
    "point", "aabb", "circle",
    "obb", "polygon", "triangle"
]



type CollisionCallbackType = tp.Callable[
    [
        CollisionGroupIDType,
        list[CollisionEvent[tp.Any]]], list[bool] | None
]


class CollisionTypes:
    """
    Collection of all collision types
    """
    __slots__ = ()

    CollisionEventIDType = CollisionEventIDType
    CollisionEntityIDType = CollisionEntityIDType
    CollisionGroupIDType = CollisionGroupIDType
    CollisionRelationIDType = CollisionRelationIDType
    CollisionExceptionIDType = CollisionExceptionIDType

    CollisionHitboxEnum = CollisionHitboxType

    CollisionEvent = CollisionEvent
    CollisionCallback = CollisionCallbackType

__all__ = [
    "CollisionEventIDType",
    "CollisionEntityIDType",
    "CollisionGroupIDType",
    "CollisionRelationIDType",
    "CollisionExceptionIDType",
    "CollisionHitboxType",
    "CollisionCallbackType",
    "CollisionTypes",
    "CollisionEvent"
]
