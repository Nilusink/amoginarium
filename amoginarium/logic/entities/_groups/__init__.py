"""
amoginarium/logic/entities/_groups/__init__.oy.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from ._functionality_groups import GravityAffected, FrictionXAffected
from ._entity_type_groups import Bullets, Walls, Players
from ._logic_group import LogicGroup
from ._base_group import BaseGroup
from ._updated import Updated

from ._base_group import WallCollider, WallBouncer, CollisionDestroyed
