"""
Different type of fuzes.

| Path: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/fuzes/_fuzes.py
| Project: amoginarium
| Created: 08.05.2026
| Authors: Nilusink
"""

from __future__ import annotations

import typing as tp

from icecream import ic

from amoginarium.shared.utility import Vec2

from ....._base import GameCollisions
from ._base import BaseFuze

if tp.TYPE_CHECKING:
    from types import EllipsisType

    from amoginarium.shared.collision_detection import CollisionEvent

    from ..._bullets import Bullet


class TTLFuze(BaseFuze):
    """detonates after a mult*ttl."""

    def __init__(
        self,
        parent: Bullet,
        ttl: float,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._ttl = ttl

    def _update(self) -> None:
        # update position
        super()._update()

        # update fuze
        if self._parent.lifetime >= self._ttl:
            self._parent.kill(killed_by=self)


class TTLMultFuze(TTLFuze):
    """multiplies the ttl."""

    def __init__(
        self,
        parent: Bullet,
        ttl: float,
        mult: float,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        super().__init__(
            parent, ttl=ttl * mult, offset=offset, function_delay=function_delay
        )


class PositionFuze(BaseFuze):
    """fuzes based specified target position (static)."""

    def __init__(
        self,
        parent: Bullet,
        position: Vec2,
        distance: float,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._target_position = position
        self._distance = distance

        if self._dbe:
            self._dbe.radius = self._distance

    def _update(self) -> None:
        # update position
        super()._update()

        # check fuze
        if (self._position - self._target_position).length <= self._distance:
            self._parent.kill(killed_by=self)


class ProximityFuze(BaseFuze):
    """fuzed if anything comes closer to fuze than a specified distance."""

    def __init__(
        self,
        parent: Bullet,
        distance: float,
        collision_exception_id: int,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._ceid = collision_exception_id
        self._collision_groups = [
            GameCollisions.collision_group_turrets,
            GameCollisions.collision_group_players,
            GameCollisions.collision_group_islands,
            GameCollisions.collision_group_shields,
        ]
        self._distance = distance

        if self._dbe:
            self._dbe.radius = self._distance

    def _update(self) -> None:
        # update position
        super()._update()

        # check fuze
        entities: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                self._collision_groups,
                self._last_pos,
                self._position,
                centered=True,
                hitbox_type="circle",
                radius=self._distance,
                ignore_collisions=self._ceid,
            )
        )

        if entities:
            self._parent.kill(killed_by=self)


class AltitudeFuze(BaseFuze):
    """fuzes if height below fuze is less than x (must be above x first to arm)."""

    def __init__(
        self,
        parent: Bullet,
        height: float,
        collision_exception_id: int,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._fuze_height = height
        self._armed = False
        self._ceid = collision_exception_id

        ic("alt")

    def _update(self) -> None:
        # update position
        super()._update()

        # update fuze
        entities: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                [GameCollisions.collision_group_islands],
                self._position,
                self._position + Vec2().from_cartesian(0, self._fuze_height),
                ignore_collisions=self._ceid,
            )
        )

        if self._armed:
            if entities:
                diff = self._position - self._last_pos

                # only explode on decent
                if diff.y > 0:
                    self._parent.kill(killed_by=self)

        elif not entities:
            self._armed = True
