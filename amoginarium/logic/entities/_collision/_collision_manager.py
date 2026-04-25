"""
amoginarium/logic/entities/_collisions.py

Project: amoginarium
Created: 16.04.2026
Authors: LukasKrah
"""

from enum import StrEnum

from amoginarium.shared.collision_detection import CollisionManager


collision_manager = CollisionManager(
    base_cell_size=500,
    level_dividers=[10],
)


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
