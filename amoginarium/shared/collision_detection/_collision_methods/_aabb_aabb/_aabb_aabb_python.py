"""
amoginarium/shared/collision_detection/_collision_methods/_aabb_aabb/_simple_python.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

import math
import typing as tp

from .._method_types import AABBAABBCollision

from ..._collision_group import CollisionGroupAABBEntityData, CollisionGroupAABB
from ..._collision_event import CollisionCallback, CollisionEvent

from amoginarium.shared.debugging import cum_timer

class AABBAABBPython(AABBAABBCollision):
    @staticmethod
    @cum_timer.time_this
    def collision[T1, T2](
            group_a: CollisionGroupAABB[T1],
            group_b: CollisionGroupAABB[T2],
            entities_a: list[CollisionGroupAABBEntityData[T1]],
            entities_b: list[CollisionGroupAABBEntityData[T2]],
            grid_b: dict[int, list[int]],
            callback_a: CollisionCallback[T1, T2] | None,
            callback_b: CollisionCallback[T2, T1] | None
    ) -> None:

        checked_pairs = set()
        is_same_group = (group_a is group_b)

        for id_a, entity_a in enumerate(entities_a):
            tracker_a = entity_a.cell_tracker

            # Only check the cells this entity is physically touching
            for cell_key in tracker_a:
                if cell_key not in grid_b:
                    continue

                cell_list_b = grid_b[cell_key]

                for id_b in cell_list_b:
                    # Prevent checking A against itself natively via IDs
                    if is_same_group and id_a == id_b:
                        continue

                    # Prevent checking the exact same pair twice if they share multiple cells
                    pair = frozenset((id_a, id_b))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    entity_b = entities_b[id_b]

                    # Secondary instance safeguard
                    if entity_a.instance is entity_b.instance:
                        continue

                    pos_old_a = entity_a.position_old
                    pos_new_a = entity_a.position_new
                    pos_old_b = entity_b.position_old
                    pos_new_b = entity_b.position_new

                    size_a = entity_a.size_new
                    size_b = entity_b.size_new

                    # 1. Real velocities for this frame
                    v_a_x = pos_new_a.x - pos_old_a.x
                    v_a_y = pos_new_a.y - pos_old_a.y
                    v_b_x = pos_new_b.x - pos_old_b.x
                    v_b_y = pos_new_b.y - pos_old_b.y

                    # 2. Relative velocity (Treat B as static)
                    v_rel_x = v_a_x - v_b_x
                    v_rel_y = v_a_y - v_b_y

                    # 3. Minkowski Difference
                    min_x = pos_old_b.x - size_a.x
                    max_x = pos_old_b.x + size_b.x
                    min_y = pos_old_b.y - size_a.y
                    max_y = pos_old_b.y + size_b.y

                    ray_o_x = pos_old_a.x
                    ray_o_y = pos_old_a.y

                    # 4. Swept AABB
                    t_near_x, t_far_x = float('-inf'), float('inf')
                    if v_rel_x != 0:
                        t_near_x = (min_x - ray_o_x) / v_rel_x
                        t_far_x = (max_x - ray_o_x) / v_rel_x
                        if t_near_x > t_far_x:
                            t_near_x, t_far_x = t_far_x, t_near_x
                    elif not (min_x <= ray_o_x <= max_x):
                        continue

                    t_near_y, t_far_y = float('-inf'), float('inf')
                    if v_rel_y != 0:
                        t_near_y = (min_y - ray_o_y) / v_rel_y
                        t_far_y = (max_y - ray_o_y) / v_rel_y
                        if t_near_y > t_far_y:
                            t_near_y, t_far_y = t_far_y, t_near_y
                    elif not (min_y <= ray_o_y <= max_y):
                        continue

                    t_hit_near = max(t_near_x, t_near_y)
                    t_hit_far = min(t_far_x, t_far_y)

                    # Standard discrete overlap check (Fall-back)
                    is_overlapping = (
                            pos_new_a.x < pos_new_b.x + size_b.x and
                            pos_new_a.x + size_a.x > pos_new_b.x and
                            pos_new_a.y < pos_new_b.y + size_b.y and
                            pos_new_a.y + size_a.y > pos_new_b.y
                    )

                    if not is_overlapping and (t_hit_near > t_hit_far or t_hit_far < 0 or t_hit_near >= 1.0):
                        continue

                    # 5. Position & Normal Calculation
                    norm_a_x, norm_a_y = 0.0, 0.0
                    t = max(0.0, t_hit_near)

                    VecType = type(pos_old_a)
                    impact_pos_a = VecType().from_cartesian(pos_old_a.x + v_a_x * t, pos_old_a.y + v_a_y * t)
                    impact_pos_b = VecType().from_cartesian(pos_old_b.x + v_b_x * t, pos_old_b.y + v_b_y * t)

                    if t_hit_near < 0:
                        # OVERLAP RESOLUTION
                        overlap_left = pos_old_a.x - min_x
                        overlap_right = max_x - pos_old_a.x
                        overlap_top = pos_old_a.y - min_y
                        overlap_bottom = max_y - pos_old_a.y

                        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                        push = min_overlap / 2.0 + 0.01

                        if min_overlap == overlap_left:
                            norm_a_x = -1.0
                            impact_pos_a.x -= push
                            impact_pos_b.x += push
                        elif min_overlap == overlap_right:
                            norm_a_x = 1.0
                            impact_pos_a.x += push
                            impact_pos_b.x -= push
                        elif min_overlap == overlap_top:
                            norm_a_y = -1.0
                            impact_pos_a.y -= push
                            impact_pos_b.y += push
                        elif min_overlap == overlap_bottom:
                            norm_a_y = 1.0
                            impact_pos_a.y += push
                            impact_pos_b.y -= push
                    else:
                        # Swept hit resolution
                        if t_near_x > t_near_y:
                            norm_a_x = -1.0 if v_rel_x > 0 else 1.0
                        elif t_near_y > t_near_x:
                            norm_a_y = -1.0 if v_rel_y > 0 else 1.0
                        else:
                            norm_a_x = -1.0 if v_rel_x > 0 else 1.0
                            norm_a_y = -1.0 if v_rel_y > 0 else 1.0

                    # 6. Dispatch events
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