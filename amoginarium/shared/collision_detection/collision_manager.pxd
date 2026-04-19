# cython: language_level=3
from libcpp.vector cimport vector
from libcpp.unordered_map cimport unordered_map
from libc.stdint cimport uint64_t

cdef struct EntityData:
    int id
    bint active
    bint is_centered
    int h_type

    double px_o, py_o, px_n, py_n
    double sx, sy
    double rot

    vector[double] vx_o
    vector[double] vy_o
    vector[double] vx_n
    vector[double] vy_n
    vector[double] axes_x
    vector[double] axes_y

    vector[int] bound_min_x
    vector[int] bound_min_y
    vector[int] bound_max_x
    vector[int] bound_max_y

    vector[vector[uint64_t]] grid_keys

    vector[int] col_groups
    vector[int] col_entities
    vector[double] col_nx
    vector[double] col_ny

    vector[int] prev_col_groups
    vector[int] prev_col_entities
    vector[double] prev_col_nx
    vector[double] prev_col_ny

cdef struct CollisionGroupStruct:
    int id
    int max_level
    bint is_static
    int h_type
    vector[EntityData] entities
    vector[int] free_ids

cdef struct CollisionRelationStruct:
    int group_a_id
    int group_b_id

cdef struct DeferredDeletion:
    int group_id
    int entity_id

cdef class CollisionManager:
    cdef double base_cell_size
    cdef vector[double] cell_sizes

    cdef vector[CollisionGroupStruct] groups
    cdef list group_instances
    cdef vector[CollisionRelationStruct] relations
    cdef list relation_callbacks

    cdef vector[unordered_map[int, unordered_map[uint64_t, vector[int]]]] grids
    cdef vector[DeferredDeletion] pending_deletions

    cdef void _update_entity_grid(self, int group_id, int entity_id)
    cdef void _remove_from_cell(self, int lvl, int group_id, uint64_t key, int entity_id)
    cdef void _calc_relation(self, CollisionRelationStruct rel, tuple callbacks)
    cdef void _dispatch_set_normals(self)
    cdef void _flush_deletions(self)