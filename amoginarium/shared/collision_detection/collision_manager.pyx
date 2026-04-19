# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False

from .collision_manager cimport CollisionManager, CollisionGroupStruct, EntityData, CollisionRelationStruct, DeferredDeletion
from .collision_methods cimport aabb_aabb_swept, swept_sat_generic
from .collision_event import CollisionEvent
from amoginarium.shared.utility import Vec2
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector
from libc.stdint cimport uint64_t
from libc.math cimport floor, cos, sin, sqrt

cdef class CollisionManager:
    def __init__(self, double base_cell_size=1000.0, list level_dividers=None):
        self.base_cell_size = base_cell_size
        self.cell_sizes.push_back(base_cell_size)

        cdef double current_size = base_cell_size
        if level_dividers:
            for div in level_dividers:
                current_size = current_size / div
                self.cell_sizes.push_back(current_size)

        self.grids.resize(self.cell_sizes.size())
        self.group_instances = []
        self.relation_callbacks = []

    def add_group(self, int max_level, bint is_static=False, str hitbox_type="aabb") -> int:
        if max_level >= self.cell_sizes.size():
            max_level = self.cell_sizes.size() - 1

        cdef int g_id = self.groups.size()
        cdef CollisionGroupStruct group
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

        self.groups.push_back(group)
        self.group_instances.append([])

        cdef int lvl
        for lvl in range(max_level + 1):
            self.grids[lvl][g_id] = unordered_map[uint64_t, vector[int]]()

        return g_id

    def clear_all_entities(self):
        cdef size_t i
        cdef int lvl
        cdef CollisionGroupStruct * group

        self.pending_deletions.clear()

        for i in range(self.groups.size()):
            group = &self.groups[i]
            group.entities.clear()
            group.free_ids.clear()
            self.group_instances[i].clear()
            for lvl in range(group.max_level + 1):
                self.grids[lvl][i].clear()

    def register_entity(self, int group_id, object instance, object pos=None, object size=None, bint centered=False,
                        object rotation=0.0, object positions=None) -> int:
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef int e_id, lvl
        cdef EntityData ed

        if not group.free_ids.empty():
            e_id = group.free_ids.back()
            group.free_ids.pop_back()

            group.entities[e_id].active = True
            group.entities[e_id].h_type = group.h_type
            group.entities[e_id].is_centered = centered
            group.entities[e_id].rot = rotation

            if pos is not None:
                group.entities[e_id].px_o = pos.x
                group.entities[e_id].py_o = pos.y
                group.entities[e_id].px_n = pos.x
                group.entities[e_id].py_n = pos.y
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

            group.entities[e_id].col_groups.clear()
            group.entities[e_id].col_entities.clear()
            group.entities[e_id].col_nx.clear()
            group.entities[e_id].col_ny.clear()
            group.entities[e_id].prev_col_groups.clear()
            group.entities[e_id].prev_col_entities.clear()
            group.entities[e_id].prev_col_nx.clear()
            group.entities[e_id].prev_col_ny.clear()

            for lvl in range(group.max_level + 1):
                group.entities[e_id].bound_min_x[lvl] = -2147483647
                group.entities[e_id].bound_min_y[lvl] = -2147483647
                group.entities[e_id].bound_max_x[lvl] = -2147483647
                group.entities[e_id].bound_max_y[lvl] = -2147483647
                group.entities[e_id].grid_keys[lvl].clear()

            self.group_instances[group_id][e_id] = instance
        else:
            e_id = group.entities.size()
            ed.id = e_id
            ed.active = True
            ed.h_type = group.h_type
            ed.is_centered = centered
            ed.rot = rotation

            if pos is not None:
                ed.px_o = pos.x
                ed.py_o = pos.y
                ed.px_n = pos.x
                ed.py_n = pos.y
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

        self.update_entity(group_id, e_id, pos, size, centered, rotation, positions, True)
        return e_id

    def delete_entity(self, int group_id, int entity_id):
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef EntityData * ed
        cdef DeferredDeletion dd

        if entity_id < 0 or entity_id >= group.entities.size(): return

        ed = &group.entities[entity_id]
        if not ed.active: return

        ed.active = False
        dd.group_id = group_id
        dd.entity_id = entity_id
        self.pending_deletions.push_back(dd)

    cdef void _flush_deletions(self):
        cdef size_t i, j
        cdef int g_id, e_id, lvl
        cdef CollisionGroupStruct * group
        cdef EntityData * ed
        cdef vector[uint64_t] * keys

        for i in range(self.pending_deletions.size()):
            g_id = self.pending_deletions[i].group_id
            e_id = self.pending_deletions[i].entity_id
            group = &self.groups[g_id]
            ed = &group.entities[e_id]

            if e_id < len(self.group_instances[g_id]):
                self.group_instances[g_id][e_id] = None

            for lvl in range(group.max_level + 1):
                keys = &ed.grid_keys[lvl]
                for j in range(keys.size()):
                    self._remove_from_cell(lvl, g_id, keys[0][j], e_id)
                keys.clear()

            group.free_ids.push_back(e_id)

        self.pending_deletions.clear()

    def update_entity(self, int group_id, int entity_id, object pos=None, object size=None, object centered=None,
                      object rotation=None, object positions=None, bint shift_history=True):
        cdef EntityData * ed = &self.groups[group_id].entities[entity_id]
        if not ed.active: return

        if shift_history:
            ed.px_o = ed.px_n
            ed.py_o = ed.py_n
            ed.vx_o = ed.vx_n
            ed.vy_o = ed.vy_n

        cdef double old_px_n = ed.px_n
        cdef double old_py_n = ed.py_n

        cdef double cx, cy, hw, hh, cr, sr, ax, ay, dx, dy, ln
        cdef double pivot_x, pivot_y
        cdef size_t i, num_v

        if centered is not None: ed.is_centered = centered
        if size is not None: ed.sx = size.x; ed.sy = size.y
        if rotation is not None: ed.rot = rotation
        if pos is not None:
            ed.px_n = pos.x
            ed.py_n = pos.y

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
            if ed.axes_x.empty():
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
            elif pos is not None:
                dx = ed.px_n - old_px_n
                dy = ed.py_n - old_py_n
                for i in range(ed.vx_n.size()):
                    ed.vx_n[i] += dx
                    ed.vy_n[i] += dy

        if ed.vx_o.empty() or ed.vx_o.size() == 0:
            ed.vx_o = ed.vx_n
            ed.vy_o = ed.vy_n

        if not self.groups[group_id].is_static:
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
        cdef size_t i, j

        if ed.h_type == 0:
            min_px = ed.vx_o[0] if ed.vx_o[0] < ed.vx_n[0] else ed.vx_n[0]
            min_py = ed.vy_o[0] if ed.vy_o[0] < ed.vy_n[0] else ed.vy_n[0]
            max_px_o = ed.vx_o[0] + ed.sx
            max_px_n = ed.vx_n[0] + ed.sx
            max_px = max_px_o if max_px_o > max_px_n else max_px_n
            max_py_o = ed.vy_o[0] + ed.sy
            max_py_n = ed.vy_n[0] + ed.sy
            max_py = max_py_o if max_py_o > max_py_n else max_py_n
        else:
            min_px = ed.vx_o[0]
            max_px = ed.vx_o[0]
            min_py = ed.vy_o[0]
            max_py = ed.vy_o[0]
            for j in range(1, ed.vx_o.size()):
                if ed.vx_o[j] < min_px:
                    min_px = ed.vx_o[j]
                elif ed.vx_o[j] > max_px:
                    max_px = ed.vx_o[j]
                if ed.vy_o[j] < min_py:
                    min_py = ed.vy_o[j]
                elif ed.vy_o[j] > max_py:
                    max_py = ed.vy_o[j]
            for j in range(ed.vx_n.size()):
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
            for i in range(old_keys.size()):
                found = False
                for j in range(new_keys.size()):
                    if old_keys[0][i] == new_keys[j]:
                        found = True
                        break
                if not found: self._remove_from_cell(lvl, group_id, old_keys[0][i], entity_id)

            for i in range(new_keys.size()):
                found = False
                for j in range(old_keys.size()):
                    if new_keys[i] == old_keys[0][j]:
                        found = True
                        break
                if not found: self.grids[lvl][group_id][new_keys[i]].push_back(entity_id)

            ed.grid_keys[lvl] = new_keys

    cdef void _remove_from_cell(self, int lvl, int group_id, uint64_t key, int entity_id):
        cdef vector[int] * cell = &self.grids[lvl][group_id][key]
        cdef size_t i
        for i in range(cell.size()):
            if cell[0][i] == entity_id:
                cell[0][i] = cell.back()
                cell.pop_back()
                break
        if cell.empty():
            self.grids[lvl][group_id].erase(key)

    def create_relation(self, int group_a_id, int group_b_id, object cb_a_on_col=None, object cb_b_on_col=None,
                        object cb_a_set_norm=None, object cb_b_set_norm=None):
        cdef CollisionRelationStruct rel
        rel.group_a_id = group_a_id
        rel.group_b_id = group_b_id
        self.relations.push_back(rel)
        self.relation_callbacks.append((cb_a_on_col, cb_b_on_col, cb_a_set_norm, cb_b_set_norm))

    def calculate_all_collisions(self):
        self._flush_deletions()

        cdef int g, e
        cdef EntityData * ed
        for g in range(self.groups.size()):
            for e in range(self.groups[g].entities.size()):
                ed = &self.groups[g].entities[e]
                if not ed.active: continue
                ed.prev_col_groups = ed.col_groups
                ed.prev_col_entities = ed.col_entities
                ed.prev_col_nx = ed.col_nx
                ed.prev_col_ny = ed.col_ny
                ed.col_groups.clear()
                ed.col_entities.clear()
                ed.col_nx.clear()
                ed.col_ny.clear()

        cdef size_t i
        for i in range(self.relations.size()):
            self._calc_relation(self.relations[i], self.relation_callbacks[i])

        self._dispatch_set_normals()
        self._flush_deletions()

    cdef void _calc_relation(self, CollisionRelationStruct rel, tuple callbacks):
        cdef CollisionGroupStruct * ga = &self.groups[rel.group_a_id]
        cdef CollisionGroupStruct * gb = &self.groups[rel.group_b_id]
        cdef bint is_same = (rel.group_a_id == rel.group_b_id)

        cdef int check_lvl = ga.max_level if ga.max_level < gb.max_level else gb.max_level
        cdef unordered_set[uint64_t] checked_pairs
        cdef uint64_t pair_key, min_id, max_id

        cdef EntityData * ea
        cdef EntityData * eb
        cdef double norm_x, norm_y, t
        cdef double imp_ax, imp_ay, imp_bx, imp_by

        cdef vector[uint64_t] * a_keys
        cdef vector[int] * cell_b

        cdef size_t a_idx, k_idx, b_idx, j, k
        cdef int b_id
        cdef int iterations
        cdef bint hit_this_iteration
        cdef bint duplicate
        cdef bint is_new
        cdef bint hit
        cdef double a_dx, a_dy, b_dx, b_dy

        cdef list events_a = []
        cdef list events_b = []

        for a_idx in range(ga.entities.size()):
            ea = &ga.entities[a_idx]
            if not ea.active: continue

            iterations = 0
            hit_this_iteration = True

            while hit_this_iteration and iterations < 3:
                hit_this_iteration = False
                iterations += 1

                ea = &ga.entities[a_idx]
                if not ea.active: break

                a_keys = &ea.grid_keys[check_lvl]

                for k_idx in range(a_keys.size()):
                    if not ea.active: break

                    if self.grids[check_lvl][rel.group_b_id].count(a_keys[0][k_idx]) == 0:
                        continue

                    cell_b = &self.grids[check_lvl][rel.group_b_id][a_keys[0][k_idx]]

                    for b_idx in range(cell_b.size()):
                        b_id = cell_b[0][b_idx]

                        if is_same and ea.id == b_id:
                            continue

                        eb = &gb.entities[b_id]
                        if not eb.active: continue

                        if is_same:
                            min_id = ea.id if ea.id < b_id else b_id
                            max_id = b_id if ea.id < b_id else ea.id
                            pair_key = (<uint64_t> min_id << 32) | <uint64_t> max_id
                        else:
                            pair_key = (<uint64_t> ea.id << 32) | <uint64_t> b_id

                        if checked_pairs.count(pair_key): continue
                        checked_pairs.insert(pair_key)

                        hit = False

                        if ea.h_type == 0 and eb.h_type == 0:
                            hit = aabb_aabb_swept(
                                ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.sx, ea.sy,
                                eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                                &norm_x, &norm_y, &t
                            )
                        else:
                            a_dx = ea.px_n - ea.px_o
                            a_dy = ea.py_n - ea.py_o
                            b_dx = eb.px_n - eb.px_o
                            b_dy = eb.py_n - eb.py_o

                            hit = swept_sat_generic(
                                ea.vx_o, ea.vy_o, ea.vx_n, ea.vy_n, ea.axes_x, ea.axes_y, a_dx, a_dy,
                                eb.vx_o, eb.vy_o, eb.vx_n, eb.vy_n, eb.axes_x, eb.axes_y, b_dx, b_dy,
                                &norm_x, &norm_y, &t
                            )

                        if hit:
                            imp_ax = ea.px_o + ((ea.px_n - ea.px_o) * t)
                            imp_ay = ea.py_o + ((ea.py_n - ea.py_o) * t)
                            imp_bx = eb.px_o + ((eb.px_n - eb.px_o) * t)
                            imp_by = eb.py_o + ((eb.py_n - eb.py_o) * t)

                            duplicate = False
                            for j in range(ea.col_groups.size()):
                                if ea.col_groups[j] == rel.group_b_id and ea.col_entities[j] == b_id and abs(
                                        ea.col_nx[j] - norm_x) < 0.01 and abs(
                                        ea.col_ny[j] - norm_y) < 0.01:
                                    duplicate = True
                                    break

                            if not duplicate:
                                ea.col_groups.push_back(rel.group_b_id)
                                ea.col_entities.push_back(b_id)
                                ea.col_nx.push_back(norm_x)
                                ea.col_ny.push_back(norm_y)

                                is_new = True
                                for k in range(ea.prev_col_groups.size()):
                                    if ea.prev_col_groups[k] == rel.group_b_id and ea.prev_col_entities[
                                        k] == b_id and abs(
                                            ea.prev_col_nx[k] - norm_x) < 0.01 and abs(
                                        ea.prev_col_ny[k] - norm_y) < 0.01:
                                        is_new = False
                                        break

                                if is_new and callbacks[0] is not None:
                                    events_a.append((ea.id, b_id, imp_ax, imp_ay, norm_x, norm_y))

                            duplicate = False
                            for j in range(eb.col_groups.size()):
                                if eb.col_groups[j] == rel.group_a_id and eb.col_entities[j] == ea.id and abs(
                                        eb.col_nx[j] - (-norm_x)) < 0.01 and abs(
                                        eb.col_ny[j] - (-norm_y)) < 0.01:
                                    duplicate = True
                                    break

                            if not duplicate:
                                eb.col_groups.push_back(rel.group_a_id)
                                eb.col_entities.push_back(ea.id)
                                eb.col_nx.push_back(-norm_x)
                                eb.col_ny.push_back(-norm_y)

                                is_new = True
                                for k in range(eb.prev_col_groups.size()):
                                    if eb.prev_col_groups[k] == rel.group_a_id and eb.prev_col_entities[
                                        k] == ea.id and abs(
                                            eb.prev_col_nx[k] - (-norm_x)) < 0.01 and abs(
                                        eb.prev_col_ny[k] - (-norm_y)) < 0.01:
                                        is_new = False
                                        break

                                if is_new and callbacks[1] is not None:
                                    events_b.append((b_id, ea.id, imp_bx, imp_by, -norm_x, -norm_y))

                            hit_this_iteration = True
                            break

                    if hit_this_iteration:
                        break

        for ev in events_a:
            inst_a = self.group_instances[rel.group_a_id][ev[0]]
            inst_b = self.group_instances[rel.group_b_id][ev[1]]
            callbacks[0](inst_a, CollisionEvent(rel.group_b_id, inst_b, Vec2().from_cartesian(ev[2], ev[3]),
                                                Vec2().from_cartesian(ev[4], ev[5])))

        for ev in events_b:
            inst_b = self.group_instances[rel.group_b_id][ev[0]]
            inst_a = self.group_instances[rel.group_a_id][ev[1]]
            callbacks[1](inst_b, CollisionEvent(rel.group_a_id, inst_a, Vec2().from_cartesian(ev[2], ev[3]),
                                                Vec2().from_cartesian(ev[4], ev[5])))

    cdef void _dispatch_set_normals(self):
        cdef size_t i, a_idx, b_idx, j, k
        cdef CollisionRelationStruct rel
        cdef tuple cbs
        cdef CollisionGroupStruct * ga
        cdef CollisionGroupStruct * gb
        cdef EntityData * ea
        cdef EntityData * eb
        cdef bint is_same
        cdef bint changed, found
        cdef int c_cnt, p_cnt

        cdef list normal_events_a = []
        cdef list normal_events_b = []

        for i in range(self.relations.size()):
            rel = self.relations[i]
            cbs = self.relation_callbacks[i]
            ga = &self.groups[rel.group_a_id]
            gb = &self.groups[rel.group_b_id]
            is_same = (rel.group_a_id == rel.group_b_id)

            if cbs[2] is not None:
                for a_idx in range(ga.entities.size()):
                    ea = &ga.entities[a_idx]
                    if not ea.active: continue

                    c_cnt = 0
                    p_cnt = 0
                    for j in range(ea.col_groups.size()):
                        if ea.col_groups[j] == rel.group_b_id: c_cnt += 1
                    for j in range(ea.prev_col_groups.size()):
                        if ea.prev_col_groups[j] == rel.group_b_id: p_cnt += 1

                    changed = False
                    if c_cnt != p_cnt:
                        changed = True
                    else:
                        for j in range(ea.col_groups.size()):
                            if ea.col_groups[j] == rel.group_b_id:
                                found = False
                                for k in range(ea.prev_col_groups.size()):
                                    if ea.prev_col_groups[k] == rel.group_b_id and abs(
                                            ea.col_nx[j] - ea.prev_col_nx[k]) < 0.01 and abs(
                                            ea.col_ny[j] - ea.prev_col_ny[k]) < 0.01:
                                        found = True
                                        break
                                if not found:
                                    changed = True
                                    break

                    if changed:
                        curr_norms = []
                        for j in range(ea.col_groups.size()):
                            if ea.col_groups[j] == rel.group_b_id:
                                curr_norms.append(Vec2().from_cartesian(ea.col_nx[j], ea.col_ny[j]))
                        normal_events_a.append((cbs[2], rel.group_a_id, ea.id, rel.group_b_id, curr_norms))

            if not is_same and cbs[3] is not None:
                for b_idx in range(gb.entities.size()):
                    eb = &gb.entities[b_idx]
                    if not eb.active: continue

                    c_cnt = 0
                    p_cnt = 0
                    for j in range(eb.col_groups.size()):
                        if eb.col_groups[j] == rel.group_a_id: c_cnt += 1
                    for j in range(eb.prev_col_groups.size()):
                        if eb.prev_col_groups[j] == rel.group_a_id: p_cnt += 1

                    changed = False
                    if c_cnt != p_cnt:
                        changed = True
                    else:
                        for j in range(eb.col_groups.size()):
                            if eb.col_groups[j] == rel.group_a_id:
                                found = False
                                for k in range(eb.prev_col_groups.size()):
                                    if eb.prev_col_groups[k] == rel.group_a_id and abs(
                                            eb.col_nx[j] - eb.prev_col_nx[k]) < 0.01 and abs(
                                            eb.col_ny[j] - eb.prev_col_ny[k]) < 0.01:
                                        found = True
                                        break
                                if not found:
                                    changed = True
                                    break

                    if changed:
                        curr_norms = []
                        for j in range(eb.col_groups.size()):
                            if eb.col_groups[j] == rel.group_a_id:
                                curr_norms.append(Vec2().from_cartesian(eb.col_nx[j], eb.col_ny[j]))
                        normal_events_b.append((cbs[3], rel.group_b_id, eb.id, rel.group_a_id, curr_norms))

        for ev in normal_events_a:
            cb = ev[0]
            inst_a = self.group_instances[ev[1]][ev[2]]
            cb(inst_a, ev[3], ev[4])

        for ev in normal_events_b:
            cb = ev[0]
            inst_b = self.group_instances[ev[1]][ev[2]]
            cb(inst_b, ev[3], ev[4])

    def get_points(self, int group_id, int entity_id) -> list:
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        if entity_id < 0 or entity_id >= group.entities.size():
            return []

        cdef EntityData * ed = &group.entities[entity_id]
        if not ed.active:
            return []

        cdef list points = []
        cdef size_t i
        for i in range(ed.vx_n.size()):
            points.append(Vec2().from_cartesian(ed.vx_n[i], ed.vy_n[i]))

        return points
