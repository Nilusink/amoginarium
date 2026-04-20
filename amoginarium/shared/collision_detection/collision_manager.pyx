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
from cython.operator cimport dereference as deref, preincrement as inc

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
        self.next_col_id = 1

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
        elif hitbox_type == "point":
            group.h_type = 4

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

        for i in range(self.relations.size()):
            self.relations[i].active_cols.clear()
            self.relations[i].updated_cols.clear()

        for i in range(self.groups.size()):
            group = &self.groups[i]
            group.entities.clear()
            group.free_ids.clear()
            self.group_instances[i].clear()
            for lvl in range(group.max_level + 1):
                self.grids[lvl][i].clear()

    def register_entity(self, int group_id, object instance, object position=None, object size=None,
                        bint centered=False,
                        double rotation=0.0, list positions=None) -> int:
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
            e_id = group.entities.size()
            ed.id = e_id
            ed.active = True
            ed.h_type = group.h_type
            ed.is_centered = centered
            ed.rot = rotation

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

        self.update_entity(group_id, e_id, position, size, centered, rotation, positions, True)
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

    cdef void _cleanup_entity_collisions(self, int group_id, int entity_id):
        cdef CollisionRelationStruct * rel
        cdef uint64_t pair_key
        cdef uint64_t a_id, b_id
        cdef tuple cbs
        cdef list evs_a = []
        cdef list evs_b = []

        for i in range(self.relations.size()):
            rel = &self.relations[i]
            if rel.group_a_id == group_id or rel.group_b_id == group_id:
                cbs = self.relation_callbacks[i]

                it = rel.active_cols.begin()
                while it != rel.active_cols.end():
                    pair_key = deref(it).first
                    col_id = deref(it).second

                    a_id = pair_key >> 32
                    b_id = pair_key & 0xFFFFFFFF

                    if (rel.group_a_id == group_id and a_id == entity_id) or \
                            (rel.group_b_id == group_id and b_id == entity_id):

                        if cbs[1] is not None:
                            inst_a = self.group_instances[rel.group_a_id][a_id]
                            inst_b = self.group_instances[rel.group_b_id][b_id]
                            if inst_a is not None and inst_b is not None:
                                evs_a.append((inst_a, CollisionEvent(col_id, rel.id, rel.group_b_id, inst_b,
                                                                     Vec2().from_cartesian(
                                                                         self.groups[rel.group_a_id].entities[
                                                                             a_id].px_n,
                                                                         self.groups[rel.group_a_id].entities[
                                                                             a_id].py_n), Vec2(), 1.0)))

                        if cbs[3] is not None:
                            inst_b = self.group_instances[rel.group_b_id][b_id]
                            inst_a = self.group_instances[rel.group_a_id][a_id]
                            if inst_a is not None and inst_b is not None:
                                evs_b.append((inst_b, CollisionEvent(col_id, rel.id, rel.group_a_id, inst_a,
                                                                     Vec2().from_cartesian(
                                                                         self.groups[rel.group_b_id].entities[
                                                                             b_id].px_n,
                                                                         self.groups[rel.group_b_id].entities[
                                                                             b_id].py_n), Vec2(), 1.0)))

                        it = rel.active_cols.erase(it)
                    else:
                        inc(it)

                for ev in evs_a: cbs[1](ev[0], [ev[1]])
                for ev in evs_b: cbs[3](ev[0], [ev[1]])

    cdef void _flush_deletions(self):
        cdef size_t i, j
        cdef int g_id, e_id, lvl
        cdef CollisionGroupStruct * group
        cdef EntityData * ed
        cdef vector[uint64_t] * keys

        for i in range(self.pending_deletions.size()):
            g_id = self.pending_deletions[i].group_id
            e_id = self.pending_deletions[i].entity_id

            self._cleanup_entity_collisions(g_id, e_id)

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

    def update_entity(self, int group_id, int entity_id, object position=None, object size=None, object centered=None,
                      object rotation=None, list positions=None, bint shift_history=True):
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
        if position is not None:
            ed.px_n = position.x
            ed.py_n = position.y

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

                dx = ed.px_n - old_px_n
                dy = ed.py_n - old_py_n
                ed.vx_o.clear()
                ed.vy_o.clear()
                for i in range(ed.vx_n.size()):
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
                for i in range(ed.vx_n.size()):
                    ed.vx_n[i] += dx
                    ed.vy_n[i] += dy

        elif ed.h_type == 4:
            ed.sx = 0.0
            ed.sy = 0.0
            ed.vx_n.clear()
            ed.vy_n.clear()
            ed.vx_n.push_back(ed.px_n)
            ed.vy_n.push_back(ed.py_n)

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

        if ed.h_type == 0 or ed.h_type == 4:
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

    def create_relation(self, int group_a_id, int group_b_id, object cb_a_on_start=None, object cb_a_on_end=None,
                        object cb_b_on_start=None, object cb_b_on_end=None) -> int:
        cdef int r_id = self.relations.size()
        cdef CollisionRelationStruct rel
        rel.id = r_id
        rel.group_a_id = group_a_id
        rel.group_b_id = group_b_id
        self.relations.push_back(rel)
        self.relation_callbacks.append((cb_a_on_start, cb_a_on_end, cb_b_on_start, cb_b_on_end))
        return r_id

    def calculate_all_collisions(self):
        self._flush_deletions()
        cdef size_t i
        for i in range(self.relations.size()):
            self._calc_relation(&self.relations[i], self.relation_callbacks[i])

    def calculate_collisions(self, list relation_ids):
        self._flush_deletions()
        cdef int r_id
        for r_id in relation_ids:
            if 0 <= r_id < self.relations.size():
                self._calc_relation(&self.relations[r_id], self.relation_callbacks[r_id])

    cdef void _calc_relation(self, CollisionRelationStruct * rel, tuple callbacks):
        cdef CollisionGroupStruct * ga = &self.groups[rel.group_a_id]
        cdef CollisionGroupStruct * gb = &self.groups[rel.group_b_id]
        cdef bint is_same = (rel.group_a_id == rel.group_b_id)

        cdef int check_lvl = ga.max_level if ga.max_level < gb.max_level else gb.max_level
        cdef uint64_t pair_key, a_id, b_id
        cdef unordered_set[uint64_t] checked_pairs

        cdef EntityData * ea
        cdef EntityData * eb
        cdef double norm_x, norm_y, t
        cdef double imp_ax, imp_ay, imp_bx, imp_by

        cdef vector[uint64_t] * a_keys
        cdef vector[int] * cell_b

        cdef size_t a_idx, k_idx, b_idx, j, k
        cdef int iterations
        cdef bint hit
        cdef double a_dx, a_dy, b_dx, b_dy

        cdef bint is_active_col
        cdef int col_id

        # Local dicts to group start/end events per entity
        events_a_start = {}
        events_b_start = {}
        events_a_end = {}
        events_b_end = {}

        cdef int ret_len
        cdef list actual_evs
        cdef object ret

        rel.updated_cols.clear()

        for a_idx in range(ga.entities.size()):
            ea = &ga.entities[a_idx]
            if not ea.active: continue

            a_keys = &ea.grid_keys[check_lvl]

            for k_idx in range(a_keys.size()):
                if not ea.active: break

                if self.grids[check_lvl][rel.group_b_id].count(a_keys[0][k_idx]) == 0:
                    continue

                cell_b = &self.grids[check_lvl][rel.group_b_id][a_keys[0][k_idx]]

                for b_idx in range(cell_b.size()):
                    b_id = cell_b[0][b_idx]

                    if is_same and ea.id >= b_id:
                        continue

                    eb = &gb.entities[b_id]
                    if not eb.active: continue

                    pair_key = (<uint64_t> ea.id << 32) | <uint64_t> b_id
                    if checked_pairs.count(pair_key): continue
                    checked_pairs.insert(pair_key)

                    is_active_col = (rel.active_cols.count(pair_key) > 0)
                    hit = False

                    if (ea.h_type == 0 or ea.h_type == 4) and (eb.h_type == 0 or eb.h_type == 4):
                        hit = aabb_aabb_swept(
                            ea.vx_o[0], ea.vy_o[0], ea.vx_n[0], ea.vy_n[0], ea.sx, ea.sy,
                            eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                            is_active_col,
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
                            is_active_col,
                            &norm_x, &norm_y, &t
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
                                inst_b = self.group_instances[rel.group_b_id][b_id]
                                ev = CollisionEvent(col_id, rel.id, rel.group_b_id, inst_b,
                                                    Vec2().from_cartesian(imp_ax, imp_ay),
                                                    Vec2().from_cartesian(norm_x, norm_y), t)
                                if ea.id not in events_a_start: events_a_start[ea.id] = []
                                events_a_start[ea.id].append((ev, pair_key))

                            if callbacks[2] is not None:
                                inst_a = self.group_instances[rel.group_a_id][ea.id]
                                ev = CollisionEvent(col_id, rel.id, rel.group_a_id, inst_a,
                                                    Vec2().from_cartesian(imp_bx, imp_by),
                                                    Vec2().from_cartesian(-norm_x, -norm_y), t)
                                if b_id not in events_b_start: events_b_start[b_id] = []
                                events_b_start[b_id].append((ev, pair_key))

        cdef vector[uint64_t] to_remove
        it = rel.active_cols.begin()
        while it != rel.active_cols.end():
            pair_key = deref(it).first
            col_id = deref(it).second
            if rel.updated_cols.find(pair_key) == rel.updated_cols.end():
                a_id = pair_key >> 32
                b_id = pair_key & 0xFFFFFFFF

                if callbacks[1] is not None:
                    inst_a = self.group_instances[rel.group_a_id][a_id]
                    inst_b = self.group_instances[rel.group_b_id][b_id]
                    if inst_a is not None and inst_b is not None:
                        ev = CollisionEvent(col_id, rel.id, rel.group_b_id, inst_b,
                                            Vec2().from_cartesian(ga.entities[a_id].px_n, ga.entities[a_id].py_n),
                                            Vec2(), 1.0)
                        if a_id not in events_a_end: events_a_end[a_id] = []
                        events_a_end[a_id].append(ev)

                if callbacks[3] is not None:
                    inst_b = self.group_instances[rel.group_b_id][b_id]
                    inst_a = self.group_instances[rel.group_a_id][a_id]
                    if inst_b is not None and inst_a is not None:
                        ev = CollisionEvent(col_id, rel.id, rel.group_a_id, inst_a,
                                            Vec2().from_cartesian(gb.entities[b_id].px_n, gb.entities[b_id].py_n),
                                            Vec2(), 1.0)
                        if b_id not in events_b_end: events_b_end[b_id] = []
                        events_b_end[b_id].append(ev)

                to_remove.push_back(pair_key)
            inc(it)

        for k in range(to_remove.size()):
            rel.active_cols.erase(to_remove[k])

        for ent_id, evs in events_a_start.items():
            evs.sort(key=lambda e: e[0].time)
            actual_evs = [e[0] for e in evs]
            ret = callbacks[0](self.group_instances[rel.group_a_id][ent_id], actual_evs)
            if ret is not None:
                ret_len = len(ret) if len(ret) < len(evs) else len(evs)
                for idx in range(ret_len):
                    if not ret[idx]:
                        rel.active_cols.erase(<uint64_t> evs[idx][1])

        for ent_id, evs in events_b_start.items():
            evs.sort(key=lambda e: e[0].time)
            actual_evs = [e[0] for e in evs]
            ret = callbacks[2](self.group_instances[rel.group_b_id][ent_id], actual_evs)
            if ret is not None:
                ret_len = len(ret) if len(ret) < len(evs) else len(evs)
                for idx in range(ret_len):
                    if not ret[idx]:
                        rel.active_cols.erase(<uint64_t> evs[idx][1])

        for ent_id, evs in events_a_end.items():
            callbacks[1](self.group_instances[rel.group_a_id][ent_id], evs)

        for ent_id, evs in events_b_end.items():
            callbacks[3](self.group_instances[rel.group_b_id][ent_id], evs)

    def manual_collision(self, list group_ids, object start_position, object end_position, object size=None,
                         str hitbox_type="point", bint centered=False, double rotation=0.0,
                         list start_positions=None) -> list:
        cdef EntityData ed
        cdef double cx, cy, hw, hh, cr, sr, ax, ay, dx, dy, ln
        cdef double pivot_x, pivot_y
        cdef size_t i, num_v
        cdef double min_px, min_py, max_px_o, max_px_n, max_px, max_py_o, max_py_n, max_py
        cdef list events = []
        cdef int g_id, lvl, min_cx, min_cy, max_cx, max_cy, grid_cx, grid_cy, b_id
        cdef double c_size, norm_x, norm_y, t, a_dx, a_dy, b_dx, b_dy
        cdef uint64_t key
        cdef vector[int] * cell_b
        cdef CollisionGroupStruct * gb
        cdef EntityData * eb
        cdef unordered_set[int] checked

        ed.h_type = 4
        if hitbox_type == "aabb":
            ed.h_type = 0
        elif hitbox_type == "obb":
            ed.h_type = 1
        elif hitbox_type == "triangle":
            ed.h_type = 2
        elif hitbox_type == "polygon":
            ed.h_type = 3

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

                for i in range(ed.vx_o.size()):
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

        if ed.vx_o.empty() and not ed.vx_n.empty():
            dx = ed.px_n - ed.px_o
            dy = ed.py_n - ed.py_o
            for i in range(ed.vx_n.size()):
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
        else:
            min_px = ed.vx_o[0];
            max_px = ed.vx_o[0]
            min_py = ed.vy_o[0];
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

        for g_id in group_ids:
            if g_id < 0 or g_id >= self.groups.size(): continue
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
                        for j in range(cell_b.size()):
                            b_id = cell_b[0][j]
                            if checked.count(b_id): continue
                            checked.insert(b_id)

                            eb = &gb.entities[b_id]
                            if not eb.active: continue

                            hit = False
                            if (ed.h_type == 0 or ed.h_type == 4) and (eb.h_type == 0 or eb.h_type == 4):
                                hit = aabb_aabb_swept(ed.vx_o[0], ed.vy_o[0], ed.vx_n[0], ed.vy_n[0], ed.sx, ed.sy,
                                                      eb.vx_o[0], eb.vy_o[0], eb.vx_n[0], eb.vy_n[0], eb.sx, eb.sy,
                                                      False, &norm_x, &norm_y, &t)
                            else:
                                a_dx = ed.px_n - ed.px_o;
                                a_dy = ed.py_n - ed.py_o
                                b_dx = eb.px_n - eb.px_o;
                                b_dy = eb.py_n - eb.py_o
                                hit = swept_sat_generic(ed.vx_o, ed.vy_o, ed.vx_n, ed.vy_n, ed.axes_x, ed.axes_y, a_dx,
                                                        a_dy,
                                                        eb.vx_o, eb.vy_o, eb.vx_n, eb.vy_n, eb.axes_x, eb.axes_y, b_dx,
                                                        b_dy,
                                                        False, &norm_x, &norm_y, &t)

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