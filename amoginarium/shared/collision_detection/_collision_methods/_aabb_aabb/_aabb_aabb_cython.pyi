import typing as tp

from .._method_types import AABBAABBCollision
from ..._collision_group import CollisionGroupAABBEntityData, CollisionGroupAABB
from ..._collision_event import CollisionCallback

class AABBAABBCython(AABBAABBCollision):
    @staticmethod
    def collision[T1, T2](
            group_a: CollisionGroupAABB[T1],
            group_b: CollisionGroupAABB[T2],
            entities_a: list[CollisionGroupAABBEntityData[T1]],
            entities_b: list[CollisionGroupAABBEntityData[T2]],
            grid_b: dict[int, list[int]],
            callback_a: CollisionCallback[T1, T2] | None,
            callback_b: CollisionCallback[T2, T1] | None
    ) -> None: ...
