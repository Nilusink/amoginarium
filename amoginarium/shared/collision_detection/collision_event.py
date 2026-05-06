import typing as tp
from amoginarium.shared.utility import Vec2


class CollisionEvent[T]:
    __slots__ = ("collision_id", "relation_id", "group_id", "other_entity", "position", "normal", "time")
    collision_id: int
    relation_id: int
    group_id: int
    other_entity: T
    position: Vec2
    normal: Vec2
    time: float

    def __init__(
            self,
            collision_id: int,
            relation_id: int,
            group_id: int,
            other_entity: T,
            position: Vec2,
            normal: Vec2,
            time: float,
    ) -> None:
        self.collision_id = collision_id
        self.relation_id = relation_id
        self.group_id = group_id
        self.other_entity = other_entity
        self.position = position
        self.normal = normal
        self.time = time

    def __repr__(self) -> str:
        return f"<CollisionEvent(col_id={self.collision_id}, rel_id={self.relation_id}, group={self.group_id}, other={self.other_entity}, pos={self.position}, norm={self.normal}, time={self.time})>"


type CollisionCallback = tp.Callable[[tp.Any, int, list[CollisionEvent[tp.Any]]], list[bool] | None]
