"""
_entity_hints.py
12.03.2026

type hints for entities

Author:
Nilusink
"""
from __future__ import annotations
from typing import Protocol

from ..logic import Vec2
from ..shared import Coalitions
from ._island import Island


class BaseEntityLike(Protocol):
    @property
    def id(self) -> int: ...

    @property
    def parent(self) -> BaseEntityLike: ...

    @property
    def root(self) -> BaseEntityLike: ...

    @property
    def children(self) -> list[BaseEntityLike]: ...

    def update(self, delta: float) -> None: ...


class GameEntityLike(BaseEntityLike, Protocol):
    facing: Vec2
    position: Vec2
    velocity: Vec2
    acceleration: Vec2

    @property
    def position_center(self) -> Vec2: ...

    @property
    def world_position(self) -> Vec2: ...

    @property
    def is_bullet(self) -> Vec2: ...

    @property
    def coalition(self) -> Coalitions: ...

    def on_ground(self) -> bool: ...

    def kill(self, killed_by: GameEntityLike) -> None: ...


class PlayerLike(GameEntityLike, Protocol):
    @classmethod
    def load_textures(cls) -> None: ...

    @property
    def max_hp(self) -> int: ...

    @property
    def hp(self) -> float: ...

    @property
    def alive(self) -> bool: ...

    def next_weapon(self) -> None: ...

    def previous_weapon(self) -> None: ...

    def hit(self, damage: float, hit_by: GameEntityLike) -> None: ...

    def collide_wall(self, wall: Island) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]: ...

    def respawn(self, pos: Vec2 = ...) -> None: ...

