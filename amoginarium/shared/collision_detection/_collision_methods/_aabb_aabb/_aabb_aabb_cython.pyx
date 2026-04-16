# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import cython

from amoginarium.shared.collision_detection._collision_group import CollisionGroupAABBEntityData, CollisionGroupAABB
from amoginarium.shared.collision_detection._collision_event import CollisionCallback, CollisionEvent
from amoginarium.shared.debugging import cum_timer

# Inline C functions for maximum speed without Python overhead
cdef inline double c_max(double a, double b) noexcept:
    return a if a > b else b

cdef inline double c_min(double a, double b) noexcept:
    return a if a < b else b

cdef inline double c_min4(double a, double b, double c, double d) noexcept:
    cdef double m1 = a if a < b else b
    cdef double m2 = c if c < d else d
    return m1 if m1 < m2 else m2


class AABBAABBCython:
    @staticmethod
    @cum_timer.time_this
    def collision(
            group_a,
            group_b,
            list entities_a,
            list entities_b,
            dict grid_b,
            callback_a,
            callback_b
    ) -> None:

        cdef bint is_same_group = (group_a is group_b)
        cdef Py_ssize_t num_a = len(entities_a)
        cdef Py_ssize_t i, j, id_b

        # Statically type all math variables as raw C doubles
        cdef double pos_old_a_x, pos_old_a_y, pos_new_a_x, pos_new_a_y, size_a_x, size_a_y
        cdef double pos_old_b_x, pos_old_b_y, pos_new_b_x, pos_new_b_y, size_b_x, size_b_y
        cdef double v_a_x, v_a_y, v_b_x, v_b_y, v_rel_x, v_rel_y
        cdef double min_x, max_x, min_y, max_y, ray_o_x, ray_o_y
        cdef double t_near_x, t_far_x, t_near_y, t_far_y, t_hit_near, t_hit_far
        cdef bint is_overlapping
        cdef double norm_a_x, norm_a_y, t, push
        cdef double overlap_left, overlap_right, overlap_top, overlap_bottom, min_overlap

        cdef double inf = 1e300

        cdef set checked_pairs = set()
        cdef dict tracker_a
        cdef list cell_list_b
        cdef object cell_key
        cdef object pair

        for i in range(num_a):
            entity_a = entities_a[i]
            tracker_a = entity_a.cell_tracker

            # Extract variables to C-space once per outer loop
            pos_old_a_x = entity_a.position_old.x
            pos_old_a_y = entity_a.position_old.y
            pos_new_a_x = entity_a.position_new.x
            pos_new_a_y = entity_a.position_new.y
            size_a_x = entity_a.size_new.x
            size_a_y = entity_a.size_new.y

            v_a_x = pos_new_a_x - pos_old_a_x
            v_a_y = pos_new_a_y - pos_old_a_y
            ray_o_x = pos_old_a_x
            ray_o_y = pos_old_a_y

            # Only iterate through the grid cells this entity is actually touching
            for cell_key in tracker_a:
                if cell_key not in grid_b:
                    continue

                cell_list_b = grid_b[cell_key]

                for j in range(len(cell_list_b)):
                    id_b = cell_list_b[j]

                    # Prevent checking A against itself
                    if is_same_group and i == id_b:
                        continue

                    # Prevent checking the exact same pair twice if they share multiple cells
                    pair = frozenset((i, id_b))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    entity_b = entities_b[id_b]

                    # Secondary instance safeguard
                    if entity_a.instance is entity_b.instance:
                        continue

                    pos_old_b_x = entity_b.position_old.x
                    pos_old_b_y = entity_b.position_old.y
                    pos_new_b_x = entity_b.position_new.x
                    pos_new_b_y = entity_b.position_new.y
                    size_b_x = entity_b.size_new.x
                    size_b_y = entity_b.size_new.y

                    v_b_x = pos_new_b_x - pos_old_b_x
                    v_b_y = pos_new_b_y - pos_old_b_y

                    v_rel_x = v_a_x - v_b_x
                    v_rel_y = v_a_y - v_b_y

                    min_x = pos_old_b_x - size_a_x
                    max_x = pos_old_b_x + size_b_x
                    min_y = pos_old_b_y - size_a_y
                    max_y = pos_old_b_y + size_b_y

                    # Swept AABB Math
                    t_near_x = -inf
                    t_far_x = inf
                    if v_rel_x != 0.0:
                        t_near_x = (min_x - ray_o_x) / v_rel_x
                        t_far_x = (max_x - ray_o_x) / v_rel_x
                        if t_near_x > t_far_x:
                            t_near_x, t_far_x = t_far_x, t_near_x
                    elif not (min_x <= ray_o_x <= max_x):
                        continue

                    t_near_y = -inf
                    t_far_y = inf
                    if v_rel_y != 0.0:
                        t_near_y = (min_y - ray_o_y) / v_rel_y
                        t_far_y = (max_y - ray_o_y) / v_rel_y
                        if t_near_y > t_far_y:
                            t_near_y, t_far_y = t_far_y, t_near_y
                    elif not (min_y <= ray_o_y <= max_y):
                        continue

                    t_hit_near = c_max(t_near_x, t_near_y)
                    t_hit_far = c_min(t_far_x, t_far_y)

                    # Discrete overlap check
                    is_overlapping = (
                            pos_new_a_x < pos_new_b_x + size_b_x and
                            pos_new_a_x + size_a_x > pos_new_b_x and
                            pos_new_a_y < pos_new_b_y + size_b_y and
                            pos_new_a_y + size_a_y > pos_new_b_y
                    )

                    if not is_overlapping and (t_hit_near > t_hit_far or t_hit_far < 0.0 or t_hit_near >= 1.0):
                        continue

                    # Position & Normal Calculation
                    norm_a_x = 0.0
                    norm_a_y = 0.0
                    t = c_max(0.0, t_hit_near)

                    if t_hit_near < 0.0:
                        overlap_left = pos_old_a_x - min_x
                        overlap_right = max_x - pos_old_a_x
                        overlap_top = pos_old_a_y - min_y
                        overlap_bottom = max_y - pos_old_a_y

                        min_overlap = c_min4(overlap_left, overlap_right, overlap_top, overlap_bottom)
                        push = (min_overlap / 2.0) + 0.01

                        if min_overlap == overlap_left:
                            norm_a_x = -1.0
                            pos_old_a_x -= push
                            pos_old_b_x += push
                        elif min_overlap == overlap_right:
                            norm_a_x = 1.0
                            pos_old_a_x += push
                            pos_old_b_x -= push
                        elif min_overlap == overlap_top:
                            norm_a_y = -1.0
                            pos_old_a_y -= push
                            pos_old_b_y += push
                        else:  # overlap_bottom
                            norm_a_y = 1.0
                            pos_old_a_y += push
                            pos_old_b_y -= push
                    else:
                        if t_near_x > t_near_y:
                            norm_a_x = -1.0 if v_rel_x > 0.0 else 1.0
                        elif t_near_y > t_near_x:
                            norm_a_y = -1.0 if v_rel_y > 0.0 else 1.0
                        else:
                            norm_a_x = -1.0 if v_rel_x > 0.0 else 1.0
                            norm_a_y = -1.0 if v_rel_y > 0.0 else 1.0

                    # Re-enter Python space only for actual hits to create Events
                    if callback_a is not None or callback_b is not None:
                        VecType = type(entity_a.position_old)
                        impact_pos_a = VecType().from_cartesian(pos_old_a_x + v_a_x * t, pos_old_a_y + v_a_y * t)
                        impact_pos_b = VecType().from_cartesian(pos_old_b_x + v_b_x * t, pos_old_b_y + v_b_y * t)

                        if callback_a is not None:
                            callback_a(
                                entity_a.instance,
                                CollisionEvent(
                                    group=group_b,
                                    other_entity=entity_b.instance,
                                    position=impact_pos_a,
                                    normal=VecType().from_cartesian(norm_a_x, norm_a_y)
                                )
                            )

                        if callback_b is not None:
                            callback_b(
                                entity_b.instance,
                                CollisionEvent(
                                    group=group_a,
                                    other_entity=entity_a.instance,
                                    position=impact_pos_b,
                                    normal=VecType().from_cartesian(-norm_a_x, -norm_a_y)
                                )
                            )