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

    def get_id(self) -> int:
        for i in range(MAX_ENTITIES):
            if i not in self._used_ids:
                self._used_ids.add(i)
                return i

        else:
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
