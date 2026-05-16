"""
amoginarium/logic/entities/_base/_collision/_collision_types.py

Defines common type aliases and enumerations used throughout the collision system.
Helps maintain type safety and provides clarity for collision identifiers.

Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""

from enum import StrEnum


class CollisionType:
    """
    Defines type aliases for collision-related identifiers to improve code clarity
    """

    __slots__ = ()

    type CollisionID = int
    type EntityID = int
    type GroupID = int
    type RelationID = int
    type ExceptionID = int


class HitboxTypes(StrEnum):
    """
    Enumeration of supported geometric primitive types for collision detection.
    """

    point = "point"
    aabb = "aabb"
    circle = "circle"
    obb = "obb"
    triangle = "triangle"
    polygon = "polygon"
