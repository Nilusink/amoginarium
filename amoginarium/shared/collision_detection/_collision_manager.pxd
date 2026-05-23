# cython: language_level=3

"""
Header file for the Cython-generated CollisionManager class.

| Path: amoginarium/shared/collision_detection/_collision_manager.pxd
| Project: amoginarium
| Created: 13.05.2026
| Authors: LukasKrah
"""

from libc.stdint cimport uint64_t
from libcpp.unordered_map cimport unordered_map
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector

from ._collision_types import CollisionEntityIDType, CollisionGroupIDType
from ._collision_types import CollisionRelationIDType

"""
Data of a single entity in the collision system
"""
cdef struct EntityData:
    int id  # type: CollisionEntityIDType
    bint alive  # False if entity has been marked for pending deletion
    bint is_active
    bint is_centered
    int hitbox_type

    vector[int] ignore_collisions

    double position_x_old, position_y_old, position_x_new, position_y_new
    double size_x, size_y
    double rot
    double radius

    vector[double] vector_x_old
    vector[double] vector_y_old
    vector[double] vector_x_new
    vector[double] vector_y_new
    vector[double] axes_x
    vector[double] axes_y

    vector[int] bound_min_x
    vector[int] bound_min_y
    vector[int] bound_max_x
    vector[int] bound_max_y

    vector[vector[uint64_t]] grid_keys

"""
Data of a collision group
"""
cdef struct CollisionGroupStruct:
    int id  # type: CollisionGroupIDType
    int max_level
    bint is_static
    int hitbox_type
    vector[EntityData] entities
    vector[int] free_ids  # type: vector[CollisionEntityIDType]

"""
Data of a collision relation
(a relation between two groups)
"""
cdef struct CollisionRelationStruct:
    int id  # type: CollisionRelationIDType
    int group_a_id  # type: CollisionGroupIDType
    int group_b_id  # type: CollisionGroupIDType
    unordered_map[uint64_t, int] active_cols  # noqa
    unordered_set[uint64_t] updated_cols

"""
Data of a deferred deletion
(an entity that will be deleted in the next frame)
"""
cdef struct DeferredDeletion:
    int group_id  # type: CollisionGroupIDType
    int entity_id  # type: CollisionEntityIDType

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

    cdef double base_cell_size
    cdef vector[double] cell_sizes

    cdef vector[CollisionGroupStruct] groups

    # list[list[instance]] - first index: group_id, second index: entity_id
    # Contains instances for the callbacks
    cdef list group_instances

    cdef vector[CollisionRelationStruct] relations
    cdef list relation_callbacks

    cdef vector[unordered_map[int, unordered_map[uint64_t, vector[int]]]] grids
    cdef vector[DeferredDeletion] pending_deletions

    cdef int next_col_id

    cdef void _update_entity_grid(self, int group_id, int entity_id)
    cdef void _remove_from_cell(self, int lvl, int group_id,
                                uint64_t key, int entity_id)
    cdef void _remove_entity_from_grid(self, int group_id, int entity_id)
    cdef void _calc_relation(self, CollisionRelationStruct * rel, tuple callbacks)
    cdef void _flush_deletions(self)
    cdef void _cleanup_entity_collisions(self, int group_id, int entity_id)
