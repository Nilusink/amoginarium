"""
amoginarium/logic/entities/_base_entities/__init__.py

Basic types of logic entities:
- BaseLogicEntity: Most basic type of logic entity.
- PositionedLogicEntity: Adds position/size and optional collision detection
- LogicGameEntity: Implements all basic stuff for logic entities

Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from ._base_logic_entity import BaseLogicEntity, EntityChildViable
from ._positioned_logic_entity import PositionedLogicEntity
from ._logic_game_entity import LogicGameEntity
