"""
amoginarium/shared/collision_detection/_collision_methods/__init__.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from ._base_method import CollisionMethod
from ._method_types import (
    PointPointCollision, PointAABBCollision,
    AABBPointCollision, AABBAABBCollision
)
from ._methods import CollisionMethods
