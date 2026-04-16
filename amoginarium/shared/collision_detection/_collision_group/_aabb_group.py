"""
amoginarium/shared/collision_detection/_collision_group/_aabb_group.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp
import array

from amoginarium.shared.utility import convert_coord, coord_t
from amoginarium.shared.debugging import cum_timer

from ._base_group import CollisionGroup, CollisionGroupEntityData, CollisionHitBox


class CollisionGroupAABBEntityData[T](CollisionGroupEntityData):
    __slots__ = ("cell_tracker",)
    cell_tracker: dict[int, int]

    def __init__(self, instance: T) -> None:
        super().__init__(instance=instance)
        self.cell_tracker = {}


class CollisionGroupAABB[T](CollisionGroup):
    __slots__ = (
        "_grid", "_cell_size",
        "pos_old_x", "pos_old_y", "pos_new_x", "pos_new_y", "size_x", "size_y"
    )
    _hitbox_type = CollisionHitBox.aabb
    _entities: list[CollisionGroupAABBEntityData[T]]

    # Expose raw memory arrays for Cython
    pos_old_x: array.array
    pos_old_y: array.array
    pos_new_x: array.array
    pos_new_y: array.array
    size_x: array.array
    size_y: array.array

    def __init__(self, cell_size: int = 10) -> None:
        super().__init__()
        self._cell_size = cell_size
        self._grid: dict[int, list[int]] = {}

        # 'd' = double precision float (C double)
        self.pos_old_x = array.array('d')
        self.pos_old_y = array.array('d')
        self.pos_new_x = array.array('d')
        self.pos_new_y = array.array('d')
        self.size_x = array.array('d')
        self.size_y = array.array('d')

    @cum_timer.time_this
    def register(
            self,
            instance: T,
            *,
            position: coord_t = (0, 0),
            size: coord_t = (0, 0),
    ) -> int:
        self._entities.append(CollisionGroupAABBEntityData[T](instance=instance))
        self._next_id += 1

        p_x, p_y = convert_coord(position)
        s_x, s_y = convert_coord(size)

        self.pos_old_x.append(p_x)
        self.pos_old_y.append(p_y)
        self.pos_new_x.append(p_x)
        self.pos_new_y.append(p_y)
        self.size_x.append(s_x)
        self.size_y.append(s_y)

        self.update_grid_position(self._next_id)
        return self._next_id

    @cum_timer.time_this
    def update(
            self,
            entity_id: int,
            *,
            position: coord_t | None = None,
            size: coord_t | None = None
    ) -> None:
        grid_needs_update = False

        if position is not None:
            # Shift old frame data directly in memory
            self.pos_old_x[entity_id] = self.pos_new_x[entity_id]
            self.pos_old_y[entity_id] = self.pos_new_y[entity_id]

            p_x, p_y = convert_coord(position)
            self.pos_new_x[entity_id] = p_x
            self.pos_new_y[entity_id] = p_y
            grid_needs_update = True

        if size is not None:
            s_x, s_y = convert_coord(size)
            self.size_x[entity_id] = s_x
            self.size_y[entity_id] = s_y
            grid_needs_update = True

        if grid_needs_update:
            self.update_grid_position(entity_id)

    def update_grid_position(self, entity_id: int) -> None:
        entity = self._entities[entity_id]

        new_x = self.pos_new_x[entity_id]
        new_y = self.pos_new_y[entity_id]
        sx = self.size_x[entity_id]
        sy = self.size_y[entity_id]

        min_cx = int(new_x) // self._cell_size
        min_cy = int(new_y) // self._cell_size
        max_cx = int(new_x + sx) // self._cell_size
        max_cy = int(new_y + sy) // self._cell_size

        new_keys = []
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                new_keys.append((cx << 32) | (cy & 0xFFFFFFFF))

        tracker = entity.cell_tracker

        keys_to_remove = [k for k in tracker if k not in new_keys]
        for old_key in keys_to_remove:
            idx = tracker[old_key]
            cell_list = self._grid[old_key]
            last_entity_id = cell_list[-1]

            cell_list[idx] = last_entity_id
            self._entities[last_entity_id].cell_tracker[old_key] = idx
            cell_list.pop()
            del tracker[old_key]

            if not cell_list:
                del self._grid[old_key]

        for new_key in new_keys:
            if new_key not in tracker:
                if new_key not in self._grid:
                    self._grid[new_key] = []

                cell_list = self._grid[new_key]
                tracker[new_key] = len(cell_list)
                cell_list.append(entity_id)

    @property
    def grid(self) -> dict[int, list[int]]:
        return self._grid