"""
_entity_hints.py
12.03.2026

type hints for entities

Author:
Nilusink
"""
from __future__ import annotations
from typing import Protocol
import pygame as pg

from amoginarium.logic import Vec2
from amoginarium.shared import Coalitions


class HasPosition(Protocol):
    position: Vec2


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
    def is_bullet(self) -> bool: ...

    @property
    def coalition(self) -> Coalitions: ...

    def on_ground(self) -> bool: ...

    def kill(self, killed_by: GameEntityLike) -> None: ...


class IslandLike(GameEntityLike, Protocol):
    @classmethod
    def load_textures(cls) -> None: ...

    @classmethod
    def random_between(
            cls,
            x_start: int,
            x_end: int,
            y_start: int,
            y_end: int,
            x_size_start: int,
            x_size_end: int,
            y_size_start: int,
            y_size_end: int
    ) -> IslandLike: ...

    @classmethod
    def _get_block_mask(cls) -> pg.Mask | tuple[pg.Mask, pg.Mask]: ...

    def _generate_collision_mask(self) -> None: ...

    def collide(self, other) -> tuple[int, int] | None: ...

    def player_contact(self, player, delta: float) -> None: ...

    def get_collided_sides(
            self,
            top_collider: tuple[Vec2, pg.Mask],
            right_collider: tuple[Vec2, pg.Mask],
            bottom_collider: tuple[Vec2, pg.Mask],
            left_collider: tuple[Vec2, pg.Mask],
    ) -> tuple[
        tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]
    ]: ...


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

    def heal(self, heal: float) -> bool: ...

    # def collide_wall(self, wall: IslandLike) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]: ...

    def respawn(self, pos: Vec2 = ...) -> None: ...

