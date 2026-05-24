"""
Initialization for entity groups.

Provides access to all predefined group instances
used to categorize and batch-process logic entities.

Path: amoginarium/logic/entities/_base/_groups/__init__.py
Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from ._base_group import BaseGroup
from ._entity_type_groups import Bullets, Players, Walls
from ._functionality_groups import FrictionXAffected, GravityAffected
from ._logic_group import LogicGroup
from ._updated import Updated, Dead
