"""
Base entity classes and functionality modules for logic entities.

| ``Path``: amoginarium/logic/entities/_base/__init__.py
| ``Project``: amoginarium
| ``Created``: 27.04.2026
| ``Authors``: LukasKrah
"""

from ._base_entities import BaseLogicEntity, PositionedLogicEntity
from ._collision import CollisionCallbackType, CollisionEntityIDType, CollisionEvent
from ._collision import CollisionEventIDType, CollisionExceptionIDType
from ._collision import CollisionGroupIDType, CollisionHitboxType, CollisionManager
from ._collision import CollisionRelationIDType, CollisionTypes, GameCollisions
from ._debug import DebugCircleEntity, DebugPolygonEntity, DebugRectangleEntity
from ._game_entities import CollisionLogicEntity, LogicGameEntity
from ._groups import BaseGroup, Bullets, Dead, FrictionXAffected
from ._groups import GravityAffected, LogicGroup, Players, Updated, Walls

GameCollisions.init(  # noqa: RUF067
    CollisionLogicEntity.collision_start,  # type: ignore[trust me]
    CollisionLogicEntity.collision_end,  # type: ignore[trust me]
)


__all__ = (
    "BaseLogicEntity",
    "EntityChildViable",
    "PositionedLogicEntity",
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
    "DebugCircleEntity",
    "DebugPolygonEntity",
    "DebugRectangleEntity",
    "CollisionLogicEntity",
    "LogicGameEntity",
    "BaseGroup",
    "Bullets",
    "FrictionXAffected",
    "GravityAffected",
    "LogicGroup",
    "Players",
    "Updated",
    "Walls",
)
