"""
Different type of fuzes.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/fuzes/
            _fuzes.py
| ``Project``: amoginarium
| ``Created``: 08.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

from icecream import ic

from amoginarium.shared.utility import Vec2

from ....._base import GameCollisions
from ._base import BaseFuze

if tp.TYPE_CHECKING:
    from types import EllipsisType

    from amoginarium.shared import MurderViable
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionExceptionIDType
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from ..._bullets import Bullet


class TTLFuze(BaseFuze):
    """Detonates after a mult*ttl."""

    __slots__ = ("_ttl",)

    _ttl: float

    def __init__(
        self,
        parent: Bullet,
        ttl: float,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create TTL Fuze.

        :param parent: Parent bullet
        :param ttl: Time to live after the fuze triggers
        :param offset: Offset relative to bullet
        :param function_delay: Delays actors function
        """
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._ttl = ttl

    @tp.override
    def _update(self) -> None:
        """Update the ttl fuze."""
        # update position
        super()._update()

        # update fuze
        if self._parent.lifetime >= self._ttl:
            self._parent.kill(killed_by=self)


class TTLMultFuze(TTLFuze):
    """Multiplies the ttl."""

    __slots__ = ()

    def __init__(
        self,
        parent: Bullet,
        ttl: float,
        mult: float,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create Multiplied TTL Fuze.

        :param parent: Parent bullet
        :param ttl: Time to live after the fuze triggers
        :param mult: Multiplier for the ttl
        :param offset: Offset relative to bullet
        :param function_delay: Delays actors function
        """
        super().__init__(
            parent, ttl=ttl * mult, offset=offset, function_delay=function_delay
        )


class PositionFuze(BaseFuze):
    """Fuzes based specified target position (static)."""

    __slots__ = ("_target_position", "_distance")

    _target_position: Vec2
    _distance: float

    def __init__(
        self,
        parent: Bullet,
        position: Vec2,
        distance: float,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create Position Fuze.

        :param parent: Parent bullet
        :param position: Trigger target position
        :param distance: From which distance from position this fuze triggers
        :param offset: Offset relative to bullet
        :param function_delay: Delays actors function
        """
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._target_position = position
        self._distance = distance

        if self._dbe:
            self._dbe.radius = self._distance

    @tp.override
    def _update(self) -> None:
        """Update the position fuze."""
        # update position
        super()._update()

        # check fuze
        if (self._position - self._target_position).length <= self._distance:
            self._parent.kill(killed_by=self)


class ProximityFuze(BaseFuze):
    """Fuzed if anything comes closer to fuze than a specified distance."""

    __slots__ = (
        "_collision_exception_id",
        "_collision_groups",
        "_entities",
        "_distance",
    )

    _collision_exception_id: CollisionExceptionIDType
    _collision_groups: list[CollisionGroupIDType]
    _entities: list[CollisionEvent]
    _distance: float

    def __init__(
        self,
        parent: Bullet,
        distance: float,
        collision_exception_id: CollisionExceptionIDType,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create a proximity fuze.

        :param parent: Parent bullet
        :param distance: Trigger distance
        :param collision_exception_id: Collision exception ID so the entity that
            holds the trigger does not trigger the fuze
        :param offset: Offset relative to bullet
        :param function_delay: Delays actors function
        """
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._collision_exception_id = collision_exception_id
        self._collision_groups = [
            GameCollisions.collision_group_turrets,
            GameCollisions.collision_group_players,
            GameCollisions.collision_group_islands,
            GameCollisions.collision_group_shields,
        ]
        self._distance = distance

        if self._dbe:
            self._dbe.radius = self._distance

        self._entities = []
        GameCollisions.add_extra_calculate_callback(self.__calculate_collisions)

    def __calculate_collisions(self) -> None:
        """Calculate if any entities in self._collision_groups are within proximity."""
        self._entities: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                self._collision_groups,
                self._last_pos,
                self._position,
                centered=True,
                hitbox_type="circle",
                radius=self._distance,
                ignore_collisions=self._collision_exception_id,
            )
        )

    @tp.override
    def _update(self) -> None:
        """Update the proximity fuze."""
        # update position
        super()._update()

        if self._entities:
            self._parent.kill(killed_by=self)

    @tp.override
    def kill(self, killed_by: MurderViable | EllipsisType) -> None:
        """
        Kills this proximity fuze.

        :param killed_by: Who killed this fuze
        """
        GameCollisions.remove_extra_calculate_callback(self.__calculate_collisions)

        super().kill(killed_by=killed_by)


class AltitudeFuze(BaseFuze):
    """
    Fuzes if height below fuze is less than x (must be above x first to arm).

    Height is defined as distance above an island
    """

    __slots__ = (
        "_fuze_height",
        "_armed",
        "_collision_exception_id",
        "_entities",
    )

    _fuze_height: float
    _armed: bool
    _collision_exception_id: CollisionExceptionIDType
    _entities: list[CollisionEvent]

    def __init__(
        self,
        parent: Bullet,
        height: float,
        collision_exception_id: int,
        *,
        offset: Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create altitude-triggered fuze.

        :param parent: Parent bullet
        :param height: Height under which to trigger the fuze
        :param collision_exception_id: Collision exception ID so the entity that
            holds the trigger does not trigger the fuze
        :param offset: Offset relative to bullet
        :param function_delay: Delays actors function
        """
        super().__init__(parent, offset=offset, function_delay=function_delay)

        self._fuze_height = height
        self._armed = False
        self._collision_exception_id = collision_exception_id

        self._entities = []

        ic("alt")

        GameCollisions.add_extra_calculate_callback(self.__calc_collision_with_islands)

    def __calc_collision_with_islands(self) -> None:
        """Calculate if the fuze has any island in the distance below it."""
        self._entities: list[CollisionEvent] = (
            GameCollisions.collision_manager.manual_collision(
                [GameCollisions.collision_group_islands],
                self._position,
                self._position + Vec2().from_cartesian(0, self._fuze_height),
                ignore_collisions=self._collision_exception_id,
            )
        )

    @tp.override
    def _update(self) -> None:
        """Update the altitude fuze."""
        # update position
        super()._update()

        # update fuze
        if self._armed:
            if self._entities:
                diff = self._position - self._last_pos

                # only explode on decent
                if diff.y > 0:
                    self._parent.kill(killed_by=self)

        elif not self._entities:
            self._armed = True

    @tp.override
    def kill(self, killed_by: MurderViable | EllipsisType) -> None:
        """
        Kills the altitude fuze.

        :param killed_by: Who killed this fuze
        """
        GameCollisions.remove_extra_calculate_callback(
            self.__calc_collision_with_islands
        )
        super().kill(killed_by=killed_by)


FUZES: tp.Final[dict[str, type[BaseFuze]]] = {
    "ttl": TTLFuze,
    "ttl_mult": TTLMultFuze,
    "distance": PositionFuze,
    "proximity": ProximityFuze,
    "alt": AltitudeFuze,
}
