"""
amoginarium/shared/collision_detection/_collision_group/_circle_group.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""
from __future__ import annotations

import typing as tp

from amoginarium.shared.utility import Vec2, convert_coord, coord_t

from ._base_group import CollisionGroup, CollisionGroupEntityData, CollisionHitBox


class CollisionGroupCircleEntityData[T](CollisionGroupEntityData):
    __slots__ = ("instance", "position_old", "position_new", "radius_old", "radius_new")
    position_old: tp.Final[Vec2]
    position_new: tp.Final[Vec2]
    radius_old: float
    radius_new: float

    def __init__(
            self,
            instance: T,
            *,
            position: coord_t | None = None,
            radius: float = 0.0,
    ) -> None:
        super().__init__(instance=instance)
        self.position_old = Vec2()
        self.position_new = Vec2()
        self.radius_old = radius
        self.radius_new = radius

        if position is not None:
            self.position_old.xy = convert_coord(position)
            self.position_new.xy = self.position_old.xy



class CollisionGroupCircle[T](CollisionGroup):
    _hitbox_type = CollisionHitBox.circle
    _entities: dict[int, CollisionGroupCircleEntityData[T]]

    def register(
            self,
            instance: T,
            *,
            position: coord_t | None = None,
            radius: float = 0.0,
    ) -> int:
        self._entities[self._next_id] = CollisionGroupCircleEntityData[T](
            instance=instance,
            position=position,
            radius=radius
        )
        return super().register()

    def update(
            self,
            entity_id: int,
            *,
            position: coord_t | None = None,
            radius: float | None = None
    ) -> None:
        entity = self._entities[entity_id]

        if position is not None:
            entity.position_old.xy = entity.position_new.xy
            entity.position_new.xy = convert_coord(position)

        if radius is not None:
            entity.radius_old = entity.radius_new
            entity.radius_new = radius
