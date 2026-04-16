"""
amoginarium/shared/collision_detection/collision_event.py
"""

import typing as tp
from amoginarium.shared.utility import Vec2

class CollisionEvent[T]:
    __slots__ = ("group_id", "other_entity", "position", "normal")
    group_id: int
    other_entity: T
    position: Vec2
    normal: Vec2

    def __init__(
            self,
            group_id: int,
            other_entity: T,
            position: Vec2,
            normal: Vec2,
    ) -> None:
        self.group_id = group_id
        self.other_entity = other_entity
        self.position = position
        self.normal = normal

type CollisionCallback = tp.Callable[[CollisionEvent[tp.Any]], None]