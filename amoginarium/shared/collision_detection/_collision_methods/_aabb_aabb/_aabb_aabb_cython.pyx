# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False

from libcpp.unordered_set cimport unordered_set
from libc.stdint cimport uint64_t

from amoginarium.shared.collision_detection._collision_event import CollisionEvent
from amoginarium.shared.debugging import cum_timer
from amoginarium.shared.utility import Vec2

cdef inline double c_max(double a, double b) noexcept: return a if a > b else b
cdef inline double c_min(double a, double b) noexcept: return a if a < b else b
cdef inline double c_min4(double a, double b, double c, double d) noexcept:
    cdef double m1 = a if a < b else b
    cdef double m2 = c if c < d else d
    return m1 if m1 < m2 else m2


class AABBAABBCython:

    @staticmethod
    @cum_timer.time_this
    def collision(
            group_a, group_b, list entities_a, list entities_b, dict grid_b,
            double[:] a_px_o, double[:] a_py_o, double[:] a_px_n, double[:] a_py_n, double[:] a_sx, double[:] a_sy,
            double[:] b_px_o, double[:] b_py_o, double[:] b_px_n, double[:] b_py_n, double[:] b_sx, double[:] b_sy,
            callback_a, callback_b
    ) -> None:

        cdef Py_ssize_t num_a = len(entities_a)
        if num_a == 0: return

        cdef bint is_same_group = (group_a is group_b)
        cdef Py_ssize_t i, j, id_b

        # High-Speed C++ Hash Set for pair deduplication (Replaces Python Set/Frozenset)
        cdef unordered_set[uint64_t] checked_pairs
        cdef uint64_t pair_key, min_id, max_id

        cdef double pos_old_a_x, pos_old_a_y, pos_new_a_x, pos_new_a_y, size_a_x, size_a_y
        cdef double pos_old_b_x, pos_old_b_y, pos_new_b_x, pos_new_b_y, size_b_x, size_b_y
        cdef double v_a_x, v_a_y, v_b_x, v_b_y, v_rel_x, v_rel_y
        cdef double min_x, max_x, min_y, max_y, ray_o_x, ray_o_y
        cdef double t_near_x, t_far_x, t_near_y, t_far_y, t_hit_near, t_hit_far
        cdef bint is_overlapping
        cdef double norm_a_x, norm_a_y, t, push
        cdef double overlap_left, overlap_right, overlap_top, overlap_bottom, min_overlap

        cdef double inf = 1e300
        cdef dict tracker_a
        cdef list cell_list_b

        for i in range(num_a):
            entity_a = entities_a[i]
            tracker_a = entity_a.cell_tracker

            # Fetch coordinates instantly via raw C pointer dereference
            pos_old_a_x = a_px_o[i]
            pos_old_a_y = a_py_o[i]
            pos_new_a_x = a_px_n[i]
            pos_new_a_y = a_py_n[i]
            size_a_x = a_sx[i]
            size_a_y = a_sy[i]

            v_a_x = pos_new_a_x - pos_old_a_x
            v_a_y = pos_new_a_y - pos_old_a_y
            ray_o_x = pos_old_a_x
            ray_o_y = pos_old_a_y

            for cell_key in tracker_a:
                if cell_key not in grid_b: continue

                cell_list_b = grid_b[cell_key]
                for j in range(len(cell_list_b)):
                    id_b = cell_list_b[j]

                    if is_same_group and i == id_b: continue

                    # Pack pair IDs into a 64-bit integer for instantaneous C++ Set hashing
                    min_id = i if i < id_b else id_b
                    max_id = id_b if i < id_b else i
                    pair_key = (min_id << 32) | max_id

                    if checked_pairs.count(pair_key): continue
                    checked_pairs.insert(pair_key)

                    entity_b = entities_b[id_b]
                    if entity_a.instance is entity_b.instance: continue

                    pos_old_b_x = b_px_o[id_b]
                    pos_old_b_y = b_py_o[id_b]
                    pos_new_b_x = b_px_n[id_b]
                    pos_new_b_y = b_py_n[id_b]
                    size_b_x = b_sx[id_b]
                    size_b_y = b_sy[id_b]

                    v_b_x = pos_new_b_x - pos_old_b_x
                    v_b_y = pos_new_b_y - pos_old_b_y
                    v_rel_x = v_a_x - v_b_x
                    v_rel_y = v_a_y - v_b_y

                    min_x = pos_old_b_x - size_a_x
                    max_x = pos_old_b_x + size_b_x
                    min_y = pos_old_b_y - size_a_y
                    max_y = pos_old_b_y + size_b_y

                    t_near_x = -inf
                    t_far_x = inf
                    if v_rel_x != 0.0:
                        t_near_x = (min_x - ray_o_x) / v_rel_x
                        t_far_x = (max_x - ray_o_x) / v_rel_x
                        if t_near_x > t_far_x: t_near_x, t_far_x = t_far_x, t_near_x
                    elif not (min_x <= ray_o_x <= max_x):
                        continue

                    t_near_y = -inf
                    t_far_y = inf
                    if v_rel_y != 0.0:
                        t_near_y = (min_y - ray_o_y) / v_rel_y
                        t_far_y = (max_y - ray_o_y) / v_rel_y
                        if t_near_y > t_far_y: t_near_y, t_far_y = t_far_y, t_near_y
                    elif not (min_y <= ray_o_y <= max_y):
                        continue

                    t_hit_near = c_max(t_near_x, t_near_y)
                    t_hit_far = c_min(t_far_x, t_far_y)

                    is_overlapping = (
                            pos_new_a_x < pos_new_b_x + size_b_x and pos_new_a_x + size_a_x > pos_new_b_x and
                            pos_new_a_y < pos_new_b_y + size_b_y and pos_new_a_y + size_a_y > pos_new_b_y
                    )

                    if not is_overlapping and (t_hit_near > t_hit_far or t_hit_far < 0.0 or t_hit_near >= 1.0):
                        continue

                    norm_a_x, norm_a_y = 0.0, 0.0
                    t = c_max(0.0, t_hit_near)

                    if t_hit_near < 0.0:
                        overlap_left = pos_old_a_x - min_x
                        overlap_right = max_x - pos_old_a_x
                        overlap_top = pos_old_a_y - min_y
                        overlap_bottom = max_y - pos_old_a_y

                        min_overlap = c_min4(overlap_left, overlap_right, overlap_top, overlap_bottom)
                        push = (min_overlap / 2.0) + 0.01

                        if min_overlap == overlap_left:
                            norm_a_x = -1.0; pos_old_a_x -= push; pos_old_b_x += push
                        elif min_overlap == overlap_right:
                            norm_a_x = 1.0; pos_old_a_x += push; pos_old_b_x -= push
                        elif min_overlap == overlap_top:
                            norm_a_y = -1.0; pos_old_a_y -= push; pos_old_b_y += push
                        else:
                            norm_a_y = 1.0; pos_old_a_y += push; pos_old_b_y -= push
                    else:
                        if t_near_x > t_near_y:
                            norm_a_x = -1.0 if v_rel_x > 0.0 else 1.0
                        elif t_near_y > t_near_x:
                            norm_a_y = -1.0 if v_rel_y > 0.0 else 1.0
                        else:
                            norm_a_x = -1.0 if v_rel_x > 0.0 else 1.0
                            norm_a_y = -1.0 if v_rel_y > 0.0 else 1.0

                    if callback_a is not None or callback_b is not None:
                        impact_pos_a = Vec2().from_cartesian(pos_old_a_x + v_a_x * t, pos_old_a_y + v_a_y * t)
                        impact_pos_b = Vec2().from_cartesian(pos_old_b_x + v_b_x * t, pos_old_b_y + v_b_y * t)

                        if callback_a is not None: callback_a(entity_a.instance, CollisionEvent(group=group_b,
                                                                                                other_entity=entity_b.instance,
                                                                                                position=impact_pos_a,
                                                                                                normal=Vec2().from_cartesian(
                                                                                                    norm_a_x,
                                                                                                    norm_a_y)))
                        if callback_b is not None: callback_b(entity_b.instance, CollisionEvent(group=group_a,
                                                                                                other_entity=entity_a.instance,
                                                                                                position=impact_pos_b,
                                                                                                normal=Vec2().from_cartesian(
                                                                                                    -norm_a_x,
                                                                                                    -norm_a_y)))