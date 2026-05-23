"""
Collision Manager.

| ``Path``: amoginarium/shared/collision_detection/_collision_manager.pyi
| ``Project``: amoginarium
| ``Created``: 17.04.2026
| ``Authors``: LukasKrah
"""

import typing as tp

from amoginarium.shared.utility import Vec2

from ._collision_event import CollisionEvent
from ._collision_types import CollisionCallbackType, CollisionEntityIDType
from ._collision_types import CollisionExceptionIDType, CollisionGroupIDType
from ._collision_types import CollisionHitboxType, CollisionRelationIDType

class CollisionManager:
    """
    A collision manager represents a collision system with
    - different groups
    - relations between the groups
    - different entities registered in the groups
    It handles:
    - Calling collision_start and collision_end callbacks
    - Using a grid to speed up collision detection.
    """

    def __init__(
        self,
        base_cell_size: float = 100.0,
        level_dividers: list[int] | None = None,
    ) -> None:
        """
        Create a new CollisionSystemManager
        :param base_cell_size: Size of one base cell of the grid (height and width)
        :param level_dividers: Each number creates a new sub-grid for each cell
            recursive dividing the previous cells size by the given number.
        """

    def add_group(
        self,
        max_level: int,
        is_static: bool = False,
        hitbox_type: CollisionHitboxType = CollisionHitboxType.aabb,
    ) -> CollisionGroupIDType:
        """
        Add a new entity group
        :param max_level: Until which level of the grid the entities in this group
            are registered. If the entities in the group tend to be bigger than
            a cell level size, they probably shouldn't register in it
        :param is_static: Whether the entities in this group are static (don't move)
            or dynamic (move). Static entities can also be registered as dynamic.
            This is a pure speed improvement!
        :param hitbox_type: The type of the hitbox of the entities in this group.
            For simplicity, only one type is supported per group.
        :return: The unique ID of the new group.
        """

    def clear_all_entities(self) -> None:
        """
        Deletes all registered entities.
        """

    def register_entity(
        self,
        group_id: CollisionGroupIDType,
        instance: tp.Any,
        position: Vec2 | None = None,
        size: Vec2 | None = None,
        centered: bool = False,
        rotation: float = 0.0,
        positions: list[Vec2] | None = None,
        radius: float | None = None,
        ignore_collisions: CollisionExceptionIDType
        | list[CollisionExceptionIDType]
        | None = None,
        is_active: bool = True,
    ) -> CollisionEntityIDType:
        """
        Register a new entity in the collision system
        :param group_id: Which group the entity belongs to
        :param instance: Instance of the entity;
            that will be given as the first argument to the collision callbacks
        :param position: Position of the entity. Relevant for point, aabb, circle, obb.
        :param size: Size of the entity. Relevant for aabb, obb.
            If radius is not given for circles size.x / 2 is used instead.
        :param centered: Whether the position represents the center or top-left.
             Relevant for aabb, circle, obb.
        :param rotation: Rotation of the entity in radians. Only relevant for obb.
        :param positions: List of vertices for polygonal/trinagle hitboxes.
            If the rotation or shape changes during one update/calculation, the new
            shape is used and the old shape is formed around the first position.
        :param radius: Radius for circular hitboxes.
        :param ignore_collisions: List of or a single collision exception rule/s.
            Any 2 entities that have the same exception ID will not collide.
        :param is_active: Whether the entity is alive.
            Useful for disabling collisions temporarily.
        :return: The unique ID of the new entity.
        """

    def delete_entity(
        self,
        group_id: CollisionGroupIDType,
        entity_id: CollisionEntityIDType,
    ) -> None:
        """
        Delete an entity from the collision system
        :param group_id: Which group the entity belongs to
        :param entity_id: The unique ID of the entity to delete.
        """

    def update_entity(
        self,
        group_id: CollisionGroupIDType,
        entity_id: CollisionEntityIDType,
        position: Vec2 | None = None,
        size: Vec2 | None = None,
        centered: bool | None = None,
        rotation: float | None = None,
        positions: list[Vec2] | None = None,
        radius: float | None = None,
        ignore_collisions: int | list[int] | None = None,
        is_active: bool | None = None,
        shift_history: bool = True,
    ) -> None:
        """
        Update an entity of the collision system.
        :param group_id: Which group the entity belongs to
        :param entity_id: The unique ID of the entity to update
        :param position: Position of the entity. Relevant for point, aabb, circle, obb.
        :param size: Size of the entity. Relevant for aabb, obb.
            If radius is not given for circles size.x / 2 is used instead.
        :param centered: Whether the position represents the center or top-left.
             Relevant for aabb, circle, obb.
        :param rotation: Rotation of the entity in radians. Only relevant for obb.
        :param positions: List of vertices for polygonal/trinagle hitboxes.
            If the rotation or shape changes during one update/calculation, the new
            shape is used and the old shape is formed around the first position.
        :param radius: Radius for circular hitboxes.
        :param ignore_collisions: List of or a single collision exception rule/s.
            Any 2 entities that have the same exception ID will not collide.
        :param is_active: Whether the entity is alive.
            Useful for disabling collisions temporarily.
        :param shift_history: Whether to shift the current parameters to the
            parameter history. If update_entity is called multiple times per
            calculation, normally, this should only be True the first time it is called.
        """

    def create_relation(
        self,
        a_group_id: CollisionGroupIDType,
        b_group_id: CollisionGroupIDType,
        a_collision_start_callback: CollisionCallbackType | None = None,
        a_collision_end_callback: CollisionCallbackType | None = None,
        b_collision_start_callback: CollisionCallbackType | None = None,
        b_collision_end_callback: CollisionCallbackType | None = None,
    ) -> CollisionRelationIDType:
        """
        Create a new collision relation between two groups.
        :param a_group_id: ID of the first group involved in the relation
        :param b_group_id: ID of the second group involved in the relation
        :param a_collision_start_callback: Callback that group A
            will get called on a collision start.
        :param a_collision_end_callback: Callback that group A
            will get called on a collision end.
        :param b_collision_start_callback: Callback that group B
            will get called on a collision start.
        :param b_collision_end_callback: Callback that group B
            will get called on a collision end.
        :return: The unique ID of this new relation.
        """

    def calculate_all_collisions(self) -> None:
        """
        Starts the collision calculation process.
        Should only be called once per frame.
        """

    def calculate_collisions(self, relation_ids: list[CollisionRelationIDType]) -> None:
        """
        Start calculation of specific relations.
        :param relation_ids: List of relation IDs to calculate.
        """

    def manual_collision(
        self,
        group_ids: list[CollisionGroupIDType],
        start_position: Vec2,
        end_position: Vec2,
        size: Vec2 | None = None,
        hitbox_type: str = "point",
        centered: bool = False,
        rotation: float = 0.0,
        start_positions: list[Vec2] | None = None,
        radius: float | None = None,
        ignore_collisions: int | list[int] | None = None,
    ) -> list[CollisionEvent]:
        """
        Run a manual collision without registering an entity or notifying
        other entities about it.

        There is no need to register the entity, create a group,
        or create any relations.

        :param group_ids: Which groups to collide with (essentially relations)
        :param start_position: The start position of the collision trace.
            Relevant for point, aabb, circle, obb. Disregarded for triangle and polygon.
        :param end_position: The end position of the collision trace.
            For triangle and polygon this represents the end position of the first point.
        :param size: Size of the entity. Relevant for aabb, obb.
            If radius is not given for circles size.x / 2 is used instead.
        :param hitbox_type: Which hitbox type to use.
        :param centered: Whether the position represents the center or top-left.
             Relevant for aabb, circle, obb.
        :param rotation: Rotation of the entity in radians. Only relevant for obb.
        :param start_positions: List of vertices for polygonal/trinagle hitboxes.
            The end positions are calculated by the movement of the first position of
            this list to the end_position.
        :param radius: Radius for circular hitboxes.
        :param ignore_collisions: List of or a single collision exception rule/s.
            Any 2 entities that have the same exception ID will not collide.
        :return: List of CollisionEvents
        """

    def get_hitbox(self, group_id: CollisionGroupIDType) -> CollisionHitboxType | None:
        """
        Debug-Method to get the hitbox type of any group.
        :param group_id: The group ID.
        :return: The hitbox type of the group or None if group does not exist.
        """

    def get_points(
        self, group_id: CollisionGroupIDType, entity_id: CollisionEntityIDType
    ) -> list[Vec2]:
        """
        Debug-method to get the points of a hitbox.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: List of points of the hitbox
            For circles only 8 points are returned.
            I recommend using get_position and get_radius for them instead!
        """

    def get_position(
        self, group_id: CollisionGroupIDType, entity_id: CollisionEntityIDType
    ) -> Vec2 | None:
        """
        Debug-method to get the position of an entity.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: The position of the entity if it exists. Otherwise, None.
        """

    def get_size(
        self, group_id: CollisionGroupIDType, entity_id: CollisionEntityIDType
    ) -> Vec2 | None:
        """
        Debug-method to get the size of an entity.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: The size of the entity if it exists. Otherwise, None.
        """

    def get_radius(self, group_id: int, entity_id: int) -> float:
        """
        Debug-method to get the radius of an entity.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: The radius of the entity if it exists. Otherwise, 0.
        """
