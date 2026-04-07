"""
_logic_entity_hints.py
28.03.2026

type hints for logic entities

Author:
Nilusink
"""
from __future__ import annotations
from multiprocessing.shared_memory import SharedMemory
from typing import Protocol, Self


class BaseLogicEntityLike(Protocol):
    __slots__ = ["_parent", "_children", "_lifetime", "__id", "__shm"]

    _children: list[Self]
    _lifetime: float
    _parent: Self

    def __init__(
            self,
            id: int,
            shm: SharedMemory,
            parent: Self | None = None,
    ) -> None: ...

    @property
    def id(self) -> int: ...
    @property
    def parent(self) -> Self | None: ...
    @property
    def root(self) -> Self: ...
    @property
    def children(self) -> list[Self]: ...

    def _update(self, delta: float) -> None: ...
    def update(self, delta: float) -> None: ...
