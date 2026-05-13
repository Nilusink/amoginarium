"""
amoginarium/shared/collision_detection/_collision_event.py

Project: amoginarium
Created: 13.05.2026
Authors: LukasKrah
"""

from ..utility import Vec2


class CollisionEvent[T]:
    """
    Collision event (start or end) data structure.

    :ivar collision_id: Unique identifier for this specific collision
    :ivar relation_id: Identifier of the relationship between the two colliding groups.
    :ivar group_id: Identifier of the other group involved in the collision.
    :ivar other_entity: Reference to the other entity involved in the collision.
    :ivar position: The 2D coordinates where the collision occurred.
    :ivar normal: The collision normal vector.
    :ivar time: The timestamp or frame-time of the collision.
    """
    __slots__ = (
        "collision_id", "relation_id", "group_id", "other_entity", "position",
        "normal", "time"
    )

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
        """
        Initializes a new CollisionEvent instance.
        :param collision_id: Unique identifier for this specific collision.
        :param relation_id: Identifier of the relationship between the two colliding groups.
        :param group_id: Identifier of the other group involved in the collision.
        :param other_entity: Reference to the other entity involved in the collision.
        :param position: The 2D coordinates where the collision occurred.
        :param normal: The collision normal vector.
        :param time: The timestamp or frame-time of the collision.
        """
        self.collision_id = collision_id
        self.relation_id = relation_id
        self.group_id = group_id
        self.other_entity = other_entity
        self.position = position
        self.normal = normal
        self.time = time

    def __repr__(self) -> str:
        """
        Returns a string representation of the CollisionEvent.
        :return: String containing the event's metadata and collision details.
        """
        return (
            f"<CollisionEvent(col_id={self.collision_id}, rel_id={self.relation_id}, "
            f"group={self.group_id}, other={self.other_entity}, pos={self.position}, "
            f"norm={self.normal}, time={self.time})>"
        )

