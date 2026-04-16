"""
amoginarium/shared/collision_detection/__init__.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

# todo - mytodo: everything created should be auto added to the manager!

from ._collision_group import (CollisionGroup, CollisionHitBox,
                               CollisionGroupPoint, CollisionGroupAABB)
from ._collision_relation import CollisionRelation
from ._collision_methods import CollisionMethods
from ._collision_manager import CollisionManager
from ._collision_event import CollisionEvent, CollisionCallback