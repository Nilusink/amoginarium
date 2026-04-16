"""
amoginarium/shared/collision_detection/_collision_manager.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

import typing as tp
from types import EllipsisType

from amoginarium.shared.debugging import cum_timer

from ._collision_group import CollisionGroup
from ._collision_methods import CollisionMethod
from ._collision_relation import CollisionRelation
from ._collision_event import CollisionCallback


class CollisionManager:
    __slots__ = ("__relations", "__dispatch")
    __relations: list[CollisionRelation]
    __dispatch: list[tp.Callable[[], None]]

    def __init__(self) -> None:
        self.__relations = []
        self.__dispatch = []

    @cum_timer.time_this
    def create_relation[T1, T2](
            self,
            *,
            group_a: CollisionGroup[T1],
            group_b: CollisionGroup[T2],
            on_collision_a: CollisionCallback[T1, T2] | None = None,
            on_collision_b: CollisionCallback[T2, T1] | None = None,
            collision_method: CollisionMethod | EllipsisType = ...,
    ) -> None:
        self.add_relation(
            CollisionRelation(
                group_a=group_a,
                group_b=group_b,
                on_collision_a=on_collision_a,
                on_collision_b=on_collision_b,
                collision_method=collision_method
            )
        )

    def add_relation(self, relation: CollisionRelation) -> None:
        self.__relations.append(relation)
        # Cache the bound method directly to bypass attribute lookup every frame
        self.__dispatch.append(relation.calculate_collisions)

    @cum_timer.time_this
    def calculate_all_collisions(self) -> None:
        for dispatch_func in self.__dispatch:
            dispatch_func()