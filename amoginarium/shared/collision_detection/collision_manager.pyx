# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False
"""
Collision Manager.

Path: amoginarium/shared/collision_detection/collision_manager.pyx
Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from .collision_manager cimport CollisionGroupStruct, CollisionManager
from .collision_manager cimport CollisionRelationStruct, DeferredDeletion, EntityData
from .collision_methods cimport aabb_aabb_swept, aabb_circle_swept, circle_circle_swept
from .collision_methods cimport circle_poly_swept, poly_poly_swept

from amoginarium.shared.utility import Vec2

from .collision_event import CollisionEvent

from cython.operator cimport dereference as deref
from cython.operator cimport preincrement as inc
from libc.math cimport cos, floor, sin, sqrt
from libc.stdint cimport uint64_t
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector


cdef class CollisionManager:
    def __init__(self, double base_cell_size=1000.0, list level_dividers=None):
        cdef double current_size

        self.base_cell_size = base_cell_size
        self.cell_sizes.push_back(base_cell_size)

        current_size = base_cell_size
        if level_dividers:
            for div in level_dividers:
                current_size = current_size / div
                self.cell_sizes.push_back(current_size)

        self.grids.resize(self.cell_sizes.size())
        self.group_instances = []
        self.relation_callbacks = []
        self.next_col_id = 1

    def add_group(self, int max_level, bint is_static=False, str hitbox_type="aabb") -> int:
        cdef size_t cs_sz
        cdef int g_id
        cdef CollisionGroupStruct group
        cdef int lvl

        cs_sz = self.cell_sizes.size()
        if max_level >= <int> cs_sz:
            max_level = <int> cs_sz - 1

        g_id = <int> self.groups.size()
        group.id = g_id
        group.max_level = max_level
        group.is_static = is_static

        group.h_type = 0
        if hitbox_type == "obb":
            group.h_type = 1
        elif hitbox_type == "triangle":
            group.h_type = 2
        elif hitbox_type == "polygon":
            group.h_type = 3
        elif hitbox_type == "point":
            group.h_type = 4
        elif hitbox_type == "circle":
            group.h_type = 5

        self.groups.push_back(group)
        self.group_instances.append([])

        for lvl in range(max_level + 1):
            self.grids[lvl][g_id] = unordered_map[uint64_t, vector[int]]()

        return g_id

    def clear_all_entities(self):
        cdef size_t i
        cdef int lvl
        cdef CollisionGroupStruct * group
        cdef size_t rel_sz
        cdef size_t grp_sz

        self.pending_deletions.clear()

        rel_sz = self.relations.size()
        for i in range(rel_sz):
            self.relations[i].active_cols.clear()
            self.relations[i].updated_cols.clear()

        grp_sz = self.groups.size()
        for i in range(grp_sz):
            group = &self.groups[i]
            group.entities.clear()
            group.free_ids.clear()
            self.group_instances[i].clear()
            for lvl in range(group.max_level + 1):
                self.grids[lvl][i].clear()

    def register_entity(self, int group_id, object instance, object position=None, object size=None,
                        bint centered=False,
                        double rotation=0.0, list positions=None, object radius=None,
                        object ignore_collisions=None, bint is_active=True) -> int:
        if group_id < 0 or group_id >= self.groups.size(): return -1
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef int e_id, lvl
        cdef EntityData ed
        cdef double _rad = 0.0
        cdef size_t free_ids_sz

        if radius is not None:
            _rad = radius
        elif size is not None:
            _rad = size.x / 2.0

        free_ids_sz = group.free_ids.size()
        if free_ids_sz > 0:
            e_id = group.free_ids.back()
            group.free_ids.pop_back()
            group.entities[e_id].active = True
            group.entities[e_id].is_active = is_active
            group.entities[e_id].h_type = group.h_type
            group.entities[e_id].is_centered = centered
            group.entities[e_id].rot = rotation
            group.entities[e_id].radius = _rad

            group.entities[e_id].ignore_collisions.clear()
            if ignore_collisions is not None:
                if isinstance(ignore_collisions, list):
                    for ig in ignore_collisions:
                        group.entities[e_id].ignore_collisions.push_back(ig)
                else:
                    group.entities[e_id].ignore_collisions.push_back(ignore_collisions)

            if position is not None:
                group.entities[e_id].px_o = position.x
                group.entities[e_id].py_o = position.y
                group.entities[e_id].px_n = position.x
                group.entities[e_id].py_n = position.y
            else:
                group.entities[e_id].px_o = 0.0
                group.entities[e_id].py_o = 0.0
                group.entities[e_id].px_n = 0.0
                group.entities[e_id].py_n = 0.0

            if size is not None:
                group.entities[e_id].sx = size.x
                group.entities[e_id].sy = size.y
            else:
                group.entities[e_id].sx = 0.0
                group.entities[e_id].sy = 0.0

            group.entities[e_id].vx_o.clear()
            group.entities[e_id].vy_o.clear()
            group.entities[e_id].vx_n.clear()
            group.entities[e_id].vy_n.clear()
            group.entities[e_id].axes_x.clear()
            group.entities[e_id].axes_y.clear()

            for lvl in range(group.max_level + 1):
                group.entities[e_id].bound_min_x[lvl] = -2147483647
                group.entities[e_id].bound_min_y[lvl] = -2147483647
                group.entities[e_id].bound_max_x[lvl] = -2147483647
                group.entities[e_id].bound_max_y[lvl] = -2147483647
                group.entities[e_id].grid_keys[lvl].clear()

            self.group_instances[group_id][e_id] = instance
        else:
            e_id = <int> group.entities.size()
            ed.id = e_id
            ed.active = True
            ed.is_active = is_active
            ed.h_type = group.h_type
            ed.is_centered = centered
            ed.rot = rotation
            ed.radius = _rad

            ed.ignore_collisions.clear()
            if ignore_collisions is not None:
                if isinstance(ignore_collisions, list):
                    for ig in ignore_collisions:
                        ed.ignore_collisions.push_back(ig)
                else:
                    ed.ignore_collisions.push_back(ignore_collisions)

            if position is not None:
                ed.px_o = position.x
                ed.py_o = position.y
                ed.px_n = position.x
                ed.py_n = position.y
            else:
                ed.px_o = 0.0
                ed.py_o = 0.0
                ed.px_n = 0.0
                ed.py_n = 0.0

            if size is not None:
                ed.sx = size.x
                ed.sy = size.y
            else:
                ed.sx = 0.0
                ed.sy = 0.0

            ed.grid_keys.resize(group.max_level + 1)
            ed.bound_min_x.resize(group.max_level + 1, -2147483647)
            ed.bound_min_y.resize(group.max_level + 1, -2147483647)
            ed.bound_max_x.resize(group.max_level + 1, -2147483647)
            ed.bound_max_y.resize(group.max_level + 1, -2147483647)

            group.entities.push_back(ed)
            self.group_instances[group_id].append(instance)

        self.update_entity(group_id, e_id, position, size, centered, rotation, positions, True, radius,
                           ignore_collisions)
        return e_id

    def delete_entity(self, int group_id, int entity_id):
        if group_id < 0 or group_id >= self.groups.size(): return
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef EntityData * ed
        cdef DeferredDeletion dd
        cdef size_t ent_sz

        ent_sz = group.entities.size()
        if entity_id < 0 or entity_id >= <int> ent_sz: return

        ed = &group.entities[entity_id]
        if not ed.active: return

        ed.active = False
        dd.group_id = group_id
        dd.entity_id = entity_id
        self.pending_deletions.push_back(dd)

    cdef void _cleanup_entity_collisions(self, int group_id, int entity_id):
        cdef CollisionRelationStruct * rel
        cdef uint64_t pair_key
        cdef uint64_t a_id, b_id
        cdef tuple cbs
        cdef size_t rel_sz
        cdef size_t i, k, to_remove_sz
        cdef vector[uint64_t] to_remove
        cdef int g_a_id, g_b_id, r_id
        cdef object inst_a, inst_b

        rel_sz = self.relations.size()
        for i in range(rel_sz):
            rel = &self.relations[i]
            r_id = rel.id
            g_a_id = rel.group_a_id
            g_b_id = rel.group_b_id

            if g_a_id == group_id or g_b_id == group_id:
                cbs = self.relation_callbacks[i]
                to_remove.clear()

                it = rel.active_cols.begin()
                while it != rel.active_cols.end():
                    pair_key = deref(it).first
                    col_id = deref(it).second

                    a_id = pair_key >> 32
                    b_id = pair_key & 0xFFFFFFFF

                    # If either A or B is the entity being deactivated/deleted
                    if (g_a_id == group_id and a_id == entity_id) or (g_b_id == group_id and b_id == entity_id):
                        if self.groups[g_a_id].entities.size() > a_id and self.groups[g_b_id].entities.size() > b_id:
                            if len(self.group_instances[g_a_id]) > a_id and len(self.group_instances[g_b_id]) > b_id:
                                inst_a = self.group_instances[g_a_id][a_id]
                                inst_b = self.group_instances[g_b_id][b_id]

                                if inst_a is not None and inst_b is not None:

                                    # Trigger End for A (cbs[1])
                                    if cbs[1] is not None:
                                        ev_a = CollisionEvent(col_id, r_id, g_b_id, inst_b,
                                                              Vec2().from_cartesian(
                                                                  self.groups[g_a_id].entities[a_id].px_n,
                                                                  self.groups[g_a_id].entities[a_id].py_n),
                                                              Vec2(), 1.0)
                                        cbs[1](inst_a, [ev_a])

                                    # Trigger End for B (cbs[3])
                                    if cbs[3] is not None:
                                        ev_b = CollisionEvent(col_id, r_id, g_a_id, inst_a,
                                                              Vec2().from_cartesian(
                                                                  self.groups[g_b_id].entities[b_id].px_n,
                                                                  self.groups[g_b_id].entities[b_id].py_n),
                                                              Vec2(), 1.0)
                                        cbs[3](inst_b, [ev_b])

                        to_remove.push_back(pair_key)

                    inc(it)

                to_remove_sz = to_remove.size()
                for k in range(to_remove_sz):
                    rel.active_cols.erase(to_remove[k])

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

    def update_entity(self, int group_id, int entity_id, object position=None, object size=None, object centered=None,
                      object rotation=None, list positions=None, bint shift_history=True, object radius=None,
                      object ignore_collisions=None, object is_active=None):
        if group_id < 0 or group_id >= self.groups.size(): return
        if entity_id < 0 or entity_id >= self.groups[group_id].entities.size(): return

        cdef EntityData * ed = &self.groups[group_id].entities[entity_id]
        cdef double old_px_n, old_py_n
        cdef double cx, cy, hw, hh, cr, sr, ax, ay, dx, dy, ln
        cdef double pivot_x, pivot_y
        cdef size_t i, num_v
        cdef size_t ax_x_sz, vx_n_sz, vx_n_sz_2, vx_o_sz2, vx_n_sz2, vx_o_sz3, vx_n_sz3
        cdef bint old_is_active, transitioned_to_active, transitioned_to_inactive

        if not ed.active: return

        old_is_active = ed.is_active
        transitioned_to_active = False
        transitioned_to_inactive = False

        if is_active is not None:
            ed.is_active = is_active
            if old_is_active and not ed.is_active:
                transitioned_to_inactive = True
            elif not old_is_active and ed.is_active:
                transitioned_to_active = True

        if transitioned_to_inactive:
            self._cleanup_entity_collisions(group_id, entity_id)
            self._remove_entity_from_grid(group_id, entity_id)

        if shift_history:
            ed.px_o = ed.px_n
            ed.py_o = ed.py_n
            ed.vx_o = ed.vx_n
            ed.vy_o = ed.vy_n

        old_px_n = ed.px_n
        old_py_n = ed.py_n

        if centered is not None: ed.is_centered = centered
        if size is not None: ed.sx = size.x; ed.sy = size.y
        if rotation is not None: ed.rot = rotation
        if position is not None:
            ed.px_n = position.x
            ed.py_n = position.y

        if radius is not None:
            ed.radius = radius
        elif size is not None:
            ed.radius = size.x / 2.0

        if ignore_collisions is not None:
            ed.ignore_collisions.clear()
            if isinstance(ignore_collisions, list):
                for ig in ignore_collisions:
                    ed.ignore_collisions.push_back(ig)
            else:
                ed.ignore_collisions.push_back(ignore_collisions)

        if ed.h_type == 0:
            if ed.is_centered:
                cx = ed.px_n - (ed.sx / 2.0)
                cy = ed.py_n - (ed.sy / 2.0)
            else:
                cx = ed.px_n
                cy = ed.py_n
            ed.vx_n.clear()
            ed.vy_n.clear()
            ed.vx_n.push_back(cx)
            ed.vy_n.push_back(cy)
            ed.vx_n.push_back(cx + ed.sx)
            ed.vy_n.push_back(cy)
            ed.vx_n.push_back(cx + ed.sx)
            ed.vy_n.push_back(cy + ed.sy)
            ed.vx_n.push_back(cx)
            ed.vy_n.push_back(cy + ed.sy)

            ax_x_sz = ed.axes_x.size()
            if ax_x_sz == 0:
                ed.axes_x.push_back(1.0)
                ed.axes_y.push_back(0.0)
                ed.axes_x.push_back(0.0)
                ed.axes_y.push_back(1.0)

        elif ed.h_type == 1:
            cr = cos(ed.rot)
            sr = sin(ed.rot)
            ed.vx_n.clear()
            ed.vy_n.clear()

            if ed.is_centered:
                cx = ed.px_n
                cy = ed.py_n
                hw = ed.sx / 2.0
                hh = ed.sy / 2.0
                ed.vx_n.push_back(cx - hw * cr + hh * sr)
                ed.vy_n.push_back(cy - hw * sr - hh * cr)
                ed.vx_n.push_back(cx + hw * cr + hh * sr)
                ed.vy_n.push_back(cy + hw * sr - hh * cr)
                ed.vx_n.push_back(cx + hw * cr - hh * sr)
                ed.vy_n.push_back(cy + hw * sr + hh * cr)
                ed.vx_n.push_back(cx - hw * cr - hh * sr)
                ed.vy_n.push_back(cy - hw * sr + hh * cr)
            else:
                pivot_x = ed.px_n
                pivot_y = ed.py_n
                ed.vx_n.push_back(pivot_x)
                ed.vy_n.push_back(pivot_y)
                ed.vx_n.push_back(pivot_x + ed.sx * cr)
                ed.vy_n.push_back(pivot_y + ed.sx * sr)
                ed.vx_n.push_back(pivot_x + ed.sx * cr - ed.sy * sr)
                ed.vy_n.push_back(pivot_y + ed.sx * sr + ed.sy * cr)
                ed.vx_n.push_back(pivot_x - ed.sy * sr)
                ed.vy_n.push_back(pivot_y + ed.sy * cr)

            ed.axes_x.clear()
            ed.axes_y.clear()
            ed.axes_x.push_back(cr)
            ed.axes_y.push_back(sr)
            ed.axes_x.push_back(-sr)
            ed.axes_y.push_back(cr)

        elif ed.h_type == 2 or ed.h_type == 3:
            if positions is not None:
                ed.vx_n.clear()
                ed.vy_n.clear()
                ax = 0
                ay = 0
                for p in positions:
                    ed.vx_n.push_back(p.x)
                    ed.vy_n.push_back(p.y)
                    ax += p.x
                    ay += p.y
                ed.px_n = ax / len(positions)
                ed.py_n = ay / len(positions)

                dx = ed.px_n - old_px_n
                dy = ed.py_n - old_py_n
                ed.vx_o.clear()
                ed.vy_o.clear()
                vx_n_sz = ed.vx_n.size()
                for i in range(vx_n_sz):
                    ed.vx_o.push_back(ed.vx_n[i] - dx)
                    ed.vy_o.push_back(ed.vy_n[i] - dy)

                ed.axes_x.clear()
                ed.axes_y.clear()
                num_v = ed.vx_n.size()
                for i in range(num_v):
                    dx = ed.vx_n[(i + 1) % num_v] - ed.vx_n[i]
                    dy = ed.vy_n[(i + 1) % num_v] - ed.vy_n[i]
                    ln = sqrt(dx * dx + dy * dy)
                    if ln > 0.0001:
                        ed.axes_x.push_back(-dy / ln)
                        ed.axes_y.push_back(dx / ln)
            elif position is not None:
                dx = ed.px_n - old_px_n
                dy = ed.py_n - old_py_n
                vx_n_sz_2 = ed.vx_n.size()
                for i in range(vx_n_sz_2):
                    ed.vx_n[i] += dx
                    ed.vy_n[i] += dy

        elif ed.h_type == 4:
            ed.sx = 0.0
            ed.sy = 0.0
            ed.vx_n.clear()
            ed.vy_n.clear()
            ed.vx_n.push_back(ed.px_n)
            ed.vy_n.push_back(ed.py_n)

        elif ed.h_type == 5:
            if ed.is_centered:
                cx = ed.px_n;
                cy = ed.py_n
            else:
                cx = ed.px_n + ed.radius;
                cy = ed.py_n + ed.radius
            ed.vx_n.clear()
            ed.vy_n.clear()
            ed.vx_n.push_back(cx)
            ed.vy_n.push_back(cy)

        vx_o_sz2 = ed.vx_o.size()
        if vx_o_sz2 == 0 or transitioned_to_active or not ed.is_active:
            ed.vx_o = ed.vx_n
            ed.vy_o = ed.vy_n
            ed.px_o = ed.px_n
            ed.py_o = ed.py_n

        if not self.groups[group_id].is_static:
            if ed.is_active:
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

        if ed.h_type == 0 or ed.h_type == 4:
            min_px = ed.vx_o[0] if ed.vx_o[0] < ed.vx_n[0] else ed.vx_n[0]
            min_py = ed.vy_o[0] if ed.vy_o[0] < ed.vy_n[0] else ed.vy_n[0]
            max_px_o = ed.vx_o[0] + ed.sx
            max_px_n = ed.vx_n[0] + ed.sx
            max_px = max_px_o if max_px_o > max_px_n else max_px_n
            max_py_o = ed.vy_o[0] + ed.sy
            max_py_n = ed.vy_n[0] + ed.sy
            max_py = max_py_o if max_py_o > max_py_n else max_py_n
        elif ed.h_type == 5:
            min_px = (ed.vx_o[0] if ed.vx_o[0] < ed.vx_n[0] else ed.vx_n[0]) - ed.radius
            min_py = (ed.vy_o[0] if ed.vy_o[0] < ed.vy_n[0] else ed.vy_n[0]) - ed.radius
            max_px = (ed.vx_o[0] if ed.vx_o[0] > ed.vx_n[0] else ed.vx_n[0]) + ed.radius
            max_py = (ed.vy_o[0] if ed.vy_o[0] > ed.vy_n[0] else ed.vy_n[0]) + ed.radius
        else:
            min_px = ed.vx_o[0]
            max_px = ed.vx_o[0]
            min_py = ed.vy_o[0]
            max_py = ed.vy_o[0]
            vx_o_sz = ed.vx_o.size()
            for j in range(1, vx_o_sz):
                if ed.vx_o[j] < min_px:
                    min_px = ed.vx_o[j]
                elif ed.vx_o[j] > max_px:
                    max_px = ed.vx_o[j]
                if ed.vy_o[j] < min_py:
                    min_py = ed.vy_o[j]
                elif ed.vy_o[j] > max_py:
                    max_py = ed.vy_o[j]
            vx_n_sz = ed.vx_n.size()
            for j in range(vx_n_sz):
                if ed.vx_n[j] < min_px:
                    min_px = ed.vx_n[j]
                elif ed.vx_n[j] > max_px:
                    max_px = ed.vx_n[j]
                if ed.vy_n[j] < min_py:
                    min_py = ed.vy_n[j]
                elif ed.vy_n[j] > max_py:
                    max_py = ed.vy_n[j]

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

    def create_relation(self, int group_a_id, int group_b_id, object cb_a_on_start=None, object cb_a_on_end=None,
                        object cb_b_on_start=None, object cb_b_on_end=None) -> int:
        cdef int r_id
        cdef CollisionRelationStruct rel

        r_id = <int> self.relations.size()
        rel.id = r_id
        rel.group_a_id = group_a_id
        rel.group_b_id = group_b_id
        self.relations.push_back(rel)
        self.relation_callbacks.append((cb_a_on_start, cb_a_on_end, cb_b_on_start, cb_b_on_end))
        return r_id

    def calculate_all_collisions(self):
        cdef size_t i, rel_sz

        self._flush_deletions()
        rel_sz = self.relations.size()
        for i in range(rel_sz):
            self._calc_relation(&self.relations[i], self.relation_callbacks[i])

    def calculate_collisions(self, list relation_ids):
        cdef int r_id
        cdef size_t rel_sz

        self._flush_deletions()
        rel_sz = self.relations.size()
        for r_id in relation_ids:
            if 0 <= r_id < <int> rel_sz:
                self._calc_relation(&self.relations[r_id], self.relation_callbacks[r_id])

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
        cdef double norm_x, norm_y, t
        cdef double imp_ax, imp_ay, imp_bx, imp_by
        cdef vector[uint64_t] * a_keys
        cdef vector[int] * cell_b
        cdef size_t a_idx, k_idx, b_idx, j, k, a_keys_sz, cell_b_sz, ent_sz, to_remove_sz
        cdef int iterations
        cdef bint hit
        cdef double a_dx, a_dy, b_dx, b_dy
        cdef bint is_active_col
        cdef int col_id
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
            if not ea.active: continue
            if not ea.is_active: continue

            a_keys = &ea.grid_keys[check_lvl]
            a_keys_sz = a_keys[0].size()

            for k_idx in range(a_keys_sz):
                if not ea.active: break

                if self.grids[check_lvl][g_b_id].count(a_keys[0][k_idx]) == 0:
                    continue

                cell_b = &self.grids[check_lvl][g_b_id][a_keys[0][k_idx]]
                cell_b_sz = cell_b[0].size()

                for b_idx in range(cell_b_sz):
                    b_id = cell_b[0][b_idx]

                    if is_same and ea.id >= b_id:
                        continue

                    eb = &gb.entities[b_id]
                    if not eb.active: continue
                    if not eb.is_active: continue

                    ignore = False
                    ig_a_sz = ea.ignore_collisions.size()
                    ig_b_sz = eb.ignore_collisions.size()

                    if ig_a_sz > 0 and ig_b_sz > 0:
                        for ig_a_i in range(ig_a_sz):
                            for ig_b_i in range(ig_b_sz):
                                if ea.ignore_collisions[ig_a_i] == eb.ignore_collisions[ig_b_i]:
                                    ignore = True
                                    break
                            if ignore: break
                    if ignore: continue

                    pair_key = (<uint64_t> ea.id << 32) | <uint64_t> b_id
                    if checked_pairs.count(pair_key): continue
                    checked_pairs.insert(pair_key)

                    is_active_col = (rel.active_cols.count(pair_key) > 0)
                    hit = False

                    if ea.h_type == 0 and eb.h_type == 0:
                        hit = aabb_aabb_swept(
                            ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.sx, ea.sy,
                            eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                            is_active_col, &norm_x, &norm_y, &t)
                    elif ea.h_type == 0 and (eb.h_type == 4 or eb.h_type == 5):
                        hit = aabb_circle_swept(
                            ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.sx, ea.sy,
                            eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.radius,
                            is_active_col, &norm_x, &norm_y, &t)
                    elif (ea.h_type == 4 or ea.h_type == 5) and eb.h_type == 0:
                        hit = aabb_circle_swept(
                            eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                            ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.radius,
                            is_active_col, &norm_x, &norm_y, &t)
                        norm_x = -norm_x
                        norm_y = -norm_y
                    elif (ea.h_type == 4 or ea.h_type == 5) and (eb.h_type == 4 or eb.h_type == 5):
                        hit = circle_circle_swept(
                            ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.radius,
                            eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.radius,
                            is_active_col, &norm_x, &norm_y, &t)
                    elif ea.h_type >= 4 and eb.h_type < 4:
                        a_dx = ea.px_n - ea.px_o
                        a_dy = ea.py_n - ea.py_o
                        b_dx = eb.px_n - eb.px_o
                        b_dy = eb.py_n - eb.py_o
                        hit = circle_poly_swept(
                            ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.radius,
                            eb.vx_o.data(), eb.vy_o.data(), eb.vx_n.data(), eb.vy_n.data(), eb.vx_o.size(),
                            eb.axes_x.data(), eb.axes_y.data(), eb.axes_x.size(), b_dx, b_dy,
                            is_active_col, &norm_x, &norm_y, &t
                        )
                    elif ea.h_type < 4 and eb.h_type >= 4:
                        a_dx = ea.px_n - ea.px_o
                        a_dy = ea.py_n - ea.py_o
                        b_dx = eb.px_n - eb.px_o
                        b_dy = eb.py_n - eb.py_o
                        hit = circle_poly_swept(
                            eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.radius,
                            ea.vx_o.data(), ea.vy_o.data(), ea.vx_n.data(), ea.vy_n.data(), ea.vx_o.size(),
                            ea.axes_x.data(), ea.axes_y.data(), ea.axes_x.size(), a_dx, a_dy,
                            is_active_col, &norm_x, &norm_y, &t
                        )
                        norm_x = -norm_x
                        norm_y = -norm_y
                    else:
                        a_dx = ea.px_n - ea.px_o
                        a_dy = ea.py_n - ea.py_o
                        b_dx = eb.px_n - eb.px_o
                        b_dy = eb.py_n - eb.py_o
                        hit = poly_poly_swept(
                            ea.vx_o.data(), ea.vy_o.data(), ea.vx_o.size(),
                            ea.axes_x.data(), ea.axes_y.data(), ea.axes_x.size(), a_dx, a_dy,
                            eb.vx_o.data(), eb.vy_o.data(), eb.vx_o.size(),
                            eb.axes_x.data(), eb.axes_y.data(), eb.axes_x.size(), b_dx, b_dy,
                            is_active_col, &norm_x, &norm_y, &t
                        )

                    if hit:
                        rel.updated_cols.insert(pair_key)

                        if not is_active_col:
                            col_id = self.next_col_id
                            self.next_col_id += 1
                            rel.active_cols[pair_key] = col_id

                            imp_ax = ea.px_o + ((ea.px_n - ea.px_o) * t)
                            imp_ay = ea.py_o + ((ea.py_n - ea.py_o) * t)
                            imp_bx = eb.px_o + ((eb.px_n - eb.px_o) * t)
                            imp_by = eb.py_o + ((eb.py_n - eb.py_o) * t)

                            if callbacks[0] is not None:
                                inst_b = self.group_instances[g_b_id][b_id]
                                ev = CollisionEvent(col_id, r_id, g_b_id, inst_b, Vec2().from_cartesian(imp_ax, imp_ay),
                                                    Vec2().from_cartesian(norm_x, norm_y), t)
                                if ea.id not in events_a_start: events_a_start[ea.id] = []
                                events_a_start[ea.id].append((ev, pair_key))

                            if callbacks[2] is not None:
                                inst_a = self.group_instances[g_a_id][ea.id]
                                ev = CollisionEvent(col_id, r_id, g_a_id, inst_a, Vec2().from_cartesian(imp_bx, imp_by),
                                                    Vec2().from_cartesian(-norm_x, -norm_y), t)
                                if b_id not in events_b_start: events_b_start[b_id] = []
                                events_b_start[b_id].append((ev, pair_key))

        it = rel.active_cols.begin()
        while it != rel.active_cols.end():
            pair_key = deref(it).first
            col_id = deref(it).second
            if rel.updated_cols.find(pair_key) == rel.updated_cols.end():
                a_id = pair_key >> 32
                b_id = pair_key & 0xFFFFFFFF

                if callbacks[1] is not None:
                    inst_a = self.group_instances[g_a_id][a_id]
                    inst_b = self.group_instances[g_b_id][b_id]
                    if inst_a is not None and inst_b is not None:
                        ev = CollisionEvent(col_id, r_id, g_b_id, inst_b,
                                            Vec2().from_cartesian(ga.entities[a_id].px_n, ga.entities[a_id].py_n),
                                            Vec2(), 1.0)
                        if a_id not in events_a_end: events_a_end[a_id] = []
                        events_a_end[a_id].append(ev)

                if callbacks[3] is not None:
                    inst_b = self.group_instances[g_b_id][b_id]
                    inst_a = self.group_instances[g_a_id][a_id]
                    if inst_b is not None and inst_a is not None:
                        ev = CollisionEvent(col_id, r_id, g_a_id, inst_a,
                                            Vec2().from_cartesian(gb.entities[b_id].px_n, gb.entities[b_id].py_n),
                                            Vec2(), 1.0)
                        if b_id not in events_b_end: events_b_end[b_id] = []
                        events_b_end[b_id].append(ev)

                to_remove.push_back(pair_key)
            inc(it)

        to_remove_sz = to_remove.size()
        for k in range(to_remove_sz):
            rel.active_cols.erase(to_remove[k])

        # --- START CALLBACKS ---
        for ent_id, evs in events_a_start.items():
            evs.sort(key=lambda e: e[0].time)
            actual_evs = [e[0] for e in evs]
            ret = callbacks[0](self.group_instances[g_a_id][ent_id], actual_evs)
            rel = &self.relations[r_id]
            if ret is not None:
                ret_len = len(ret) if len(ret) < len(evs) else len(evs)
                for idx in range(ret_len):
                    if not ret[idx]:
                        rel.active_cols.erase(<uint64_t> evs[idx][1])

        for ent_id, evs in events_b_start.items():
            evs.sort(key=lambda e: e[0].time)
            actual_evs = [e[0] for e in evs]
            ret = callbacks[2](self.group_instances[g_b_id][ent_id], actual_evs)
            rel = &self.relations[r_id]
            if ret is not None:
                ret_len = len(ret) if len(ret) < len(evs) else len(evs)
                for idx in range(ret_len):
                    if not ret[idx]:
                        rel.active_cols.erase(<uint64_t> evs[idx][1])

        # --- END CALLBACKS ---
        for ent_id, evs in events_a_end.items():
            callbacks[1](self.group_instances[g_a_id][ent_id], evs)
            rel = &self.relations[r_id]

        for ent_id, evs in events_b_end.items():
            callbacks[3](self.group_instances[g_b_id][ent_id], evs)
            rel = &self.relations[r_id]

    def manual_collision(self, list group_ids, object start_position, object end_position, object size=None,
                         str hitbox_type="point", bint centered=False, double rotation=0.0,
                         list start_positions=None, object radius=None, object ignore_collisions=None) -> list:
        cdef EntityData ed
        cdef double cx, cy, cx_o, cy_o, hw, hh, cr, sr, ax, ay, dx, dy, ln
        cdef double pivot_x, pivot_y
        cdef size_t i, num_v
        cdef double min_px, min_py, max_px_o, max_px_n, max_px, max_py_o, max_py_n, max_py
        cdef list events
        cdef int g_id, lvl, min_cx, min_cy, max_cx, max_cy, grid_cx, grid_cy, b_id
        cdef double c_size, norm_x, norm_y, t, a_dx, a_dy, b_dx, b_dy
        cdef uint64_t key
        cdef vector[int] * cell_b
        cdef CollisionGroupStruct * gb
        cdef EntityData * eb
        cdef unordered_set[int] checked
        cdef size_t cell_b_sz, vx_o_sz, vx_n_sz, vx_o_sz2, vx_n_sz2, vx_o_sz3, vx_n_sz3, grp_sz
        cdef double _rad
        cdef object inst_b
        cdef bint ignore
        cdef size_t ig_a_sz, ig_b_sz, ig_a_i, ig_b_i

        events = []
        ed.h_type = 4
        if hitbox_type == "aabb":
            ed.h_type = 0
        elif hitbox_type == "obb":
            ed.h_type = 1
        elif hitbox_type == "triangle":
            ed.h_type = 2
        elif hitbox_type == "polygon":
            ed.h_type = 3
        elif hitbox_type == "circle":
            ed.h_type = 5

        _rad = 0.0
        if radius is not None:
            _rad = radius
        elif size is not None:
            _rad = size.x / 2.0
        ed.radius = _rad

        ed.ignore_collisions.clear()
        if ignore_collisions is not None:
            if isinstance(ignore_collisions, list):
                for ig in ignore_collisions:
                    ed.ignore_collisions.push_back(ig)
            else:
                ed.ignore_collisions.push_back(ignore_collisions)

        ed.is_centered = centered
        ed.rot = rotation
        ed.px_o = start_position.x
        ed.py_o = start_position.y
        ed.px_n = end_position.x
        ed.py_n = end_position.y

        if size is not None:
            ed.sx = size.x
            ed.sy = size.y
        else:
            ed.sx = 0.0
            ed.sy = 0.0

        if ed.h_type == 0:
            if ed.is_centered:
                cx = ed.px_n - (ed.sx / 2.0);
                cy = ed.py_n - (ed.sy / 2.0)
            else:
                cx = ed.px_n;
                cy = ed.py_n
            ed.vx_n.push_back(cx);
            ed.vy_n.push_back(cy)
            ed.vx_n.push_back(cx + ed.sx);
            ed.vy_n.push_back(cy)
            ed.vx_n.push_back(cx + ed.sx);
            ed.vy_n.push_back(cy + ed.sy)
            ed.vx_n.push_back(cx);
            ed.vy_n.push_back(cy + ed.sy)
            ed.axes_x.push_back(1.0);
            ed.axes_y.push_back(0.0)
            ed.axes_x.push_back(0.0);
            ed.axes_y.push_back(1.0)

        elif ed.h_type == 1:
            cr = cos(ed.rot);
            sr = sin(ed.rot)
            if ed.is_centered:
                hw = ed.sx / 2.0;
                hh = ed.sy / 2.0
                ed.vx_n.push_back(ed.px_n - hw * cr + hh * sr);
                ed.vy_n.push_back(ed.py_n - hw * sr - hh * cr)
                ed.vx_n.push_back(ed.px_n + hw * cr + hh * sr);
                ed.vy_n.push_back(ed.py_n + hw * sr - hh * cr)
                ed.vx_n.push_back(ed.px_n + hw * cr - hh * sr);
                ed.vy_n.push_back(ed.py_n + hw * sr + hh * cr)
                ed.vx_n.push_back(ed.px_n - hw * cr - hh * sr);
                ed.vy_n.push_back(ed.py_n - hw * sr + hh * cr)
            else:
                ed.vx_n.push_back(ed.px_n);
                ed.vy_n.push_back(ed.py_n)
                ed.vx_n.push_back(ed.px_n + ed.sx * cr);
                ed.vy_n.push_back(ed.py_n + ed.sx * sr)
                ed.vx_n.push_back(ed.px_n + ed.sx * cr - ed.sy * sr);
                ed.vy_n.push_back(ed.py_n + ed.sx * sr + ed.sy * cr)
                ed.vx_n.push_back(ed.px_n - ed.sy * sr);
                ed.vy_n.push_back(ed.py_n + ed.sy * cr)
            ed.axes_x.push_back(cr);
            ed.axes_y.push_back(sr)
            ed.axes_x.push_back(-sr);
            ed.axes_y.push_back(cr)

        elif ed.h_type == 2 or ed.h_type == 3:
            if start_positions is not None:
                ax = 0;
                ay = 0
                for p in start_positions:
                    ed.vx_o.push_back(p.x);
                    ed.vy_o.push_back(p.y)
                    ax += p.x;
                    ay += p.y
                ed.px_o = ax / len(start_positions)
                ed.py_o = ay / len(start_positions)

                dx = ed.px_n - ed.px_o
                dy = ed.py_n - ed.py_o

                vx_o_sz = ed.vx_o.size()
                for i in range(vx_o_sz):
                    ed.vx_n.push_back(ed.vx_o[i] + dx)
                    ed.vy_n.push_back(ed.vy_o[i] + dy)

                num_v = ed.vx_n.size()
                for i in range(num_v):
                    dx = ed.vx_n[(i + 1) % num_v] - ed.vx_n[i]
                    dy = ed.vy_n[(i + 1) % num_v] - ed.vy_n[i]
                    ln = sqrt(dx * dx + dy * dy)
                    if ln > 0.0001:
                        ed.axes_x.push_back(-dy / ln)
                        ed.axes_y.push_back(dx / ln)

        elif ed.h_type == 4:
            ed.sx = 0.0;
            ed.sy = 0.0
            ed.vx_n.push_back(ed.px_n);
            ed.vy_n.push_back(ed.py_n)
            ed.vx_o.push_back(ed.px_o);
            ed.vy_o.push_back(ed.py_o)

        elif ed.h_type == 5:
            if ed.is_centered:
                cx = ed.px_n;
                cy = ed.py_n
            else:
                cx = ed.px_n + ed.radius;
                cy = ed.py_n + ed.radius
            ed.vx_n.push_back(cx);
            ed.vy_n.push_back(cy)

        vx_o_sz2 = ed.vx_o.size()
        vx_n_sz2 = ed.vx_n.size()
        if vx_o_sz2 == 0 and vx_n_sz2 > 0:
            dx = ed.px_n - ed.px_o
            dy = ed.py_n - ed.py_o
            for i in range(vx_n_sz2):
                ed.vx_o.push_back(ed.vx_n[i] - dx)
                ed.vy_o.push_back(ed.vy_n[i] - dy)

        if ed.h_type == 0 or ed.h_type == 4:
            min_px = ed.vx_o[0] if ed.vx_o[0] < ed.vx_n[0] else ed.vx_n[0]
            min_py = ed.vy_o[0] if ed.vy_o[0] < ed.vy_n[0] else ed.vy_n[0]
            max_px_o = ed.vx_o[0] + ed.sx;
            max_px_n = ed.vx_n[0] + ed.sx
            max_px = max_px_o if max_px_o > max_px_n else max_px_n
            max_py_o = ed.vy_o[0] + ed.sy;
            max_py_n = ed.vy_n[0] + ed.sy
            max_py = max_py_o if max_py_o > max_py_n else max_py_n
        elif ed.h_type == 5:
            min_px = (ed.vx_o[0] if ed.vx_o[0] < ed.vx_n[0] else ed.vx_n[0]) - ed.radius
            min_py = (ed.vy_o[0] if ed.vy_o[0] < ed.vy_n[0] else ed.vy_n[0]) - ed.radius
            max_px = (ed.vx_o[0] if ed.vx_o[0] > ed.vx_n[0] else ed.vx_n[0]) + ed.radius
            max_py = (ed.vy_o[0] if ed.vy_o[0] > ed.vy_n[0] else ed.vy_n[0]) + ed.radius
        else:
            min_px = ed.vx_o[0];
            max_px = ed.vx_o[0]
            min_py = ed.vy_o[0];
            max_py = ed.vy_o[0]
            vx_o_sz3 = ed.vx_o.size()
            for j in range(1, vx_o_sz3):
                if ed.vx_o[j] < min_px:
                    min_px = ed.vx_o[j]
                elif ed.vx_o[j] > max_px:
                    max_px = ed.vx_o[j]
                if ed.vy_o[j] < min_py:
                    min_py = ed.vy_o[j]
                elif ed.vy_o[j] > max_py:
                    max_py = ed.vy_o[j]
            vx_n_sz3 = ed.vx_n.size()
            for j in range(vx_n_sz3):
                if ed.vx_n[j] < min_px:
                    min_px = ed.vx_n[j]
                elif ed.vx_n[j] > max_px:
                    max_px = ed.vx_n[j]
                if ed.vy_n[j] < min_py:
                    min_py = ed.vy_n[j]
                elif ed.vy_n[j] > max_py:
                    max_py = ed.vy_n[j]

        grp_sz = self.groups.size()
        for g_id in group_ids:
            if g_id < 0 or g_id >= <int> grp_sz: continue
            gb = &self.groups[g_id]
            checked.clear()

            for lvl in range(gb.max_level + 1):
                c_size = self.cell_sizes[lvl]
                min_cx = <int> floor(min_px / c_size)
                min_cy = <int> floor(min_py / c_size)
                max_cx = <int> floor(max_px / c_size)
                max_cy = <int> floor(max_py / c_size)

                for grid_cy in range(min_cy, max_cy + 1):
                    for grid_cx in range(min_cx, max_cx + 1):
                        key = (<uint64_t> grid_cx << 32) | (<uint64_t> grid_cy & 0xFFFFFFFF)
                        if self.grids[lvl][g_id].count(key) == 0: continue

                        cell_b = &self.grids[lvl][g_id][key]
                        cell_b_sz = cell_b[0].size()
                        for j in range(cell_b_sz):
                            b_id = cell_b[0][j]
                            if checked.count(b_id): continue
                            checked.insert(b_id)

                            eb = &gb.entities[b_id]
                            if not eb.active: continue
                            if not eb.is_active: continue

                            ignore = False
                            ig_a_sz = ed.ignore_collisions.size()
                            ig_b_sz = eb.ignore_collisions.size()

                            if ig_a_sz > 0 and ig_b_sz > 0:
                                for ig_a_i in range(ig_a_sz):
                                    for ig_b_i in range(ig_b_sz):
                                        if ed.ignore_collisions[ig_a_i] == eb.ignore_collisions[ig_b_i]:
                                            ignore = True
                                            break
                                    if ignore: break
                            if ignore: continue

                            hit = False
                            if ed.h_type == 0 and eb.h_type == 0:
                                hit = aabb_aabb_swept(
                                    ed.vx_o[0], ed.vy_o[0], ed.vx_n[0], ed.vy_n[0], ed.sx, ed.sy,
                                    eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                                    False, &norm_x, &norm_y, &t)
                            elif ed.h_type == 0 and (eb.h_type == 4 or eb.h_type == 5):
                                hit = aabb_circle_swept(
                                    ed.vx_o[0], ed.vy_o[0], ed.vx_n[0], ed.vy_n[0], ed.sx, ed.sy,
                                    eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.radius,
                                    False, &norm_x, &norm_y, &t)
                            elif (ed.h_type == 4 or ed.h_type == 5) and eb.h_type == 0:
                                hit = aabb_circle_swept(
                                    eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                                    ed.vx_o[0], ed.vy_o[0], ed.vx_n[0], ed.vy_n[0], ed.radius,
                                    False, &norm_x, &norm_y, &t)
                                norm_x = -norm_x
                                norm_y = -norm_y
                            elif (ed.h_type == 4 or ed.h_type == 5) and (eb.h_type == 4 or eb.h_type == 5):
                                hit = circle_circle_swept(
                                    ed.vx_o[0], ed.vy_o[0], ed.vx_n[0], ed.vy_n[0], ed.radius,
                                    eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.radius,
                                    False, &norm_x, &norm_y, &t)
                            elif ed.h_type >= 4 and eb.h_type < 4:
                                a_dx = ed.px_n - ed.px_o
                                a_dy = ed.py_n - ed.py_o
                                b_dx = eb.px_n - eb.px_o
                                b_dy = eb.py_n - eb.py_o
                                hit = circle_poly_swept(
                                    ed.vx_o[0], ed.vy_o[0], ed.vx_n[0], ed.vy_n[0], ed.radius,
                                    eb.vx_o.data(), eb.vy_o.data(), eb.vx_n.data(), eb.vy_n.data(), eb.vx_o.size(),
                                    eb.axes_x.data(), eb.axes_y.data(), eb.axes_x.size(), b_dx, b_dy,
                                    False, &norm_x, &norm_y, &t
                                )
                            elif ed.h_type < 4 and eb.h_type >= 4:
                                a_dx = ed.px_n - ed.px_o
                                a_dy = ed.py_n - ed.py_o
                                b_dx = eb.px_n - eb.px_o
                                b_dy = eb.py_n - eb.py_o
                                hit = circle_poly_swept(
                                    eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.radius,
                                    ed.vx_o.data(), ed.vy_o.data(), ed.vx_n.data(), ed.vy_n.data(), ed.vx_o.size(),
                                    ed.axes_x.data(), ed.axes_y.data(), ed.axes_x.size(), a_dx, a_dy,
                                    False, &norm_x, &norm_y, &t
                                )
                                norm_x = -norm_x
                                norm_y = -norm_y
                            else:
                                a_dx = ed.px_n - ed.px_o
                                a_dy = ed.py_n - ed.py_o
                                b_dx = eb.px_n - eb.px_o
                                b_dy = eb.py_n - eb.py_o
                                hit = poly_poly_swept(
                                    ed.vx_o.data(), ed.vy_o.data(), ed.vx_o.size(),
                                    ed.axes_x.data(), ed.axes_y.data(), ed.axes_x.size(), a_dx, a_dy,
                                    eb.vx_o.data(), eb.vy_o.data(), eb.vx_o.size(),
                                    eb.axes_x.data(), eb.axes_y.data(), eb.axes_x.size(), b_dx, b_dy,
                                    False, &norm_x, &norm_y, &t
                                )

                            if hit:
                                inst_b = self.group_instances[g_id][b_id]
                                imp_ax = ed.px_o + ((ed.px_n - ed.px_o) * t)
                                imp_ay = ed.py_o + ((ed.py_n - ed.py_o) * t)
                                events.append(
                                    CollisionEvent(-1, -1, g_id, inst_b, Vec2().from_cartesian(imp_ax, imp_ay),
                                                   Vec2().from_cartesian(norm_x, norm_y), t))

        events.sort(key=lambda e: e.time)
        return events

    def get_points(self, int group_id, int entity_id) -> list:
        if group_id < 0 or group_id >= self.groups.size(): return []
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef size_t ent_sz
        cdef EntityData * ed
        cdef list points
        cdef size_t i, vx_n_sz

        ent_sz = group.entities.size()
        if entity_id < 0 or entity_id >= <int> ent_sz:
            return []

        ed = &group.entities[entity_id]
        if not ed.active:
            return []

        points = []

        if ed.h_type == 5:
            for i in range(8):
                points.append(Vec2().from_cartesian(
                    ed.vx_n[0] + ed.radius * cos(i * 3.14159 / 4.0),
                    ed.vy_n[0] + ed.radius * sin(i * 3.14159 / 4.0)
                ))
            return points

        vx_n_sz = ed.vx_n.size()
        for i in range(vx_n_sz):
            points.append(Vec2().from_cartesian(ed.vx_n[i], ed.vy_n[i]))

        return points

    def get_hitbox(self, int group_id) -> str:
        if group_id < 0 or group_id >= self.groups.size():
            return ""

        cdef int h_type = self.groups.data()[group_id].h_type

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

    def get_position(self, int group_id, int entity_id):
        if group_id < 0 or group_id >= self.groups.size():
            return None

        cdef int e_size = self.groups.data()[group_id].entities.size()
        if entity_id < 0 or entity_id >= e_size:
            return None

        cdef EntityData * ed = &self.groups.data()[group_id].entities.data()[entity_id]
        if not ed.active:
            return None

        cdef double px = ed.px_n
        cdef double py = ed.py_n

        # Force top-left translation if it was registered as centered
        if ed.is_centered:
            px -= (ed.sx / 2.0)
            py -= (ed.sy / 2.0)

        return Vec2().from_cartesian(px, py)

    def get_size(self, int group_id, int entity_id):
        if group_id < 0 or group_id >= self.groups.size():
            return None

        cdef int e_size = self.groups.data()[group_id].entities.size()
        if entity_id < 0 or entity_id >= e_size:
            return None

        cdef EntityData * ed = &self.groups.data()[group_id].entities.data()[entity_id]
        if not ed.active:
            return None

        return Vec2().from_cartesian(ed.sx, ed.sy)

    def get_radius(self, int group_id, int entity_id) -> float:
        cdef vector[CollisionGroupStruct] * _g = &self.groups
        if group_id < 0 or group_id >= _g[0].size():
            return 0.0

        cdef CollisionGroupStruct * group = &(_g[0][group_id])
        if entity_id < 0 or entity_id >= group.entities.size():
            return 0.0

        cdef EntityData * ed = &group.entities.data()[entity_id]
        if not ed.active:
            return 0.0

        # Radius is exactly half the width (size.x / 2)
        return ed.sx / 2.0
