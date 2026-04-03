"""
_entity_counter.py
28.03.2026

keeps track of all entity ids

Author:
Nilusink
"""
from __future__ import annotations

from ._shared_memory import MAX_ENTITIES


class _EntityCounter:
    _instance: _EntityCounter = ...

    def __new__(cls, *args, **kwargs):
        if cls._instance is ...:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self._used_ids: set[int] = set()
        self._current_id: int = 0

    def get_id(self) -> int:
        """
        get next free entity id
        """
        start_id = self._current_id
        while True:
            if self._current_id not in self._used_ids:
                eid = self._current_id
                self._used_ids.add(eid)
                self._current_id = (self._current_id + 1) % MAX_ENTITIES
                return eid

            self._current_id = (self._current_id + 1) % MAX_ENTITIES

            if self._current_id == start_id:
                raise RuntimeError("entity limit reached")

    def pop_id(self, id: int) -> bool:
        """
        true if id was removed
        """
        if id not in self._used_ids:
            return False

        self._used_ids.remove(id)
        return True


ENTITY_COUNTER = _EntityCounter()
