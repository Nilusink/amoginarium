"""
Keeps track of all entity ids.

Path: amoginarium/shared/_entity_counter.py
Project: amoginarium
Created: 28.03.2026
Authors: Nilusink
"""

from __future__ import annotations

from icecream import ic

from ._shared_memory import MAX_ENTITIES, MAX_INVENTORIES


class _EntityCounter:
    def __init__(self, size: int) -> None:
        self._used_ids: set[int] = set()
        self._current_id: int = 0
        self._size = size

    def get_id(self) -> int:
        """
        Get next free entity id.
        """
        start_id = self._current_id
        while True:
            if self._current_id not in self._used_ids:
                eid = self._current_id
                self._used_ids.add(eid)
                self._current_id = (self._current_id + 1) % self._size
                return eid

            self._current_id = (self._current_id + 1) % self._size

            if self._current_id == start_id:
                # ic(start_id, self._current_id, len(self._used_ids), self._size, self._used_ids)
                msg = "entity limit reached"
                raise RuntimeError(msg)

    def pop_id(self, id: int) -> bool:
        """
        True if id was removed.
        """
        if id not in self._used_ids:
            return False

        self._used_ids.remove(id)
        return True

    def reset(self) -> None:
        """Reset the counter."""
        self._used_ids.clear()
        self._current_id = 0


ENTITY_COUNTER = _EntityCounter(MAX_ENTITIES)
INVENTORY_COUNTER = _EntityCounter(MAX_INVENTORIES)
