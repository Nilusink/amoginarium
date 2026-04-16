"""
amoginarium/shared/collision_detection/_collision_group/_aabb_group.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.utility import Vec2, convert_coord, coord_t
from amoginarium.shared.debugging import cum_timer

from ._base_group import CollisionGroup, CollisionGroupEntityData, CollisionHitBox


class CollisionGroupAABBEntityData[T](CollisionGroupEntityData):
    # Notice "instance" is inherited from the base class, no need to repeat it in slots
    __slots__ = ("position_old", "position_new", "size_old", "size_new", "cell_tracker")

    position_old: tp.Final[Vec2]
    position_new: tp.Final[Vec2]
    size_old: tp.Final[Vec2]
    size_new: tp.Final[Vec2]
    cell_tracker: dict[int, int]  # Maps packed_cell_key -> index_in_cell

    def __init__(
            self,
            instance: T,
            *,
            position: coord_t = (0, 0),
            size: coord_t = (0, 0),
    ) -> None:
        super().__init__(instance=instance)
        position_tuple = convert_coord(position)
        size_tuple = convert_coord(size)

        self.position_old = Vec2().from_cartesian(position_tuple[0], position_tuple[1])
        self.position_new = Vec2().from_cartesian(position_tuple[0], position_tuple[1])
        self.size_old = Vec2().from_cartesian(size_tuple[0], size_tuple[1])
        self.size_new = Vec2().from_cartesian(size_tuple[0], size_tuple[1])

        # Initialize the high-speed spatial footprint tracker
        self.cell_tracker = {}


class CollisionGroupAABB[T](CollisionGroup):
    __slots__ = ("_grid", "_cell_size") # _entities and _next_id are inherited
    _hitbox_type = CollisionHitBox.aabb
    _entities: list[CollisionGroupAABBEntityData[T]]

    def __init__(self, cell_size: int = 200) -> None:
        super().__init__()
        self._cell_size = cell_size
        self._grid: dict[int, list[int]] = {}

    @cum_timer.time_this
    def register(
            self,
            instance: T,
            *,
            position: coord_t | None = None,
            size: coord_t | None = None,
    ) -> int:
        self._entities.append(
            CollisionGroupAABBEntityData[T](
                instance=instance,
                position=position,
                size=size
            )
        )

        self._next_id += 1

        # Insert the newly registered entity into the spatial grid
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
        # Array index lookup in C - the fastest possible lookup in Python
        entity = self._entities[entity_id]

        grid_needs_update = False

        if position is not None:
            pos_old = entity.position_old
            pos_new = entity.position_new

            # Inline transfer - avoids method calls
            pos_old.x = pos_new.x
            pos_old.y = pos_new.y

            # Type-check inline to avoid convert_coord overhead
            if type(position) is tuple or type(position) is list:
                pos_new.x, pos_new.y = position
            else:
                pos_new.x = position.x
                pos_new.y = position.y

            grid_needs_update = True

        if size is not None:
            size_old = entity.size_old
            size_new = entity.size_new

            size_old.x = size_new.x
            size_old.y = size_new.y

            if type(size) is tuple or type(size) is list:
                size_new.x, size_new.y = size
            else:
                size_new.x = size.x
                size_new.y = size.y

            grid_needs_update = True

        # Synchronize the dynamic grid only if coordinates changed
        if grid_needs_update:
            self.update_grid_position(entity_id)

    def update_grid_position(self, entity_id: int) -> None:
        entity = self._entities[entity_id]

        # 1. Calculate Grid Boundaries for the AABB
        min_cx = int(entity.position_new.x) // self._cell_size
        min_cy = int(entity.position_new.y) // self._cell_size
        max_cx = int(entity.position_new.x + entity.size_new.x) // self._cell_size
        max_cy = int(entity.position_new.y + entity.size_new.y) // self._cell_size

        # 2. Generate the keys for every cell this AABB currently touches
        new_keys = []
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                new_keys.append((cx << 32) | (cy & 0xFFFFFFFF))

        tracker = entity.cell_tracker

        # 3. O(1) REMOVAL: Find cells we just left
        keys_to_remove = [k for k in tracker if k not in new_keys]

        for old_key in keys_to_remove:
            idx = tracker[old_key]
            cell_list = self._grid[old_key]
            last_entity_id = cell_list[-1]

            # Swap the moving entity with the last entity in this cell's list
            cell_list[idx] = last_entity_id

            # Update the tracker of the entity we just moved
            self._entities[last_entity_id].cell_tracker[old_key] = idx

            # Pop our moving entity off the end instantly
            cell_list.pop()

            # Remove it from our moving entity's tracker
            del tracker[old_key]

            # Memory cleanup: drop empty cells from the world
            if not cell_list:
                del self._grid[old_key]

        # 4. O(1) INSERTION: Find new cells we just entered
        for new_key in new_keys:
            if new_key not in tracker:
                if new_key not in self._grid:
                    self._grid[new_key] = []

                cell_list = self._grid[new_key]

                # Record our index and append instantly
                tracker[new_key] = len(cell_list)
                cell_list.append(entity_id)

    @property
    def grid(self) -> dict[int, list[int]]:
        """Grants the collision manager raw access to the grid dictionary."""
        return self._grid
