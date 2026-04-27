"""
amoginarium/logic/entities/_game_entities/__init__.py

Basic types of logic entities:
- BaseLogicEntity: Most basic type of logic entity.
- PositionedLogicEntity: Adds position/size
- CollisionLogicEntity: Adds collision detection
- LogicGameEntity: Implements all basic stuff for logic entities


Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""

from ._collision_logic_entity import CollisionLogicEntity
from ._logic_game_entity import LogicGameEntity
