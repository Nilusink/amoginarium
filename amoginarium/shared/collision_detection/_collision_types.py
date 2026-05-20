"""
Defines common type aliases and enumerations used throughout the collision system.

Path: amoginarium/shared/collision_detection/collision_types.py
Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""

import typing as tp

from ._collision_event import CollisionEvent

# ruff: disable[UP040] - otherwise typing in cython is wrong
CollisionEventIDType: tp.TypeAlias = int
CollisionEntityIDType: tp.TypeAlias = int
CollisionGroupIDType: tp.TypeAlias = int
CollisionRelationIDType: tp.TypeAlias = int
CollisionExceptionIDType: tp.TypeAlias = int

CollisionHitboxType: tp.TypeAlias = tp.Literal[
    "point",
    "aabb",
    "circle",
    "obb",
    "polygon",
    "triangle",
]
# ruff: enable[UP040]


type CollisionCallbackType = tp.Callable[
    [CollisionGroupIDType, list[CollisionEvent[tp.Any]]], list[bool] | None
]


class CollisionTypes:
    """
    Collection of all collision types.
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
    "CollisionEvent",
]
