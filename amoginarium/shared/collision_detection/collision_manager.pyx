# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False

from .collision_manager cimport CollisionManager, CollisionGroupStruct, EntityData, CollisionRelationStruct, DeferredDeletion
from .collision_methods cimport aabb_aabb_swept
from .collision_event import CollisionEvent
from amoginarium.shared.utility import Vec2
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector
from libc.stdint cimport uint64_t
from libc.math cimport floor

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

    def add_group(self, int max_level, bint is_static=False) -> int:
        if max_level >= self.cell_sizes.size():
            max_level = self.cell_sizes.size() - 1

        cdef int g_id = self.groups.size()
        cdef CollisionGroupStruct group
        group.id = g_id
        group.max_level = max_level
        group.is_static = is_static
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

    def register_entity(self, int group_id, object instance, object pos, object size, bint centered=False) -> int:
        cdef CollisionGroupStruct * group = &self.groups[group_id]
        cdef int e_id
        cdef int lvl
        cdef EntityData ed

        cdef double px = pos.x
        cdef double py = pos.y
        if centered:
            px -= size.x / 2.0
            py -= size.y / 2.0

        if not group.free_ids.empty():
            e_id = group.free_ids.back()
            group.free_ids.pop_back()

            group.entities[e_id].active = True
            group.entities[e_id].is_centered = centered
            group.entities[e_id].px_o = px;
            group.entities[e_id].py_o = py
            group.entities[e_id].px_n = px;
            group.entities[e_id].py_n = py
            group.entities[e_id].sx = size.x;
            group.entities[e_id].sy = size.y

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
            ed.is_centered = centered
            ed.px_o = px;
            ed.py_o = py
            ed.px_n = px;
            ed.py_n = py
            ed.sx = size.x;
            ed.sy = size.y

            ed.grid_keys.resize(group.max_level + 1)
            ed.bound_min_x.resize(group.max_level + 1, -2147483647)
            ed.bound_min_y.resize(group.max_level + 1, -2147483647)
            ed.bound_max_x.resize(group.max_level + 1, -2147483647)
            ed.bound_max_y.resize(group.max_level + 1, -2147483647)

            group.entities.push_back(ed)
            self.group_instances[group_id].append(instance)

        self._update_entity_grid(group_id, e_id)
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
                    self._remove_from_cell(lvl, g_id, keys.at(j), e_id)
                keys.clear()

            group.free_ids.push_back(e_id)

        self.pending_deletions.clear()

    def update_entity(self, int group_id, int entity_id, object pos=None, object size=None, object centered=None):
        cdef EntityData * ed = &self.groups[group_id].entities[entity_id]

        if not ed.active:
            return

        if centered is not None:
            ed.is_centered = centered

        if size is not None:
            ed.sx = size.x
            ed.sy = size.y

        if pos is not None:
            ed.px_o = ed.px_n
            ed.py_o = ed.py_n

            if ed.is_centered:
                ed.px_n = pos.x - (ed.sx / 2.0)
                ed.py_n = pos.y - (ed.sy / 2.0)
            else:
                ed.px_n = pos.x
                ed.py_n = pos.y

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

        for lvl in range(group.max_level + 1):
            c_size = self.cell_sizes[lvl]

            # THE FIX: Swept Bounding Box calculation.
            # Stretches the broad-phase box from the old position completely to the new one.
            min_px = ed.px_o if ed.px_o < ed.px_n else ed.px_n
            min_py = ed.py_o if ed.py_o < ed.py_n else ed.py_n

            max_px_o = ed.px_o + ed.sx
            max_px_n = ed.px_n + ed.sx
            max_px = max_px_o if max_px_o > max_px_n else max_px_n

            max_py_o = ed.py_o + ed.sy
            max_py_n = ed.py_n + ed.sy
            max_py = max_py_o if max_py_o > max_py_n else max_py_n

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
                    if old_keys.at(i) == new_keys[j]:
                        found = True;
                        break
                if not found:
                    self._remove_from_cell(lvl, group_id, old_keys.at(i), entity_id)

            for i in range(new_keys.size()):
                found = False
                for j in range(old_keys.size()):
                    if new_keys[i] == old_keys.at(j):
                        found = True;
                        break
                if not found:
                    self.grids[lvl][group_id][new_keys[i]].push_back(entity_id)

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

    def create_relation(self, int group_a_id, int group_b_id, object cb_a, object cb_b):
        cdef CollisionRelationStruct rel
        rel.group_a_id = group_a_id
        rel.group_b_id = group_b_id
        self.relations.push_back(rel)
        self.relation_callbacks.append((cb_a, cb_b))

    def calculate_all_collisions(self):
        self._flush_deletions()

        cdef size_t i
        for i in range(self.relations.size()):
            self._calc_relation(self.relations[i], self.relation_callbacks[i])

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

        cdef size_t a_idx, k_idx, b_idx
        cdef int b_id
        cdef bint a_resolved

        for a_idx in range(ga.entities.size()):
            ea = &ga.entities[a_idx]
            if not ea.active: continue

            a_resolved = False
            a_keys = &ea.grid_keys[check_lvl]

            for k_idx in range(a_keys.size()):
                if not ea.active or a_resolved: break

                if self.grids[check_lvl][rel.group_b_id].count(a_keys.at(k_idx)) == 0:
                    continue

                cell_b = &self.grids[check_lvl][rel.group_b_id][a_keys.at(k_idx)]

                for b_idx in range(cell_b.size()):
                    b_id = cell_b.at(b_idx)

                    if is_same and ea.id == b_id:
                        continue

                    eb = &gb.entities[b_id]
                    if not eb.active:
                        continue

                    if is_same:
                        min_id = ea.id if ea.id < b_id else b_id
                        max_id = b_id if ea.id < b_id else ea.id
                        pair_key = (<uint64_t> min_id << 32) | <uint64_t> max_id
                    else:
                        pair_key = (<uint64_t> ea.id << 32) | <uint64_t> b_id

                    if checked_pairs.count(pair_key):
                        continue
                    checked_pairs.insert(pair_key)

                    if aabb_aabb_swept(
                            ea.px_o, ea.py_o, ea.px_n, ea.py_n, ea.sx, ea.sy,
                            eb.px_o, eb.py_o, eb.px_n, eb.py_n, eb.sx, eb.sy,
                            &norm_x, &norm_y, &t
                    ):
                        inst_a = self.group_instances[rel.group_a_id][ea.id]
                        inst_b = self.group_instances[rel.group_b_id][eb.id]

                        imp_ax = ea.px_o + ((ea.px_n - ea.px_o) * t)
                        imp_ay = ea.py_o + ((ea.py_n - ea.py_o) * t)
                        imp_bx = eb.px_o + ((eb.px_n - eb.px_o) * t)
                        imp_by = eb.py_o + ((eb.py_n - eb.py_o) * t)

                        if ea.is_centered:
                            imp_ax += (ea.sx / 2.0)
                            imp_ay += (ea.sy / 2.0)
                        if eb.is_centered:
                            imp_bx += (eb.sx / 2.0)
                            imp_by += (eb.sy / 2.0)

                        if callbacks[0] is not None:
                            callbacks[0](inst_a,
                                         CollisionEvent(rel.group_b_id, inst_b, Vec2().from_cartesian(imp_ax, imp_ay),
                                                        Vec2().from_cartesian(norm_x, norm_y)))
                        if callbacks[1] is not None:
                            callbacks[1](inst_b,
                                         CollisionEvent(rel.group_a_id, inst_a, Vec2().from_cartesian(imp_bx, imp_by),
                                                        Vec2().from_cartesian(-norm_x, -norm_y)))

                        a_resolved = True
                        break

                if a_resolved:
                    break