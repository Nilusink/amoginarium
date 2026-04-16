"""
amoginarium/shared/collision_detection/_collision_relation.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

import typing as tp
from types import EllipsisType

from .._collision_group import (
    CollisionGroup,
    CollisionHitBox,
    CollisionGroupEntityData
)

from .._collision_methods import (
    CollisionMethod,
    CollisionMethods
)

from .._collision_event import CollisionCallback


class CollisionRelation[T1, T2]:
    __slots__ = (
        "__group_a", "__group_b", "__collision_method",
        "__callback_a", "__callback_b",
        "__list_a", "__list_b", "__grid_b", "__collision_func"
    )

    __group_a: CollisionGroup[T1]
    __group_b: CollisionGroup[T2]
    __collision_method: CollisionMethod
    __callback_a: CollisionCallback[T1, T2] | None
    __callback_b: CollisionCallback[T2, T1] | None

    __list_a: list[CollisionGroupEntityData[T1]]
    __list_b: list[CollisionGroupEntityData[T2]]
    __grid_b: dict[int, list[int]]
    __collision_func: tp.Callable

    def __init__(
            self,
            *,
            group_a: CollisionGroup[T1],
            group_b: CollisionGroup[T2],
            on_collision_a: CollisionCallback[T1, T2] | None = None,
            on_collision_b: CollisionCallback[T2, T1] | None = None,
            collision_method: CollisionMethod | EllipsisType = ...,
    ) -> None:
        self.__group_a = group_a
        self.__group_b = group_b
        self.__callback_a = on_collision_a
        self.__callback_b = on_collision_b

        if collision_method == ...:
            match self.__group_a.hitbox_type, self.__group_b.hitbox_type:
                case (CollisionHitBox.point, CollisionHitBox.point):
                    ...
                case (CollisionHitBox.point, CollisionHitBox.aabb) | (CollisionHitBox.aabb, CollisionHitBox.point):
                    ...
                case (CollisionHitBox.aabb, CollisionHitBox.aabb):
                    collision_method = CollisionMethods.aabb_aabb.Cython

        self.__collision_method = collision_method

        # Pre-cache list and grid lookups for maximum speed
        self.__list_a = self.__group_a.entities
        self.__list_b = self.__group_b.entities
        self.__grid_b = getattr(self.__group_b, "grid", {})
        self.__collision_func = self.__collision_method.collision

    def calculate_collisions(self) -> None:
        self.__collision_func(
            self.__group_a,
            self.__group_b,
            self.__list_a,
            self.__list_b,
            self.__grid_b,
            self.__callback_a,
            self.__callback_b
        )
