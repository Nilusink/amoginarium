# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False
# noinspection PyUnresolvedReferences
"""
Implements the CollisionManager class.

| ``Path``: amoginarium/shared/collision_detection/_collision_manager.pyx
| ``Project``: amoginarium
| ``Created``: 17.04.2026
| ``Authors``: LukasKrah
"""

# noinspection PyUnresolvedReferences

from ._collision_manager cimport ActiveColData, CollisionGroupStruct, CollisionManager
from ._collision_manager cimport CollisionRelationStruct, DeferredDeletion, EntityData
from ._collision_methods cimport aabb_aabb_swept, aabb_circle_swept
from ._collision_methods cimport circle_circle_swept, circle_poly_swept
from ._collision_methods cimport poly_poly_swept

from ..utility import Vec2
from ._collision_event import CollisionEvent
from ._collision_types import CollisionCallbackType, CollisionEntityIDType
from ._collision_types import CollisionExceptionIDType, CollisionGroupIDType
from ._collision_types import CollisionRelationIDType

# noinspection PyUnresolvedReferences

from cpython.ref cimport Py_DECREF, Py_INCREF, PyObject
from cython.operator cimport dereference, preincrement
from libc.math cimport cos, floor, sin, sqrt
from libc.stdint cimport uint64_t
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector


# noinspection DuplicatedCode
cdef class CollisionManager:
    """
    A collision manager represents a collision system with
    - different groups
    - relations between the groups
    - different entities registered in the groups
    It handles:
    - Calling collision_start and collision_end callbacks
    - Using a grid to speed up collision detection
    """

    def __init__(
            self,
            double base_cell_size=1000.0,  # type: float
            object level_dividers=None  # type: list[int] | None
    ) -> None:
        """
        Create a new CollisionSystemManager
        :param base_cell_size: Size of one base cell of the grid (height and width)
        :param level_dividers: Each number creates a new sub-grid for each cell
            recursive dividing the previous cells size by the given number
        """
        cdef double current_size

        self.base_cell_size = base_cell_size
        self.cell_sizes.push_back(base_cell_size)

        current_size = base_cell_size
        if level_dividers:
            for div in level_dividers:  # type: ignore
                current_size /= div
                self.cell_sizes.push_back(current_size)

        self.grids.resize(self.cell_sizes.size())
        self.group_instances = []
        self.relation_callbacks = []
        self.next_col_id = 1

    def add_group(
            self,
            int max_level,  # type: int
            bint is_static=False,  # bool (bint)
            str hitbox_type="aabb"  # CollisionHitboxType
    ) -> int:  # CollisionGroupIDType
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
        :return: The unique ID of the new group
        """
        cdef size_t total_grid_levels
        cdef int new_group_id  # type: CollisionGroupIDType
        cdef CollisionGroupStruct new_group
        cdef int current_level

        # todo - test if levels work correct?! i think 0 is what i though is 1 xD
        # max_level: If to high set to maximum
        total_grid_levels = self.cell_sizes.size()
        if max_level >= <int> total_grid_levels:
            max_level = <int> total_grid_levels - 1

        # Create new group
        new_group_id = <int> self.groups.size()
        new_group.id = new_group_id
        new_group.max_level = max_level
        new_group.is_static = is_static

        # Set hitbox_type as integer for speed reasons.
        new_group.hitbox_type = 0
        if hitbox_type == "obb":
            new_group.hitbox_type = 1
        elif hitbox_type == "triangle":
            new_group.hitbox_type = 2
        elif hitbox_type == "polygon":
            new_group.hitbox_type = 3
        elif hitbox_type == "point":
            new_group.hitbox_type = 4
        elif hitbox_type == "circle":
            new_group.hitbox_type = 5

        self.groups.push_back(new_group)
        self.group_instances.append([])

        for current_level in range(max_level + 1):
            self.grids[current_level][new_group_id] = unordered_map[
                uint64_t, vector[int]]()

        return new_group_id

    def clear_all_entities(self) -> None:
        """
        Deletes all registered entities
        """
        cdef size_t relation_idx
        cdef size_t group_idx
        cdef int grid_level
        cdef CollisionGroupStruct * current_group
        cdef size_t total_relations
        cdef size_t total_groups

        self.pending_deletions.clear()

        total_relations = self.relations.size()
        for relation_idx in range(total_relations):
            it = self.relations[relation_idx].active_cols.begin()
            while it != self.relations[relation_idx].active_cols.end():
                Py_DECREF(<object>dereference(it).second.normal_a)
                Py_DECREF(<object>dereference(it).second.normal_b)
                preincrement(it)

            self.relations[relation_idx].active_cols.clear()
            self.relations[relation_idx].updated_cols.clear()

        total_groups = self.groups.size()
        for group_idx in range(total_groups):
            current_group = &self.groups[group_idx]
            current_group.entities.clear()
            current_group.free_ids.clear()

            self.group_instances[group_idx].clear()

            for grid_level in range(current_group.max_level + 1):
                self.grids[grid_level][group_idx].clear()

    def register_entity(
            self,
            int group_id,  # type: CollisionGroupIDType
            object instance,  # Instance for callbacks
            object position=None,  # Vec2 | None
            object size=None,  # Vec2 | None
            bint centered=False,  # bool (bint)
            double rotation=0.0,  # float
            list positions=None,  # list[Vec2] | None
            object radius=None,  # float | None
            object ignore_collisions=None,  # int | list[int] | None
            bint is_active=True  # bool (bint)
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
        :param is_active: Whether the entity is active.
            Useful for disabling collisions temporarily.
        :return: The unique ID of the new entity
        """
        if group_id < 0 or group_id >= self.groups.size():
            # Group does not exist!
            return -1

        cdef CollisionGroupStruct * target_group = &self.groups[group_id]
        cdef int entity_id
        cdef int grid_level
        cdef EntityData new_entity_data
        cdef double calculated_radius = 0.0
        cdef size_t num_free_ids

        # Use radius if given, else size.x / 2, else None
        if radius is not None:
            calculated_radius = radius
        elif size is not None:
            calculated_radius = size.x / 2.0

        num_free_ids = target_group.free_ids.size()
        # Reuse a deleted entities spot
        if num_free_ids > 0:
            # Use the last free ID
            entity_id = target_group.free_ids.back()
            target_group.free_ids.pop_back()

            # Set different parameters of entity
            target_group.entities[entity_id].alive = True
            target_group.entities[entity_id].is_active = is_active
            target_group.entities[entity_id].hitbox_type = target_group.hitbox_type
            target_group.entities[entity_id].is_centered = centered
            target_group.entities[entity_id].rot = rotation
            target_group.entities[entity_id].radius = calculated_radius

            # Create ignore_collisions
            target_group.entities[entity_id].ignore_collisions.clear()
            if ignore_collisions is not None:
                if isinstance(ignore_collisions, list):
                    for ignore_rule in ignore_collisions:  # type: ignore
                        target_group.entities[entity_id].ignore_collisions.push_back(
                            ignore_rule)
                else:
                    target_group.entities[entity_id].ignore_collisions.push_back(
                        ignore_collisions)

            # Position
            if position is not None:
                target_group.entities[entity_id].position_x_old = position.x
                target_group.entities[entity_id].position_y_old = position.y
                target_group.entities[entity_id].position_x_new = position.x
                target_group.entities[entity_id].position_y_new = position.y
            else:
                target_group.entities[entity_id].position_x_old = 0.0
                target_group.entities[entity_id].position_y_old = 0.0
                target_group.entities[entity_id].position_x_new = 0.0
                target_group.entities[entity_id].position_y_new = 0.0

            # Size
            if size is not None:
                target_group.entities[entity_id].size_x = size.x
                target_group.entities[entity_id].size_y = size.y
            else:
                target_group.entities[entity_id].size_x = 0.0
                target_group.entities[entity_id].size_y = 0.0

            target_group.entities[entity_id].vector_x_old.clear()
            target_group.entities[entity_id].vector_y_old.clear()
            target_group.entities[entity_id].vector_x_new.clear()
            target_group.entities[entity_id].vector_y_new.clear()
            target_group.entities[entity_id].axes_x.clear()
            target_group.entities[entity_id].axes_y.clear()

            for grid_level in range(target_group.max_level + 1):
                target_group.entities[entity_id].bound_min_x[grid_level] = -2147483647
                target_group.entities[entity_id].bound_min_y[grid_level] = -2147483647
                target_group.entities[entity_id].bound_max_x[grid_level] = -2147483647
                target_group.entities[entity_id].bound_max_y[grid_level] = -2147483647
                target_group.entities[entity_id].grid_keys[grid_level].clear()

            self.group_instances[group_id][entity_id] = instance
        else:
            # Create new entity id
            entity_id = <int> target_group.entities.size()
            new_entity_data.id = entity_id

            # Set different parameters of entity
            new_entity_data.alive = True
            new_entity_data.is_active = is_active
            new_entity_data.hitbox_type = target_group.hitbox_type
            new_entity_data.is_centered = centered
            new_entity_data.rot = rotation
            new_entity_data.radius = calculated_radius

            # Create ignore_collisions
            new_entity_data.ignore_collisions.clear()
            if ignore_collisions is not None:
                if isinstance(ignore_collisions, list):
                    for ignore_rule in ignore_collisions:  # type: ignore
                        new_entity_data.ignore_collisions.push_back(ignore_rule)
                else:
                    new_entity_data.ignore_collisions.push_back(ignore_collisions)

            # Position
            if position is not None:
                new_entity_data.position_x_old = position.x
                new_entity_data.position_y_old = position.y
                new_entity_data.position_x_new = position.x
                new_entity_data.position_y_new = position.y
            else:
                new_entity_data.position_x_old = 0.0
                new_entity_data.position_y_old = 0.0
                new_entity_data.position_x_new = 0.0
                new_entity_data.position_y_new = 0.0

            # Size
            if size is not None:
                new_entity_data.size_x = size.x
                new_entity_data.size_y = size.y
            else:
                new_entity_data.size_x = 0.0
                new_entity_data.size_y = 0.0

            new_entity_data.grid_keys.resize(target_group.max_level + 1)
            new_entity_data.bound_min_x.resize(target_group.max_level + 1, -2147483647)
            new_entity_data.bound_min_y.resize(target_group.max_level + 1, -2147483647)
            new_entity_data.bound_max_x.resize(target_group.max_level + 1, -2147483647)
            new_entity_data.bound_max_y.resize(target_group.max_level + 1, -2147483647)

            target_group.entities.push_back(new_entity_data)
            self.group_instances[group_id].append(instance)

        # Use update to set the rest to have less duplicate code
        self.update_entity(group_id, entity_id, position, size, centered, rotation,
                           positions, True, radius,
                           ignore_collisions)
        return entity_id

    def delete_entity(
            self,
            int group_id,  # CollisionGroupIDType
            int entity_id  # CollisionEntityIDType
    ) -> None:
        """
        Delete an entity from the collision system
        :param group_id: Which group the entity belongs to
        :param entity_id: The unique ID of the entity to delete
        """
        # Check if group exists
        if group_id < 0 or group_id >= self.groups.size():
            return

        cdef CollisionGroupStruct * target_group = &self.groups[group_id]
        cdef EntityData * target_entity
        cdef DeferredDeletion deletion_request
        cdef size_t total_entities

        # check if entity exists in the group
        total_entities = target_group.entities.size()
        if entity_id < 0 or entity_id >= <int> total_entities:
            return

        # Check if entity has already been deleted / marked for deletion
        target_entity = &target_group.entities[entity_id]
        if not target_entity.alive:
            return

        target_entity.alive = False

        # Create a pending deletion request
        deletion_request.group_id = group_id
        deletion_request.entity_id = entity_id
        self.pending_deletions.push_back(deletion_request)

    cdef void _cleanup_entity_collisions(
            self,
            int group_id,  # type: CollisionGroupIDType
            int entity_id  # type: CollisionEntityIDType
    ):
        """
        End all active collisions that this entity is involved in
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        """
        cdef CollisionRelationStruct * relation
        cdef uint64_t pair_key
        cdef uint64_t entity_a_id, entity_b_id
        cdef tuple callbacks
        cdef size_t total_relations
        cdef size_t i, k, to_remove_size
        cdef vector[uint64_t] to_remove
        cdef int group_a_id, group_b_id, relation_id
        cdef object instance_a, instance_b
        cdef int col_id
        cdef double norm_x, norm_y

        total_relations = self.relations.size()
        for i in range(total_relations):
            relation = &self.relations[i]
            relation_id = relation.id
            group_a_id = relation.group_a_id
            group_b_id = relation.group_b_id

            if group_a_id == group_id or group_b_id == group_id:
                callbacks = self.relation_callbacks[i]
                to_remove.clear()

                it = relation.active_cols.begin()
                while it != relation.active_cols.end():
                    pair_key = dereference(it).first
                    col_id = dereference(it).second.col_id
                    norm_a = <object>dereference(it).second.normal_a
                    norm_b = <object>dereference(it).second.normal_b

                    entity_a_id = pair_key >> 32
                    entity_b_id = pair_key & 0xFFFFFFFF

                    # If either A or B is the entity being deactivated/deleted
                    if (group_a_id == group_id and entity_a_id == entity_id) or (
                            group_b_id == group_id and entity_b_id == entity_id):
                        if self.groups[group_a_id].entities.size() > entity_a_id and \
                                self.groups[
                                    group_b_id].entities.size() > entity_b_id:
                            if len(self.group_instances[
                                       group_a_id]) > entity_a_id and len(
                                self.group_instances[group_b_id]) > entity_b_id:
                                instance_a = self.group_instances[group_a_id][
                                    entity_a_id]
                                instance_b = self.group_instances[group_b_id][
                                    entity_b_id]

                                if instance_a is not None and instance_b is not None:

                                    # Trigger End for A (callbacks[1])
                                    if callbacks[1] is not None:
                                        ev_a = CollisionEvent(
                                            col_id,
                                            relation_id,
                                            group_b_id,
                                            instance_b,
                                            Vec2().from_cartesian(
                                                self.groups[group_a_id].entities[
                                                    entity_a_id].position_x_new,
                                                self.groups[group_a_id].entities[
                                                    entity_a_id].position_y_new),
                                            norm_a,
                                            1.0
                                        )
                                        callbacks[1](instance_a, group_b_id, [ev_a])

                                    # Trigger End for B (callbacks[3])
                                    if callbacks[3] is not None:
                                        ev_b = CollisionEvent(
                                            col_id,
                                            relation_id,
                                            group_a_id,
                                            instance_a,
                                            Vec2().from_cartesian(
                                                self.groups[group_b_id].entities[
                                                    entity_b_id].position_x_new,
                                                self.groups[group_b_id].entities[
                                                    entity_b_id].position_y_new),
                                            norm_b,
                                            1.0
                                        )
                                        callbacks[3](instance_b, group_a_id, [ev_b])

                        to_remove.push_back(pair_key)

                    preincrement(it)

                to_remove_size = to_remove.size()
                for k in range(to_remove_size):
                    Py_DECREF(<object>relation.active_cols[to_remove[k]].normal_a)
                    Py_DECREF(<object>relation.active_cols[to_remove[k]].normal_b)
                    relation.active_cols.erase(to_remove[k])

    cdef void _flush_deletions(self):
        cdef size_t i, pd_sz
        cdef int g_id, e_id
        cdef CollisionGroupStruct * group
        cdef EntityData * ed
        cdef DeferredDeletion dd

        while self.pending_deletions.size() > 0:
            pd_sz = self.pending_deletions.size()

            for i in range(pd_sz):
                dd = self.pending_deletions[i]

                g_id = dd.group_id
                e_id = dd.entity_id

                self._cleanup_entity_collisions(g_id, e_id)

                group = &self.groups[g_id]
                ed = &group.entities[e_id]

                if e_id < len(self.group_instances[g_id]):
                    self.group_instances[g_id][e_id] = None

                self._remove_entity_from_grid(g_id, e_id)

                group.free_ids.push_back(e_id)

            self.pending_deletions.erase(self.pending_deletions.begin(), self.pending_deletions.begin() + pd_sz)

    def update_entity(
            self,
            int group_id,  # CollisionGroupIDType
            int entity_id,  # CollisionEntityIDType
            object position=None,  # Vec2 | None
            object size=None,  # Vec2 | None
            object centered=None,  # bint | None
            object rotation=None,  # double | None
            list positions=None,  # list[Vec2] | None
            bint shift_history=True,  # bool (bint)
            object radius=None,  # double | None
            object ignore_collisions=None,  # int | list[int] | None
            object is_active=None  # bool (bint)
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
        # Check that group and entity exist
        if group_id < 0 or group_id >= self.groups.size():
            return
        if entity_id < 0 or entity_id >= self.groups[group_id].entities.size():
            return

        cdef EntityData * entity_data = &self.groups[group_id].entities[entity_id]

        cdef double previous_position_x_new, previous_position_y_new
        cdef double coord_x, coord_y
        cdef double half_width, half_height
        cdef double cos_rotation, sin_rotation
        cdef double axis_x, axis_y
        cdef double delta_x, delta_y
        cdef double length
        cdef double pivot_x, pivot_y
        cdef size_t i, num_v
        cdef size_t axes_x_size
        cdef size_t vector_x_new_size, vector_x_new_size_2
        cdef size_t vector_x_old_size2
        cdef bint old_is_active, transitioned_to_active, transitioned_to_inactive

        # If entity is already dead
        if not entity_data.alive:
            return

        # Determine if the entity transitioned its state
        old_is_active = entity_data.is_active
        transitioned_to_active = False
        transitioned_to_inactive = False

        if is_active is not None:
            entity_data.is_active = is_active
            if old_is_active and not entity_data.is_active:
                transitioned_to_inactive = True
            elif not old_is_active and entity_data.is_active:
                transitioned_to_active = True

        # Inactive entities get removed from the grid and all active collisions end
        if transitioned_to_inactive:
            self._cleanup_entity_collisions(group_id, entity_id)
            self._remove_entity_from_grid(group_id, entity_id)

        # If update is called multiple times per frame, only shift the positions once
        # Preferably, this should be before editing the first position
        # so on the first call
        if shift_history:
            entity_data.position_x_old = entity_data.position_x_new
            entity_data.position_y_old = entity_data.position_y_new
            entity_data.vector_x_old = entity_data.vector_x_new
            entity_data.vector_y_old = entity_data.vector_y_new

        previous_position_x_new = entity_data.position_x_new
        previous_position_y_new = entity_data.position_y_new

        # Update different parameters of the entity
        if centered is not None:
            entity_data.is_centered = centered
        if size is not None:
            entity_data.size_x = size.x
            entity_data.size_y = size.y
        if rotation is not None:
            entity_data.rot = rotation
        if position is not None:
            entity_data.position_x_new = position.x
            entity_data.position_y_new = position.y

        if radius is not None:
            entity_data.radius = radius
        elif size is not None:
            entity_data.radius = size.x / 2.0

        if ignore_collisions is not None:
            entity_data.ignore_collisions.clear()
            if isinstance(ignore_collisions, list):
                for ig in ignore_collisions:  # type: ignore
                    entity_data.ignore_collisions.push_back(ig)
            else:
                entity_data.ignore_collisions.push_back(ignore_collisions)

        # aabb
        if entity_data.hitbox_type == 0:
            if entity_data.is_centered:
                coord_x = entity_data.position_x_new - (entity_data.size_x / 2.0)
                coord_y = entity_data.position_y_new - (entity_data.size_y / 2.0)
            else:
                coord_x = entity_data.position_x_new
                coord_y = entity_data.position_y_new
            entity_data.vector_x_new.clear()
            entity_data.vector_y_new.clear()
            entity_data.vector_x_new.push_back(coord_x)
            entity_data.vector_y_new.push_back(coord_y)
            entity_data.vector_x_new.push_back(coord_x + entity_data.size_x)
            entity_data.vector_y_new.push_back(coord_y)
            entity_data.vector_x_new.push_back(coord_x + entity_data.size_x)
            entity_data.vector_y_new.push_back(coord_y + entity_data.size_y)
            entity_data.vector_x_new.push_back(coord_x)
            entity_data.vector_y_new.push_back(coord_y + entity_data.size_y)

            axes_x_size = entity_data.axes_x.size()
            if axes_x_size == 0:
                entity_data.axes_x.push_back(1.0)
                entity_data.axes_y.push_back(0.0)
                entity_data.axes_x.push_back(0.0)
                entity_data.axes_y.push_back(1.0)

        # obb
        elif entity_data.hitbox_type == 1:
            cos_rotation = cos(entity_data.rot)
            sin_rotation = sin(entity_data.rot)
            entity_data.vector_x_new.clear()
            entity_data.vector_y_new.clear()

            if entity_data.is_centered:
                coord_x = entity_data.position_x_new
                coord_y = entity_data.position_y_new
                half_width = entity_data.size_x / 2.0
                half_height = entity_data.size_y / 2.0
                entity_data.vector_x_new.push_back(
                    coord_x - half_width * cos_rotation + half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    coord_y - half_width * sin_rotation - half_height * cos_rotation)
                entity_data.vector_x_new.push_back(
                    coord_x + half_width * cos_rotation + half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    coord_y + half_width * sin_rotation - half_height * cos_rotation)
                entity_data.vector_x_new.push_back(
                    coord_x + half_width * cos_rotation - half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    coord_y + half_width * sin_rotation + half_height * cos_rotation)
                entity_data.vector_x_new.push_back(
                    coord_x - half_width * cos_rotation - half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    coord_y - half_width * sin_rotation + half_height * cos_rotation)
            else:
                pivot_x = entity_data.position_x_new
                pivot_y = entity_data.position_y_new
                entity_data.vector_x_new.push_back(pivot_x)
                entity_data.vector_y_new.push_back(pivot_y)
                entity_data.vector_x_new.push_back(
                    pivot_x + entity_data.size_x * cos_rotation)
                entity_data.vector_y_new.push_back(
                    pivot_y + entity_data.size_x * sin_rotation)
                entity_data.vector_x_new.push_back(
                    pivot_x + entity_data.size_x * cos_rotation
                    - entity_data.size_y * sin_rotation)
                entity_data.vector_y_new.push_back(
                    pivot_y + entity_data.size_x * sin_rotation
                    + entity_data.size_y * cos_rotation)
                entity_data.vector_x_new.push_back(
                    pivot_x - entity_data.size_y * sin_rotation)
                entity_data.vector_y_new.push_back(
                    pivot_y + entity_data.size_y * cos_rotation)

            entity_data.axes_x.clear()
            entity_data.axes_y.clear()
            entity_data.axes_x.push_back(cos_rotation)
            entity_data.axes_y.push_back(sin_rotation)
            entity_data.axes_x.push_back(-sin_rotation)
            entity_data.axes_y.push_back(cos_rotation)

        # triangle / polygon
        elif entity_data.hitbox_type == 2 or entity_data.hitbox_type == 3:
            if positions is not None:
                entity_data.vector_x_new.clear()
                entity_data.vector_y_new.clear()
                axis_x = 0
                axis_y = 0
                for position in positions:  # type: ignore
                    entity_data.vector_x_new.push_back(position.x)
                    entity_data.vector_y_new.push_back(position.y)
                    axis_x += position.x
                    axis_y += position.y
                entity_data.position_x_new = axis_x / len(positions)
                entity_data.position_y_new = axis_y / len(positions)

                delta_x = entity_data.position_x_new - previous_position_x_new
                delta_y = entity_data.position_y_new - previous_position_y_new
                entity_data.vector_x_old.clear()
                entity_data.vector_y_old.clear()
                vector_x_new_size = entity_data.vector_x_new.size()
                for i in range(vector_x_new_size):
                    entity_data.vector_x_old.push_back(entity_data.vector_x_new[i]
                                                       - delta_x)
                    entity_data.vector_y_old.push_back(entity_data.vector_y_new[i]
                                                       - delta_y)

                entity_data.axes_x.clear()
                entity_data.axes_y.clear()
                num_v = entity_data.vector_x_new.size()
                for i in range(num_v):
                    delta_x = (entity_data.vector_x_new[(i + 1) % num_v]
                               - entity_data.vector_x_new[i])
                    delta_y = (entity_data.vector_y_new[(i + 1) % num_v]
                               - entity_data.vector_y_new[i])
                    length = sqrt(delta_x * delta_x + delta_y * delta_y)
                    if length > 0.0001:
                        entity_data.axes_x.push_back(-delta_y / length)
                        entity_data.axes_y.push_back(delta_x / length)
            elif position is not None:
                delta_x = entity_data.position_x_new - previous_position_x_new
                delta_y = entity_data.position_y_new - previous_position_y_new
                vector_x_new_size_2 = entity_data.vector_x_new.size()
                for i in range(vector_x_new_size_2):
                    entity_data.vector_x_new[i] += delta_x
                    entity_data.vector_y_new[i] += delta_y

        # point
        elif entity_data.hitbox_type == 4:
            entity_data.size_x = 0.0
            entity_data.size_y = 0.0
            entity_data.vector_x_new.clear()
            entity_data.vector_y_new.clear()
            entity_data.vector_x_new.push_back(entity_data.position_x_new)
            entity_data.vector_y_new.push_back(entity_data.position_y_new)

        # circle
        elif entity_data.hitbox_type == 5:
            if entity_data.is_centered:
                coord_x = entity_data.position_x_new
                coord_y = entity_data.position_y_new
            else:
                coord_x = entity_data.position_x_new + entity_data.radius
                coord_y = entity_data.position_y_new + entity_data.radius
            entity_data.vector_x_new.clear()
            entity_data.vector_y_new.clear()
            entity_data.vector_x_new.push_back(coord_x)
            entity_data.vector_y_new.push_back(coord_y)

        vector_x_old_size2 = entity_data.vector_x_old.size()
        if (vector_x_old_size2 == 0 or transitioned_to_active
                or not entity_data.is_active):
            entity_data.vector_x_old = entity_data.vector_x_new
            entity_data.vector_y_old = entity_data.vector_y_new
            entity_data.position_x_old = entity_data.position_x_new
            entity_data.position_y_old = entity_data.position_y_new

        if not self.groups[group_id].is_static:
            if entity_data.is_active:
                self._update_entity_grid(group_id, entity_id)

    cdef void _update_entity_grid(self, int group_id, int entity_id):
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef EntityData * ed = &group.entities[entity_id]

        cdef int lvl
        cdef double c_size
        cdef double min_px, min_py, max_px_o, max_px_n, max_px, max_py_o, max_py_n, max_py
        cdef int min_cx, min_cy, max_cx, max_cy, cx, cy
        cdef uint64_t key
        cdef vector[uint64_t] new_keys
        cdef vector[uint64_t] * old_keys
        cdef bint found
        cdef size_t i, j, keys_sz, new_keys_sz, vx_o_sz, vx_n_sz

        if ed.hitbox_type == 0 or ed.hitbox_type == 4:
            min_px = ed.vector_x_old[0] if ed.vector_x_old[0] < ed.vector_x_new[0] else ed.vector_x_new[0]
            min_py = ed.vector_y_old[0] if ed.vector_y_old[0] < ed.vector_y_new[0] else ed.vector_y_new[0]
            max_px_o = ed.vector_x_old[0] + ed.size_x
            max_px_n = ed.vector_x_new[0] + ed.size_x
            max_px = max_px_o if max_px_o > max_px_n else max_px_n
            max_py_o = ed.vector_y_old[0] + ed.size_y
            max_py_n = ed.vector_y_new[0] + ed.size_y
            max_py = max_py_o if max_py_o > max_py_n else max_py_n
        elif ed.hitbox_type == 5:
            min_px = (ed.vector_x_old[0] if ed.vector_x_old[0] < ed.vector_x_new[0] else ed.vector_x_new[0]) - ed.radius
            min_py = (ed.vector_y_old[0] if ed.vector_y_old[0] < ed.vector_y_new[0] else ed.vector_y_new[0]) - ed.radius
            max_px = (ed.vector_x_old[0] if ed.vector_x_old[0] > ed.vector_x_new[0] else ed.vector_x_new[0]) + ed.radius
            max_py = (ed.vector_y_old[0] if ed.vector_y_old[0] > ed.vector_y_new[0] else ed.vector_y_new[0]) + ed.radius
        else:
            min_px = ed.vector_x_old[0]
            max_px = ed.vector_x_old[0]
            min_py = ed.vector_y_old[0]
            max_py = ed.vector_y_old[0]
            vx_o_sz = ed.vector_x_old.size()
            for j in range(1, vx_o_sz):
                if ed.vector_x_old[j] < min_px:
                    min_px = ed.vector_x_old[j]
                elif ed.vector_x_old[j] > max_px:
                    max_px = ed.vector_x_old[j]
                if ed.vector_y_old[j] < min_py:
                    min_py = ed.vector_y_old[j]
                elif ed.vector_y_old[j] > max_py:
                    max_py = ed.vector_y_old[j]
            vx_n_sz = ed.vector_x_new.size()
            for j in range(vx_n_sz):
                if ed.vector_x_new[j] < min_px:
                    min_px = ed.vector_x_new[j]
                elif ed.vector_x_new[j] > max_px:
                    max_px = ed.vector_x_new[j]
                if ed.vector_y_new[j] < min_py:
                    min_py = ed.vector_y_new[j]
                elif ed.vector_y_new[j] > max_py:
                    max_py = ed.vector_y_new[j]

        for lvl in range(group.max_level + 1):
            c_size = self.cell_sizes[lvl]
            min_cx = <int> floor(min_px / c_size)
            min_cy = <int> floor(min_py / c_size)
            max_cx = <int> floor(max_px / c_size)
            max_cy = <int> floor(max_py / c_size)

            if (min_cx == ed.bound_min_x[lvl] and min_cy == ed.bound_min_y[lvl] and
                    max_cx == ed.bound_max_x[lvl] and max_cy == ed.bound_max_y[lvl]):
                continue

            ed.bound_min_x[lvl] = min_cx
            ed.bound_min_y[lvl] = min_cy
            ed.bound_max_x[lvl] = max_cx
            ed.bound_max_y[lvl] = max_cy

            new_keys.clear()
            for cy in range(min_cy, max_cy + 1):
                for cx in range(min_cx, max_cx + 1):
                    key = (<uint64_t> cx << 32) | (<uint64_t> cy & 0xFFFFFFFF)
                    new_keys.push_back(key)

            old_keys = &ed.grid_keys[lvl]
            keys_sz = old_keys[0].size()
            new_keys_sz = new_keys.size()

            for i in range(keys_sz):
                found = False
                for j in range(new_keys_sz):
                    if old_keys[0][i] == new_keys[j]:
                        found = True
                        break
                if not found: self._remove_from_cell(lvl, group_id, old_keys[0][i], entity_id)

            for i in range(new_keys_sz):
                found = False
                for j in range(keys_sz):
                    if new_keys[i] == old_keys[0][j]:
                        found = True
                        break
                if not found: self.grids[lvl][group_id][new_keys[i]].push_back(entity_id)

            ed.grid_keys[lvl] = new_keys

    cdef void _remove_entity_from_grid(self, int group_id, int entity_id):
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef EntityData * ed = &group.entities[entity_id]
        cdef int lvl
        cdef vector[uint64_t] * keys
        cdef size_t j, keys_sz

        for lvl in range(group.max_level + 1):
            keys = &ed.grid_keys[lvl]
            keys_sz = keys[0].size()
            for j in range(keys_sz):
                self._remove_from_cell(lvl, group_id, keys[0][j], entity_id)
            keys[0].clear()
            ed.bound_min_x[lvl] = -2147483647
            ed.bound_min_y[lvl] = -2147483647
            ed.bound_max_x[lvl] = -2147483647
            ed.bound_max_y[lvl] = -2147483647

    cdef void _remove_from_cell(self, int lvl, int group_id, uint64_t key, int entity_id):
        if self.grids[lvl][group_id].count(key) == 0: return
        cdef vector[int] * cell = &self.grids[lvl][group_id][key]
        cdef size_t i, cell_sz
        cell_sz = cell[0].size()
        for i in range(cell_sz):
            if cell[0][i] == entity_id:
                cell[0][i] = cell[0].back()
                cell[0].pop_back()
                break
        if cell[0].size() == 0:
            self.grids[lvl][group_id].erase(key)

    def create_relation(
            self,
            int a_group_id,  # CollisionGroupIDType
            int b_group_id,  # CollisionGroupIDType
            object a_collision_start_callback=None,  # CollisionCallbackType | None
            object a_collision_end_callback=None,  # CollisionCallbackType | None
            object b_collision_start_callback=None,  # CollisionCallbackType | None
            object b_collision_end_callback=None  # CollisionCallbackType | None
    ) -> int:
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
        :return: The unique ID of this new relation
        """
        cdef int relation_id
        cdef CollisionRelationStruct relation

        relation_id = <int> self.relations.size()
        relation.id = relation_id
        relation.group_a_id = a_group_id
        relation.group_b_id = b_group_id
        self.relations.push_back(relation)
        self.relation_callbacks.append(
            (
                a_collision_start_callback,
                a_collision_end_callback,
                b_collision_start_callback,
                b_collision_end_callback
            )
        )
        return relation_id

    def calculate_all_collisions(self):
        """
        Starts the collision calculation process.
        Should only be called once per frame.
        """
        cdef size_t i, total_relations

        self._flush_deletions()
        total_relations = self.relations.size()
        for i in range(total_relations):
            self._calc_relation(&self.relations[i], self.relation_callbacks[i])

    def calculate_collisions(self, list relation_ids):
        """
        Start calculation of specific relations.
        :param relation_ids: List of relation IDs to calculate.
        """
        cdef int relation_id
        cdef size_t total_relations

        self._flush_deletions()
        total_relations = self.relations.size()
        for relation_id in relation_ids:  # type: ignore
            if 0 <= relation_id < <int> total_relations:
                self._calc_relation(&self.relations[relation_id],
                                    self.relation_callbacks[relation_id])

    cdef void _calc_relation(self, CollisionRelationStruct * rel, tuple callbacks):
        cdef int r_id, g_a_id, g_b_id
        cdef CollisionGroupStruct * ga
        cdef CollisionGroupStruct * gb
        cdef bint is_same
        cdef int check_lvl
        cdef uint64_t pair_key, a_id, b_id
        cdef unordered_set[uint64_t] checked_pairs
        cdef EntityData * ea
        cdef EntityData * eb
        cdef double norm_x, norm_y, t, ev_time
        cdef double imp_ax, imp_ay, imp_bx, imp_by
        cdef vector[uint64_t] * a_keys
        cdef vector[int] * cell_b
        cdef size_t a_idx, k_idx, b_idx, j, k, a_keys_sz, cell_b_sz, ent_sz, to_remove_sz
        cdef int iterations
        cdef bint hit
        cdef double a_dx, a_dy, b_dx, b_dy
        cdef bint is_active_col
        cdef int col_id
        cdef ActiveColData col_data
        cdef int ret_len
        cdef list actual_evs
        cdef object ret
        cdef vector[uint64_t] to_remove
        cdef bint ignore
        cdef size_t ig_a_sz, ig_b_sz, ig_a_i, ig_b_i

        r_id = rel.id
        g_a_id = rel.group_a_id
        g_b_id = rel.group_b_id
        ga = &self.groups[g_a_id]
        gb = &self.groups[g_b_id]
        is_same = (g_a_id == g_b_id)

        check_lvl = ga.max_level if ga.max_level < gb.max_level else gb.max_level

        events_a_start = {}
        events_b_start = {}
        events_a_end = {}
        events_b_end = {}

        checked_pairs.reserve(512)
        rel.updated_cols.clear()

        ent_sz = ga.entities.size()
        for a_idx in range(ent_sz):
            ea = &ga.entities[a_idx]
            if not ea.alive: continue
            if not ea.is_active: continue

            a_keys = &ea.grid_keys[check_lvl]
            a_keys_sz = a_keys[0].size()

            for k_idx in range(a_keys_sz):
                if not ea.alive: break

                if self.grids[check_lvl][g_b_id].count(a_keys[0][k_idx]) == 0:
                    continue

                cell_b = &self.grids[check_lvl][g_b_id][a_keys[0][k_idx]]
                cell_b_sz = cell_b[0].size()

                for b_idx in range(cell_b_sz):
                    b_id = cell_b[0][b_idx]

                    if is_same and ea.id >= b_id:
                        continue

                    eb = &gb.entities[b_id]
                    if not eb.alive: continue
                    if not eb.is_active: continue

                    ignore = False
                    ig_a_sz = ea.ignore_collisions.size()
                    ig_b_sz = eb.ignore_collisions.size()

                    if ig_a_sz > 0 and ig_b_sz > 0:
                        for ig_a_i in range(ig_a_sz):
                            for ig_b_i in range(ig_b_sz):
                                if ea.ignore_collisions[ig_a_i] == eb.ignore_collisions[
                                    ig_b_i]:
                                    ignore = True
                                    break
                            if ignore: break
                    if ignore: continue

                    pair_key = (<uint64_t> ea.id << 32) | <uint64_t> b_id
                    if checked_pairs.count(pair_key): continue
                    checked_pairs.insert(pair_key)

                    is_active_col = (rel.active_cols.count(pair_key) > 0)
                    hit = False

                    if ea.hitbox_type == 0 and eb.hitbox_type == 0:
                        hit = aabb_aabb_swept(
                            ea.vector_x_old[0], ea.vector_y_old[0], ea.vector_x_new[0], ea.vector_y_new[0], ea.size_x,
                            ea.size_y,
                            eb.vector_x_old[0], eb.vector_y_old[0], eb.vector_x_new[0], eb.vector_y_new[0], eb.size_x,
                            eb.size_y,
                            is_active_col, &norm_x, &norm_y, &t)
                    elif ea.hitbox_type == 0 and (eb.hitbox_type == 4 or eb.hitbox_type == 5):
                        hit = aabb_circle_swept(
                            ea.vector_x_old[0], ea.vector_y_old[0], ea.vector_x_new[0], ea.vector_y_new[0], ea.size_x,
                            ea.size_y,
                            eb.vector_x_old[0], eb.vector_y_old[0], eb.vector_x_new[0], eb.vector_y_new[0], eb.radius,
                            is_active_col, &norm_x, &norm_y, &t)
                    elif (ea.hitbox_type == 4 or ea.hitbox_type == 5) and eb.hitbox_type == 0:
                        hit = aabb_circle_swept(
                            eb.vector_x_old[0], eb.vector_y_old[0], eb.vector_x_new[0], eb.vector_y_new[0], eb.size_x,
                            eb.size_y,
                            ea.vector_x_old[0], ea.vector_y_old[0], ea.vector_x_new[0], ea.vector_y_new[0], ea.radius,
                            is_active_col, &norm_x, &norm_y, &t)
                        norm_x = -norm_x
                        norm_y = -norm_y
                    elif (ea.hitbox_type == 4 or ea.hitbox_type == 5) and (
                            eb.hitbox_type == 4 or eb.hitbox_type == 5):
                        hit = circle_circle_swept(
                            ea.vector_x_old[0], ea.vector_y_old[0], ea.vector_x_new[0], ea.vector_y_new[0], ea.radius,
                            eb.vector_x_old[0], eb.vector_y_old[0], eb.vector_x_new[0], eb.vector_y_new[0], eb.radius,
                            is_active_col, &norm_x, &norm_y, &t)
                    elif ea.hitbox_type >= 4 and eb.hitbox_type < 4:
                        a_dx = ea.position_x_new - ea.position_x_old
                        a_dy = ea.position_y_new - ea.position_y_old
                        b_dx = eb.position_x_new - eb.position_x_old
                        b_dy = eb.position_y_new - eb.position_y_old
                        hit = circle_poly_swept(
                            ea.vector_x_old[0], ea.vector_y_old[0], ea.vector_x_new[0], ea.vector_y_new[0], ea.radius,
                            eb.vector_x_old.data(), eb.vector_y_old.data(), eb.vector_x_new.data(),
                            eb.vector_y_new.data(), eb.vector_x_old.size(),
                            eb.axes_x.data(), eb.axes_y.data(), eb.axes_x.size(), b_dx,
                            b_dy,
                            is_active_col, &norm_x, &norm_y, &t
                        )
                    elif ea.hitbox_type < 4 and eb.hitbox_type >= 4:
                        a_dx = ea.position_x_new - ea.position_x_old
                        a_dy = ea.position_y_new - ea.position_y_old
                        b_dx = eb.position_x_new - eb.position_x_old
                        b_dy = eb.position_y_new - eb.position_y_old
                        hit = circle_poly_swept(
                            eb.vector_x_old[0], eb.vector_y_old[0], eb.vector_x_new[0], eb.vector_y_new[0], eb.radius,
                            ea.vector_x_old.data(), ea.vector_y_old.data(), ea.vector_x_new.data(),
                            ea.vector_y_new.data(), ea.vector_x_old.size(),
                            ea.axes_x.data(), ea.axes_y.data(), ea.axes_x.size(), a_dx,
                            a_dy,
                            is_active_col, &norm_x, &norm_y, &t
                        )
                        norm_x = -norm_x
                        norm_y = -norm_y
                    else:
                        a_dx = ea.position_x_new - ea.position_x_old
                        a_dy = ea.position_y_new - ea.position_y_old
                        b_dx = eb.position_x_new - eb.position_x_old
                        b_dy = eb.position_y_new - eb.position_y_old
                        hit = poly_poly_swept(
                            ea.vector_x_old.data(), ea.vector_y_old.data(), ea.vector_x_old.size(),
                            ea.axes_x.data(), ea.axes_y.data(), ea.axes_x.size(), a_dx,
                            a_dy,
                            eb.vector_x_old.data(), eb.vector_y_old.data(), eb.vector_x_old.size(),
                            eb.axes_x.data(), eb.axes_y.data(), eb.axes_x.size(), b_dx,
                            b_dy,
                            is_active_col, &norm_x, &norm_y, &t
                        )

                    if hit:
                        rel.updated_cols.insert(pair_key)

                        if not is_active_col:
                            col_id = self.next_col_id
                            self.next_col_id += 1
                            col_data.col_id = col_id

                            v_norm_a = Vec2().from_cartesian(norm_x, norm_y)
                            v_norm_b = Vec2().from_cartesian(-norm_x, -norm_y)
                            Py_INCREF(v_norm_a)
                            Py_INCREF(v_norm_b)

                            col_data.normal_a = <PyObject*>v_norm_a
                            col_data.normal_b = <PyObject*>v_norm_b

                            rel.active_cols[pair_key] = col_data

                            imp_ax = ea.position_x_old + ((ea.position_x_new - ea.position_x_old) * t)
                            imp_ay = ea.position_y_old + ((ea.position_y_new - ea.position_y_old) * t)
                            imp_bx = eb.position_x_old + ((eb.position_x_new - eb.position_x_old) * t)
                            imp_by = eb.position_y_old + ((eb.position_y_new - eb.position_y_old) * t)

                            ev_time = t if t > 0.0 else 0.0

                            if callbacks[0] is not None:
                                inst_b = self.group_instances[g_b_id][b_id]
                                ev = CollisionEvent(col_id, r_id, g_b_id, inst_b,
                                                    Vec2().from_cartesian(imp_ax,
                                                                          imp_ay),
                                                    <object>col_data.normal_a,
                                                    ev_time)
                                if ea.id not in events_a_start: events_a_start[
                                    ea.id] = []
                                events_a_start[ea.id].append((ev, pair_key))

                            if callbacks[2] is not None:
                                inst_a = self.group_instances[g_a_id][ea.id]
                                ev = CollisionEvent(col_id, r_id, g_a_id, inst_a,
                                                    Vec2().from_cartesian(imp_bx,
                                                                          imp_by),
                                                    <object>col_data.normal_b,
                                                    ev_time)
                                if b_id not in events_b_start: events_b_start[b_id] = []
                                events_b_start[b_id].append((ev, pair_key))

        it = rel.active_cols.begin()
        while it != rel.active_cols.end():
            pair_key = dereference(it).first
            col_id = dereference(it).second.col_id
            norm_a = <object>dereference(it).second.normal_a
            norm_b = <object>dereference(it).second.normal_b
            if rel.updated_cols.find(pair_key) == rel.updated_cols.end():
                a_id = pair_key >> 32
                b_id = pair_key & 0xFFFFFFFF

                if callbacks[1] is not None:
                    inst_a = self.group_instances[g_a_id][a_id]
                    inst_b = self.group_instances[g_b_id][b_id]
                    if inst_a is not None and inst_b is not None:
                        ev = CollisionEvent(col_id, r_id, g_b_id, inst_b,
                                            Vec2().from_cartesian(
                                                ga.entities[a_id].position_x_new,
                                                ga.entities[a_id].position_y_new),
                                            norm_a, 1.0)
                        if a_id not in events_a_end: events_a_end[a_id] = []
                        events_a_end[a_id].append(ev)

                if callbacks[3] is not None:
                    inst_b = self.group_instances[g_b_id][b_id]
                    inst_a = self.group_instances[g_a_id][a_id]
                    if inst_b is not None and inst_a is not None:
                        ev = CollisionEvent(col_id, r_id, g_a_id, inst_a,
                                            Vec2().from_cartesian(
                                                gb.entities[b_id].position_x_new,
                                                gb.entities[b_id].position_y_new),
                                            norm_b, 1.0)
                        if b_id not in events_b_end: events_b_end[b_id] = []
                        events_b_end[b_id].append(ev)

                to_remove.push_back(pair_key)
            preincrement(it)

        to_remove_sz = to_remove.size()
        for k in range(to_remove_sz):
            Py_DECREF(<object>rel.active_cols[to_remove[k]].normal_a)
            Py_DECREF(<object>rel.active_cols[to_remove[k]].normal_b)
            rel.active_cols.erase(to_remove[k])

        # --- START CALLBACKS ---
        for ent_id, evs in events_a_start.items():
            evs.sort(key=lambda e: e[0].time)
            actual_evs = [e[0] for e in evs]
            ret = callbacks[0](self.group_instances[g_a_id][ent_id], g_b_id, actual_evs)
            rel = &self.relations[r_id]
            if ret is not None:
                ret_len = len(ret) if len(ret) < len(evs) else len(evs)
                for idx in range(ret_len):
                    if not ret[idx]:
                        Py_DECREF(<object>rel.active_cols[<uint64_t> evs[idx][1]].normal_a)
                        Py_DECREF(<object>rel.active_cols[<uint64_t> evs[idx][1]].normal_b)
                        rel.active_cols.erase(<uint64_t> evs[idx][1])

        for ent_id, evs in events_b_start.items():
            evs.sort(key=lambda e: e[0].time)
            actual_evs = [e[0] for e in evs]
            ret = callbacks[2](self.group_instances[g_b_id][ent_id], g_a_id, actual_evs)
            rel = &self.relations[r_id]
            if ret is not None:
                ret_len = len(ret) if len(ret) < len(evs) else len(evs)
                for idx in range(ret_len):
                    if not ret[idx]:
                        Py_DECREF(<object>rel.active_cols[<uint64_t> evs[idx][1]].normal_a)
                        Py_DECREF(<object>rel.active_cols[<uint64_t> evs[idx][1]].normal_b)
                        rel.active_cols.erase(<uint64_t> evs[idx][1])

        # --- END CALLBACKS ---
        for ent_id, evs in events_a_end.items():
            callbacks[1](self.group_instances[g_a_id][ent_id], g_b_id, evs)
            rel = &self.relations[r_id]

        for ent_id, evs in events_b_end.items():
            callbacks[3](self.group_instances[g_b_id][ent_id], g_a_id, evs)
            rel = &self.relations[r_id]

    def manual_collision(
            self,
            list group_ids,  # list[CollisionGroupIDType]
            object start_position,  # type: Vec2
            object end_position,  # type: Vec2
            object size=None,  # Vec2 | None
            str hitbox_type="point",  # CollisionHitboxType
            bint centered=False,  # bool (bint)
            double rotation=0.0,  # float
            list start_positions=None,  # list[Vec2 | None
            object radius=None,  # float (double) | None
            object ignore_collisions=None  # int | list[int] | None
    ) -> list:  # list[CollisionEvent]
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
        cdef EntityData entity_data
        cdef double coord_x, coord_y
        cdef double half_width, half_height
        cdef double cos_rotation, sin_rotation
        cdef double axis_x, axis_y
        cdef double delta_x, delta_y
        cdef double length
        cdef double pivot_x, pivot_y
        cdef size_t i, num_vector
        cdef double min_px, min_py
        cdef double max_px_o, max_px_n
        cdef double max_px, max_py_o
        cdef double max_py_n, max_py
        cdef list events
        cdef int group_id
        cdef int grid_level
        cdef int min_cell_x, min_cell_y
        cdef int max_cell_x, max_cell_y
        cdef int grid_cell_x, grid_cell_y
        cdef int b_entity_id
        cdef double cell_size
        cdef double norm_x, norm_y
        cdef double t
        cdef double a_delta_x, a_delta_y
        cdef double b_delta_x, b_delta_y
        cdef double event_time
        cdef uint64_t key
        cdef vector[int] * cell_b
        cdef CollisionGroupStruct * collision_group
        cdef EntityData * entity_data_b
        cdef unordered_set[int] checked
        cdef size_t cell_b_size
        cdef size_t vector_x_old_size_1
        cdef size_t vector_x_old_size_2, vector_x_new_size_2
        cdef size_t vector_x_old_size_3, vector_x_new_size3
        cdef size_t groups_size
        cdef double _radius
        cdef object inst_b
        cdef bint ignore
        cdef size_t ignore_a_size, ignore_b_size
        cdef size_t ignore_a_index, ignore_b_index

        events = []
        entity_data.hitbox_type = 4
        if hitbox_type == "aabb":
            entity_data.hitbox_type = 0
        elif hitbox_type == "obb":
            entity_data.hitbox_type = 1
        elif hitbox_type == "triangle":
            entity_data.hitbox_type = 2
        elif hitbox_type == "polygon":
            entity_data.hitbox_type = 3
        elif hitbox_type == "circle":
            entity_data.hitbox_type = 5

        _radius = 0.0
        if radius is not None:
            _radius = radius
        elif size is not None:
            _radius = size.x / 2.0
        entity_data.radius = _radius

        entity_data.ignore_collisions.clear()
        if ignore_collisions is not None:
            if isinstance(ignore_collisions, list):
                for ig in ignore_collisions:
                    entity_data.ignore_collisions.push_back(ig)
            else:
                entity_data.ignore_collisions.push_back(ignore_collisions)

        entity_data.is_centered = centered
        entity_data.rot = rotation
        entity_data.position_x_old = start_position.x
        entity_data.position_y_old = start_position.y
        entity_data.position_x_new = end_position.x
        entity_data.position_y_new = end_position.y

        if size is not None:
            entity_data.size_x = size.x
            entity_data.size_y = size.y
        else:
            entity_data.size_x = 0.0
            entity_data.size_y = 0.0

        # aabb
        if entity_data.hitbox_type == 0:
            if entity_data.is_centered:
                coord_x = entity_data.position_x_new - (entity_data.size_x / 2.0)
                coord_y = entity_data.position_y_new - (entity_data.size_y / 2.0)
            else:
                coord_x = entity_data.position_x_new
                coord_y = entity_data.position_y_new
            entity_data.vector_x_new.push_back(coord_x)
            entity_data.vector_y_new.push_back(coord_y)
            entity_data.vector_x_new.push_back(coord_x + entity_data.size_x)
            entity_data.vector_y_new.push_back(coord_y)
            entity_data.vector_x_new.push_back(coord_x + entity_data.size_x)
            entity_data.vector_y_new.push_back(coord_y + entity_data.size_y)
            entity_data.vector_x_new.push_back(coord_x)
            entity_data.vector_y_new.push_back(coord_y + entity_data.size_y)
            entity_data.axes_x.push_back(1.0)
            entity_data.axes_y.push_back(0.0)
            entity_data.axes_x.push_back(0.0)
            entity_data.axes_y.push_back(1.0)

        # obb
        elif entity_data.hitbox_type == 1:
            cos_rotation = cos(entity_data.rot)
            sin_rotation = sin(entity_data.rot)
            if entity_data.is_centered:
                half_width = entity_data.size_x / 2.0
                half_height = entity_data.size_y / 2.0
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new - half_width * cos_rotation
                    + half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new - half_width * sin_rotation
                    - half_height * cos_rotation)
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new + half_width * cos_rotation
                    + half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new + half_width * sin_rotation
                    - half_height * cos_rotation)
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new + half_width * cos_rotation
                    - half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new + half_width * sin_rotation
                    + half_height * cos_rotation)
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new - half_width * cos_rotation
                    - half_height * sin_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new - half_width * sin_rotation
                    + half_height * cos_rotation)
            else:
                entity_data.vector_x_new.push_back(entity_data.position_x_new)
                entity_data.vector_y_new.push_back(entity_data.position_y_new)
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new + entity_data.size_x * cos_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new + entity_data.size_x * sin_rotation)
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new + entity_data.size_x * cos_rotation
                    - entity_data.size_y * sin_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new + entity_data.size_x * sin_rotation
                    + entity_data.size_y * cos_rotation)
                entity_data.vector_x_new.push_back(
                    entity_data.position_x_new - entity_data.size_y * sin_rotation)
                entity_data.vector_y_new.push_back(
                    entity_data.position_y_new + entity_data.size_y * cos_rotation)
            entity_data.axes_x.push_back(cos_rotation)
            entity_data.axes_y.push_back(sin_rotation)
            entity_data.axes_x.push_back(-sin_rotation)
            entity_data.axes_y.push_back(cos_rotation)

        # triangle / polygon
        elif entity_data.hitbox_type == 2 or entity_data.hitbox_type == 3:
            if start_positions is not None:
                axis_x = 0
                axis_y = 0
                for start_pos in start_positions:  # type: ignore
                    entity_data.vector_x_old.push_back(start_pos.x)
                    entity_data.vector_y_old.push_back(start_pos.y)
                    axis_x += start_pos.x
                    axis_y += start_pos.y
                entity_data.position_x_old = axis_x / len(start_positions)
                entity_data.position_y_old = axis_y / len(start_positions)

                delta_x = entity_data.position_x_new - entity_data.position_x_old
                delta_y = entity_data.position_y_new - entity_data.position_y_old

                vector_x_old_size_1 = entity_data.vector_x_old.size()
                for i in range(vector_x_old_size_1):
                    entity_data.vector_x_new.push_back(entity_data.vector_x_old[i]
                                                       + delta_x)
                    entity_data.vector_y_new.push_back(entity_data.vector_y_old[i]
                                                       + delta_y)

                num_vector = entity_data.vector_x_new.size()
                for i in range(num_vector):
                    delta_x = (entity_data.vector_x_new[(i + 1) % num_vector]
                               - entity_data.vector_x_new[i])
                    delta_y = (entity_data.vector_y_new[(i + 1) % num_vector]
                               - entity_data.vector_y_new[i])
                    length = sqrt(delta_x * delta_x + delta_y * delta_y)
                    if length > 0.0001:
                        entity_data.axes_x.push_back(-delta_y / length)
                        entity_data.axes_y.push_back(delta_x / length)

        # point
        elif entity_data.hitbox_type == 4:
            entity_data.size_x = 0.0
            entity_data.size_y = 0.0
            entity_data.vector_x_new.push_back(entity_data.position_x_new)
            entity_data.vector_y_new.push_back(entity_data.position_y_new)
            entity_data.vector_x_old.push_back(entity_data.position_x_old)
            entity_data.vector_y_old.push_back(entity_data.position_y_old)

        # circle
        elif entity_data.hitbox_type == 5:
            if entity_data.is_centered:
                coord_x = entity_data.position_x_new
                coord_y = entity_data.position_y_new
            else:
                coord_x = entity_data.position_x_new + entity_data.radius
                coord_y = entity_data.position_y_new + entity_data.radius
            entity_data.vector_x_new.push_back(coord_x)
            entity_data.vector_y_new.push_back(coord_y)

        vector_x_old_size_2 = entity_data.vector_x_old.size()
        vector_x_new_size_2 = entity_data.vector_x_new.size()
        if vector_x_old_size_2 == 0 and vector_x_new_size_2 > 0:
            delta_x = entity_data.position_x_new - entity_data.position_x_old
            delta_y = entity_data.position_y_new - entity_data.position_y_old
            for i in range(vector_x_new_size_2):
                entity_data.vector_x_old.push_back(entity_data.vector_x_new[i]
                                                   - delta_x)
                entity_data.vector_y_old.push_back(entity_data.vector_y_new[i]
                                                   - delta_y)

        # aabb / point
        if entity_data.hitbox_type == 0 or entity_data.hitbox_type == 4:
            min_px = entity_data.vector_x_old[0] if entity_data.vector_x_old[0] < \
                                                    entity_data.vector_x_new[0] else \
                entity_data.vector_x_new[0]
            min_py = entity_data.vector_y_old[0] if entity_data.vector_y_old[0] < \
                                                    entity_data.vector_y_new[0] else \
                entity_data.vector_y_new[0]
            max_px_o = entity_data.vector_x_old[0] + entity_data.size_x
            max_px_n = entity_data.vector_x_new[0] + entity_data.size_x
            max_px = max_px_o if max_px_o > max_px_n else max_px_n
            max_py_o = entity_data.vector_y_old[0] + entity_data.size_y
            max_py_n = entity_data.vector_y_new[0] + entity_data.size_y
            max_py = max_py_o if max_py_o > max_py_n else max_py_n
        # circle
        elif entity_data.hitbox_type == 5:
            min_px = (entity_data.vector_x_old[0] if entity_data.vector_x_old[0] <
                                                     entity_data.vector_x_new[0] else
                      entity_data.vector_x_new[0]) - entity_data.radius
            min_py = (entity_data.vector_y_old[0] if entity_data.vector_y_old[0] <
                                                     entity_data.vector_y_new[0] else
                      entity_data.vector_y_new[0]) - entity_data.radius
            max_px = (entity_data.vector_x_old[0] if entity_data.vector_x_old[0] >
                                                     entity_data.vector_x_new[0] else
                      entity_data.vector_x_new[0]) + entity_data.radius
            max_py = (entity_data.vector_y_old[0] if entity_data.vector_y_old[0] >
                                                     entity_data.vector_y_new[0] else
                      entity_data.vector_y_new[0]) + entity_data.radius
        # obb / triangle / polygon
        else:
            min_px = entity_data.vector_x_old[0]
            max_px = entity_data.vector_x_old[0]
            min_py = entity_data.vector_y_old[0]
            max_py = entity_data.vector_y_old[0]
            vector_x_old_size_3 = entity_data.vector_x_old.size()
            for j in range(1, vector_x_old_size_3):
                if entity_data.vector_x_old[j] < min_px:
                    min_px = entity_data.vector_x_old[j]
                elif entity_data.vector_x_old[j] > max_px:
                    max_px = entity_data.vector_x_old[j]
                if entity_data.vector_y_old[j] < min_py:
                    min_py = entity_data.vector_y_old[j]
                elif entity_data.vector_y_old[j] > max_py:
                    max_py = entity_data.vector_y_old[j]
            vector_x_new_size3 = entity_data.vector_x_new.size()
            for j in range(vector_x_new_size3):
                if entity_data.vector_x_new[j] < min_px:
                    min_px = entity_data.vector_x_new[j]
                elif entity_data.vector_x_new[j] > max_px:
                    max_px = entity_data.vector_x_new[j]
                if entity_data.vector_y_new[j] < min_py:
                    min_py = entity_data.vector_y_new[j]
                elif entity_data.vector_y_new[j] > max_py:
                    max_py = entity_data.vector_y_new[j]

        groups_size = self.groups.size()
        for group_id in group_ids:
            if group_id < 0 or group_id >= <int> groups_size:
                continue
            collision_group = &self.groups[group_id]
            checked.clear()

            for grid_level in range(collision_group.max_level + 1):
                cell_size = self.cell_sizes[grid_level]
                min_cell_x = <int> floor(min_px / cell_size)
                min_cell_y = <int> floor(min_py / cell_size)
                max_cell_x = <int> floor(max_px / cell_size)
                max_cell_y = <int> floor(max_py / cell_size)

                for grid_cell_y in range(min_cell_y, max_cell_y + 1):
                    for grid_cell_x in range(min_cell_x, max_cell_x + 1):
                        key = (<uint64_t> grid_cell_x << 32) | (
                                <uint64_t> grid_cell_y & 0xFFFFFFFF)
                        if self.grids[grid_level][group_id].count(key) == 0:
                            continue

                        cell_b = &self.grids[grid_level][group_id][key]
                        cell_b_size = cell_b[0].size()
                        for j in range(cell_b_size):
                            b_entity_id = cell_b[0][j]
                            if checked.count(b_entity_id):
                                continue
                            checked.insert(b_entity_id)

                            entity_data_b = &collision_group.entities[b_entity_id]
                            if not entity_data_b.alive:
                                continue
                            if not entity_data_b.is_active:
                                continue

                            ignore = False
                            ignore_a_size = entity_data.ignore_collisions.size()
                            ignore_b_size = entity_data_b.ignore_collisions.size()

                            if ignore_a_size > 0 and ignore_b_size > 0:
                                for ignore_a_index in range(ignore_a_size):
                                    for ignore_b_index in range(ignore_b_size):
                                        if entity_data.ignore_collisions[
                                            ignore_a_index] == \
                                                entity_data_b.ignore_collisions[
                                                    ignore_b_index]:
                                            ignore = True
                                            break
                                    if ignore: break
                            if ignore: continue

                            hit = False
                            # aabb vs. aabb
                            if (
                                    entity_data.hitbox_type == 0
                                    and entity_data_b.hitbox_type == 0
                            ):
                                hit = aabb_aabb_swept(
                                    entity_data.vector_x_old[0],
                                    entity_data.vector_y_old[0],
                                    entity_data.vector_x_new[0],
                                    entity_data.vector_y_new[0],
                                    entity_data.size_x,
                                    entity_data.size_y,
                                    entity_data_b.vector_x_old[0],
                                    entity_data_b.vector_y_old[0],
                                    entity_data_b.vector_x_new[0],
                                    entity_data_b.vector_y_new[0],
                                    entity_data_b.size_x,
                                    entity_data_b.size_y,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t
                                )
                            # aabb vs. point/circle
                            elif entity_data.hitbox_type == 0 and (
                                    entity_data_b.hitbox_type == 4
                                    or entity_data_b.hitbox_type == 5
                            ):
                                hit = aabb_circle_swept(
                                    entity_data.vector_x_old[0],
                                    entity_data.vector_y_old[0],
                                    entity_data.vector_x_new[0],
                                    entity_data.vector_y_new[0],
                                    entity_data.size_x,
                                    entity_data.size_y,
                                    entity_data_b.vector_x_old[0],
                                    entity_data_b.vector_y_old[0],
                                    entity_data_b.vector_x_new[0],
                                    entity_data_b.vector_y_new[0],
                                    entity_data_b.radius,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t
                                )
                            # point/circle vs. aabb
                            elif (
                                    (
                                            entity_data.hitbox_type == 4
                                            or entity_data.hitbox_type == 5
                                    )
                                    and entity_data_b.hitbox_type == 0
                            ):
                                hit = aabb_circle_swept(
                                    entity_data_b.vector_x_old[0],
                                    entity_data_b.vector_y_old[0],
                                    entity_data_b.vector_x_new[0],
                                    entity_data_b.vector_y_new[0],
                                    entity_data_b.size_x, entity_data_b.size_y,
                                    entity_data.vector_x_old[0],
                                    entity_data.vector_y_old[0],
                                    entity_data.vector_x_new[0],
                                    entity_data.vector_y_new[0],
                                    entity_data.radius,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t
                                )
                                norm_x = -norm_x
                                norm_y = -norm_y
                            # point/circle vs. point/circle
                            elif (
                                    entity_data.hitbox_type == 4
                                    or entity_data.hitbox_type == 5
                            ) and (
                                    entity_data_b.hitbox_type == 4
                                    or entity_data_b.hitbox_type == 5
                            ):
                                hit = circle_circle_swept(
                                    entity_data.vector_x_old[0],
                                    entity_data.vector_y_old[0],
                                    entity_data.vector_x_new[0],
                                    entity_data.vector_y_new[0],
                                    entity_data.radius,
                                    entity_data_b.vector_x_old[0],
                                    entity_data_b.vector_y_old[0],
                                    entity_data_b.vector_x_new[0],
                                    entity_data_b.vector_y_new[0],
                                    entity_data_b.radius,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t)
                            # point/circle vs. aabb/obb/triangle/polygon
                            elif (entity_data.hitbox_type >= 4
                                  and entity_data_b.hitbox_type < 4
                            ):
                                a_delta_x = (entity_data.position_x_new
                                             - entity_data.position_x_old)
                                a_delta_y = (entity_data.position_y_new
                                             - entity_data.position_y_old)
                                b_delta_x = (entity_data_b.position_x_new
                                             - entity_data_b.position_x_old)
                                b_delta_y = (entity_data_b.position_y_new
                                             - entity_data_b.position_y_old)
                                hit = circle_poly_swept(
                                    entity_data.vector_x_old[0],
                                    entity_data.vector_y_old[0],
                                    entity_data.vector_x_new[0],
                                    entity_data.vector_y_new[0],
                                    entity_data.radius,
                                    entity_data_b.vector_x_old.data(),
                                    entity_data_b.vector_y_old.data(),
                                    entity_data_b.vector_x_new.data(),
                                    entity_data_b.vector_y_new.data(),
                                    entity_data_b.vector_x_old.size(),
                                    entity_data_b.axes_x.data(),
                                    entity_data_b.axes_y.data(),
                                    entity_data_b.axes_x.size(),
                                    b_delta_x,
                                    b_delta_y,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t
                                )
                            # aabb/obb/triangle/polygon vs. point/circle
                            elif (entity_data.hitbox_type < 4
                                  and entity_data_b.hitbox_type >= 4):
                                a_delta_x = (entity_data.position_x_new
                                             - entity_data.position_x_old)
                                a_delta_y = (entity_data.position_y_new
                                             - entity_data.position_y_old)
                                b_delta_x = (entity_data_b.position_x_new
                                             - entity_data_b.position_x_old)
                                b_delta_y = (entity_data_b.position_y_new
                                             - entity_data_b.position_y_old)
                                hit = circle_poly_swept(
                                    entity_data_b.vector_x_old[0],
                                    entity_data_b.vector_y_old[0],
                                    entity_data_b.vector_x_new[0],
                                    entity_data_b.vector_y_new[0],
                                    entity_data_b.radius,
                                    entity_data.vector_x_old.data(),
                                    entity_data.vector_y_old.data(),
                                    entity_data.vector_x_new.data(),
                                    entity_data.vector_y_new.data(),
                                    entity_data.vector_x_old.size(),
                                    entity_data.axes_x.data(),
                                    entity_data.axes_y.data(),
                                    entity_data.axes_x.size(),
                                    a_delta_x,
                                    a_delta_y,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t
                                )
                                norm_x = -norm_x
                                norm_y = -norm_y
                            else:
                                a_delta_x = (entity_data.position_x_new
                                             - entity_data.position_x_old)
                                a_delta_y = (entity_data.position_y_new
                                             - entity_data.position_y_old)
                                b_delta_x = (entity_data_b.position_x_new
                                             - entity_data_b.position_x_old)
                                b_delta_y = (entity_data_b.position_y_new
                                             - entity_data_b.position_y_old)
                                hit = poly_poly_swept(
                                    entity_data.vector_x_old.data(),
                                    entity_data.vector_y_old.data(),
                                    entity_data.vector_x_old.size(),
                                    entity_data.axes_x.data(),
                                    entity_data.axes_y.data(),
                                    entity_data.axes_x.size(),
                                    a_delta_x,
                                    a_delta_y,
                                    entity_data_b.vector_x_old.data(),
                                    entity_data_b.vector_y_old.data(),
                                    entity_data_b.vector_x_old.size(),
                                    entity_data_b.axes_x.data(),
                                    entity_data_b.axes_y.data(),
                                    entity_data_b.axes_x.size(),
                                    b_delta_x,
                                    b_delta_y,
                                    False,
                                    &norm_x,
                                    &norm_y,
                                    &t
                                )

                            if hit:
                                inst_b = self.group_instances[group_id][b_entity_id]
                                imp_ax = (
                                        entity_data.position_x_old
                                        + (
                                                (
                                                        entity_data.position_x_new
                                                        - entity_data.position_x_old
                                                ) * t
                                        )
                                )
                                imp_ay = (
                                        entity_data.position_y_old
                                        + (
                                                (
                                                        entity_data.position_y_new
                                                        - entity_data.position_y_old
                                                ) * t
                                        )
                                )
                                event_time = t if t > 0.0 else 0.0
                                events.append(
                                    CollisionEvent(-1, -1, group_id, inst_b,
                                                   Vec2().from_cartesian(imp_ax,
                                                                         imp_ay),
                                                   Vec2().from_cartesian(norm_x,
                                                                         norm_y),
                                                   event_time))

        events.sort(key=lambda e: e.time)
        return events

    def get_points(
            self,
            int group_id,  # type: CollisionGroupIDType
            int entity_id  # type: CollisionEntityIDType
    ) -> list:  # list[Vec2]
        """
        Debug-method to get the points of a hitbox.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: List of points of the hitbox
            For circles only 8 points are returned.
            I recommend using get_position and get_radius for them instead!
        """
        # if groups does not exist
        if group_id < 0 or group_id >= self.groups.size():
            return []
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef size_t total_entities
        cdef EntityData * entity_data
        cdef list points  # list[Vec2]
        cdef size_t i, vector_x_new_size

        total_entities = group.entities.size()
        # if entity does not exist
        if entity_id < 0 or entity_id >= <int> total_entities:
            return []

        entity_data = &group.entities[entity_id]
        if not entity_data.alive:
            return []

        points = []

        if entity_data.hitbox_type == 5:
            for i in range(8):
                points.append(Vec2().from_cartesian(
                    entity_data.vector_x_new[0]
                    + entity_data.radius * cos(i * 3.14159 / 4.0),
                    entity_data.vector_y_new[0]
                    + entity_data.radius * sin(i * 3.14159 / 4.0)
                ))
            return points

        vector_x_new_size = entity_data.vector_x_new.size()
        for i in range(vector_x_new_size):
            points.append(Vec2().from_cartesian(
                entity_data.vector_x_new[i],
                entity_data.vector_y_new[i])
            )

        return points

    def get_hitbox(
            self,
            int group_id  # type: CollisionGroupIDType
    ) -> object:  # CollisionHitboxType
        """
        Debug-Method to get the hitbox type of any group.
        :param group_id: The group ID.
        :return: The hitbox type of the group
        """
        if group_id < 0 or group_id >= self.groups.size():
            return None

        cdef int h_type = self.groups.data()[group_id].hitbox_type

        if h_type == 1:
            return "obb"
        elif h_type == 2:
            return "triangle"
        elif h_type == 3:
            return "polygon"
        elif h_type == 4:
            return "point"
        elif h_type == 5:
            return "circle"

        return "aabb"

    def get_position(
            self,
            int group_id,  # type: CollisionGroupIDType
            int entity_id  # type: CollisionEntityIDType
    ) -> object:  # Vec2 | None
        """
        Debug-method to get the position of an entity.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: The position of the entity if it exists. Otherwise, None.
        """
        if group_id < 0 or group_id >= self.groups.size():
            return None

        cdef int e_size = self.groups.data()[group_id].entities.size()
        if entity_id < 0 or entity_id >= e_size:
            return None

        cdef EntityData * ed = &self.groups.data()[group_id].entities.data()[entity_id]
        if not ed.alive:
            return None

        cdef double position_x = ed.position_x_new
        cdef double position_y = ed.position_y_new

        # Force top-left translation if it was registered as centered
        if ed.is_centered:
            position_x -= (ed.size_x / 2.0)
            position_y -= (ed.size_y / 2.0)

        return Vec2().from_cartesian(position_x, position_y)

    def get_size(
            self,
            int group_id,  # type: CollisionGroupIDType
            int entity_id  # type: CollisionEntityIDType
    ) -> object:  # Vec2 | None
        """
        Debug-method to get the size of an entity.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: The size of the entity if it exists. Otherwise, None.
        """
        if group_id < 0 or group_id >= self.groups.size():
            return None

        cdef int e_size = self.groups.data()[group_id].entities.size()
        if entity_id < 0 or entity_id >= e_size:
            return None

        cdef EntityData * ed = &self.groups.data()[group_id].entities.data()[entity_id]
        if not ed.alive:
            return None

        return Vec2().from_cartesian(ed.size_x, ed.size_y)

    def get_radius(
            self,
            int group_id,  # type: CollisionGroupIDType
            int entity_id  # type: CollisionEntityIDType
    ) -> double:  # float
        """
        Debug-method to get the radius of an entity.
        :param group_id: The group ID of the entity
        :param entity_id: The unique ID of the entity
        :return: The radius of the entity if it exists. Otherwise, 0.
        """
        cdef vector[CollisionGroupStruct] * _g = &self.groups
        if group_id < 0 or group_id >= _g[0].size():
            return 0.0

        cdef CollisionGroupStruct * group = &(_g[0][group_id])
        if entity_id < 0 or entity_id >= group.entities.size():
            return 0.0

        cdef EntityData * ed = &group.entities.data()[entity_id]
        if not ed.alive:
            return 0.0

        # Radius is exactly half the width (size.x / 2)
        return ed.size_x / 2.0
