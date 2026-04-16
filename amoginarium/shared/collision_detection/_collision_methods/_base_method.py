"""
amoginarium/shared/collision_detection/_collision_methods/_collision_method.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from .._collision_group import CollisionGroupEntityData, CollisionGroup
from .._collision_event import CollisionCallback

class CollisionMethod:
    @staticmethod
    def collision[T1, T2](
            group_a: CollisionGroup[T1],
            group_b: CollisionGroup[T2],
            entities_a: list[CollisionGroupEntityData[T1]],
            entities_b: list[CollisionGroupEntityData[T2]],
            grid_b: dict[int, list[int]],
            callback_a: CollisionCallback[T1, T2] | None,
            callback_b: CollisionCallback[T2, T1] | None
    ) -> None:
        ...