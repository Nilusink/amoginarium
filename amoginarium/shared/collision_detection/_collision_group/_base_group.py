"""
amoginarium/shared/collision_detection/_collision_group/_base_group.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp
from enum import Enum
import abc


class CollisionHitBox(Enum):
    point = 0
    aabb = 1


class CollisionGroupEntityData[T]:
    __slots__ = ("instance",)
    instance: T

    def __init__(self, instance: T) -> None:
        self.instance = instance


class CollisionGroup[T]:
    __slots__ = ("_entities", "_next_id")
    _hitbox_type: tp.ClassVar[CollisionHitBox]

    _entities: list[CollisionGroupEntityData[T]]
    _next_id: int

    def __init__(self) -> None:
        self._entities = []
        self._next_id = -1

    @abc.abstractmethod
    def register(self) -> int:
        ...

    @abc.abstractmethod
    def update(self) -> None:
        ...

    @property
    def entities(self) -> list[CollisionGroupEntityData[T]]:
        return self._entities

    @property
    def hitbox_type(self) -> CollisionHitBox:
        return self._hitbox_type
