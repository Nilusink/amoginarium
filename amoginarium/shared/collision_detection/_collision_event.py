"""
amoginarium/shared/collision_detection/_collision_event.py

Project: amoginarium
Created: 15.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared.utility import Vec2
from ._collision_group import CollisionGroup


class CollisionEvent[T]:
    __slots__ = ("group", "other_entity", "position", "normal")
    group: CollisionGroup
    other_entity: T
    position: Vec2
    normal: Vec2

    def __init__(
            self,
            group: CollisionGroup,
            other_entity: T,
            position: Vec2,
            normal: Vec2,
    ) -> None:
        self.group = group
        self.other_entity = other_entity
        self.position = position
        self.normal = normal


# noinspection PyUnusedLocal
type CollisionCallback[T1, T2] = tp.Callable[[CollisionEvent[T2]], tp.Any]
