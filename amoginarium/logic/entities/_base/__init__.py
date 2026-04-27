"""
amoginarium/logic/entities/_base/__init__.py

Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""
from ._groups import GravityAffected, FrictionXAffected, Bullets, Walls, Players, LogicGroup, BaseGroup, Updated
from ._collision import CollisionType, HitboxTypes, CollisionExceptions, GameCollisions
from ._base_entities import BaseLogicEntity, EntityChildViable, PositionedLogicEntity
from ._debug import DebugPolygonEntity, DebugRectangleEntity, DebugCircleEntity
from ._game_entities import CollisionLogicEntity, LogicGameEntity

GameCollisions.init(
    CollisionLogicEntity.collision_start,
    CollisionLogicEntity.collision_end
)
