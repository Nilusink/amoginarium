"""
Exposes core logic entities, weaponry, and world objects.

Path: amoginarium/logic/entities/__init__.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

from ._base import BaseLogicEntity, Bullets, Dead, FrictionXAffected
from ._base import GameCollisions, GravityAffected, LogicGameEntity
from ._base import Players, PositionedLogicEntity, Updated, Walls
from ._player import Player
from ._spawnables import SPAWNABLES
from ._weaponry import ExactoBullet, Grenade
from ._weaponry.templates import AerodynamicEntity, BaseSensor, Bullet
from ._weaponry.templates import DETECTION_GLOBAL_BLUE, DETECTION_GLOBAL_NEUTRAL
from ._weaponry.templates import DETECTION_GLOBAL_RED, DETECTION_GROUP_MANAGER
from ._weaponry.templates import DetectionGroup, MagicSensor
from ._world import GrassIsland, Island
