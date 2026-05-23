"""
Exports collision management systems and hitbox type definitions.

| Path: amoginarium/logic/entities/_base/_collision/__init__.py
| Project: amoginarium
| Created: 21.04.2026
| Authors: LukasKrah
"""

from amoginarium.shared.collision_detection import CollisionCallbackType
from amoginarium.shared.collision_detection import CollisionEntityIDType
from amoginarium.shared.collision_detection import CollisionEvent, CollisionEventIDType
from amoginarium.shared.collision_detection import CollisionExceptionIDType
from amoginarium.shared.collision_detection import CollisionGroupIDType
from amoginarium.shared.collision_detection import CollisionHitboxType
from amoginarium.shared.collision_detection import CollisionManager
from amoginarium.shared.collision_detection import CollisionRelationIDType
from amoginarium.shared.collision_detection import CollisionTypes

from ._game_collisions import GameCollisions

__all__ = (
    "CollisionCallbackType",
    "CollisionEntityIDType",
    "CollisionEvent",
    "CollisionEventIDType",
    "CollisionExceptionIDType",
    "CollisionGroupIDType",
    "CollisionHitboxType",
    "CollisionManager",
    "CollisionRelationIDType",
    "CollisionTypes",
    "GameCollisions",
)
