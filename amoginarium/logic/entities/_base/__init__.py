"""
Base entity classes and functionality modules for logic entities.

Path: amoginarium/logic/entities/_base/__init__.py
Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""

from ._base_entities import BaseLogicEntity, EntityChildViable, PositionedLogicEntity
from ._collision import CollisionType, GameCollisions, HitboxTypes
from ._debug import DebugCircleEntity, DebugPolygonEntity, DebugRectangleEntity
from ._game_entities import CollisionLogicEntity, LogicGameEntity
from ._groups import BaseGroup, Bullets, Dead, FrictionXAffected
from ._groups import GravityAffected, LogicGroup, Players, Updated, Walls

GameCollisions.init(
    CollisionLogicEntity.collision_start,  # type: ignore
    CollisionLogicEntity.collision_end,  # type: ignore
)
