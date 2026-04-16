"""
amoginarium/shared/collision_detection/_collision_methods/_aabb_aabb/_simple_python.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

import math
import typing as tp

from .._method_types import AABBAABBCollision
from ..._collision_event import CollisionEvent
from amoginarium.shared.debugging import cum_timer
from amoginarium.shared.utility import Vec2

class AABBAABBPython(AABBAABBCollision):
    @staticmethod
    @cum_timer.time_this
    def collision(
            group_a, group_b, entities_a, entities_b, grid_b,
            a_px_o, a_py_o, a_px_n, a_py_n, a_sx, a_sy,
            b_px_o, b_py_o, b_px_n, b_py_n, b_sx, b_sy,
            callback_a, callback_b
    ) -> None:

        checked_pairs = set()
        is_same_group = (group_a is group_b)

        for id_a, entity_a in enumerate(entities_a):
            for cell_key in entity_a.cell_tracker:
                if cell_key not in grid_b:
                    continue

                for id_b in grid_b[cell_key]:
                    if is_same_group and id_a == id_b:
                        continue

                    # Min/Max packing to ensure order independence in the set
                    pair_key = (min(id_a, id_b) << 32) | max(id_a, id_b)
                    if pair_key in checked_pairs:
                        continue
                    checked_pairs.add(pair_key)

                    entity_b = entities_b[id_b]
                    if entity_a.instance is entity_b.instance:
                        continue

                    v_a_x = a_px_n[id_a] - a_px_o[id_a]
                    v_a_y = a_py_n[id_a] - a_py_o[id_a]
                    v_b_x = b_px_n[id_b] - b_px_o[id_b]
                    v_b_y = b_py_n[id_b] - b_py_o[id_b]

                    v_rel_x = v_a_x - v_b_x
                    v_rel_y = v_a_y - v_b_y

                    min_x = b_px_o[id_b] - a_sx[id_a]
                    max_x = b_px_o[id_b] + b_sx[id_b]
                    min_y = b_py_o[id_b] - a_sy[id_a]
                    max_y = b_py_o[id_b] + b_sy[id_b]

                    ray_o_x, ray_o_y = a_px_o[id_a], a_py_o[id_a]

                    t_near_x, t_far_x = float('-inf'), float('inf')
                    if v_rel_x != 0:
                        t_near_x = (min_x - ray_o_x) / v_rel_x
                        t_far_x = (max_x - ray_o_x) / v_rel_x
                        if t_near_x > t_far_x: t_near_x, t_far_x = t_far_x, t_near_x
                    elif not (min_x <= ray_o_x <= max_x):
                        continue

                    t_near_y, t_far_y = float('-inf'), float('inf')
                    if v_rel_y != 0:
                        t_near_y = (min_y - ray_o_y) / v_rel_y
                        t_far_y = (max_y - ray_o_y) / v_rel_y
                        if t_near_y > t_far_y: t_near_y, t_far_y = t_far_y, t_near_y
                    elif not (min_y <= ray_o_y <= max_y):
                        continue

                    t_hit_near = max(t_near_x, t_near_y)
                    t_hit_far = min(t_far_x, t_far_y)

                    is_overlapping = (
                            a_px_n[id_a] < b_px_n[id_b] + b_sx[id_b] and
                            a_px_n[id_a] + a_sx[id_a] > b_px_n[id_b] and
                            a_py_n[id_a] < b_py_n[id_b] + b_sy[id_b] and
                            a_py_n[id_a] + a_sy[id_a] > b_py_n[id_b]
                    )

                    if not is_overlapping and (t_hit_near > t_hit_far or t_hit_far < 0 or t_hit_near >= 1.0):
                        continue

                    norm_a_x, norm_a_y = 0.0, 0.0
                    t = max(0.0, t_hit_near)

                    p_ox_a, p_oy_a = a_px_o[id_a], a_py_o[id_a]
                    p_ox_b, p_oy_b = b_px_o[id_b], b_py_o[id_b]

                    if t_hit_near < 0:
                        overlap_left = p_ox_a - min_x
                        overlap_right = max_x - p_ox_a
                        overlap_top = p_oy_a - min_y
                        overlap_bottom = max_y - p_ox_a

                        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                        push = min_overlap / 2.0 + 0.01

                        if min_overlap == overlap_left:
                            norm_a_x = -1.0; p_ox_a -= push; p_ox_b += push
                        elif min_overlap == overlap_right:
                            norm_a_x = 1.0; p_ox_a += push; p_ox_b -= push
                        elif min_overlap == overlap_top:
                            norm_a_y = -1.0; p_oy_a -= push; p_oy_b += push
                        elif min_overlap == overlap_bottom:
                            norm_a_y = 1.0; p_oy_a += push; p_oy_b -= push
                    else:
                        if t_near_x > t_near_y:
                            norm_a_x = -1.0 if v_rel_x > 0 else 1.0
                        elif t_near_y > t_near_x:
                            norm_a_y = -1.0 if v_rel_y > 0 else 1.0
                        else:
                            norm_a_x = -1.0 if v_rel_x > 0 else 1.0
                            norm_a_y = -1.0 if v_rel_y > 0 else 1.0

                    if callback_a is not None or callback_b is not None:
                        impact_pos_a = Vec2().from_cartesian(p_ox_a + v_a_x * t, p_oy_a + v_a_y * t)
                        impact_pos_b = Vec2().from_cartesian(p_ox_b + v_b_x * t, p_oy_b + v_b_y * t)

                        if callback_a is not None:
                            callback_a(entity_a.instance, CollisionEvent(group=group_b, other_entity=entity_b.instance,
                                                                         position=impact_pos_a,
                                                                         normal=Vec2().from_cartesian(norm_a_x,
                                                                                                      norm_a_y)))

                        if callback_b is not None:
                            callback_b(entity_b.instance, CollisionEvent(group=group_a, other_entity=entity_a.instance,
                                                                         position=impact_pos_b,
                                                                         normal=Vec2().from_cartesian(-norm_a_x,
                                                                                                      -norm_a_y)))