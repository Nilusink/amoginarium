"""
Defines a shield item that blocks projectiles and absorbs damage.

Path: amoginarium/logic/entities/_items/_shield.py
Project: amoginarium
Created: 18.04.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from amoginarium.shared import ItemCIDs
from amoginarium.shared.audio import MetalPings
from amoginarium.shared.utility import Vec2

from .. import Updated
from .._base import GameCollisions
from ._something import Something

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.audio import RandomizedEffect
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from .._base import LogicGameEntity
    from .._player import Player
    from .._weaponry import Grenade
    from .._weaponry.templates import Bullet
    from .._world import Island


class Shield(Something):
    _CID = ItemCIDs.shield

    _image_name: tp.ClassVar[tuple[str, str] | str] = ("Shield_6", "4")
    _image_size: tp.ClassVar[tuple[int, int]] = (45, 80)
    _max_uses: tp.ClassVar[int] = 200  # acts as HP for shield

    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_shields

    __slots__ = ("_in_use", "_sound")

    _in_use: bool
    _sound: RandomizedEffect

    def __init__(
        self, runtime_buffer: Array[base_entity_t], parent_position_offset: Vec2
    ) -> None:
        super().__init__(
            runtime_buffer,
            Vec2().from_cartesian(*self._image_size),
            parent_position_offset,
        )
        self._create_collision()
        # self._generate_collision_mask()

        self._sound = MetalPings().set_volume(0.4, 0.5)
        self._in_use = False
        # self._update_mask()

        self.add(Updated)

    @property
    def hp(self) -> float:
        """Hit points."""
        return self._uses_left

    @property
    def in_use(self) -> bool:
        return self._in_use

    @tp.override
    def use(self) -> None:
        """
        Start using the item.
        """
        if not self._in_use:
            self._collision_active = True
            self._in_use = True
            self.add(Updated)

    @tp.override
    def stop_use(self) -> None:
        """
        Stop using the item.
        """
        if self._in_use:
            self._collision_active = False
            self._in_use = False
            self.remove(Updated)

    @tp.override
    def remove_parent(self, at_pos: Vec2, velocity: Vec2 | EllipsisType = ...) -> None:
        super().remove_parent(
            at_pos
            - Vec2().from_cartesian(
                self._image_size[0] * 0.45, self._image_size[1] * 0.7
            ),
            velocity,
        )

    @tp.override
    def _collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[Island | Bullet | Grenade | Player]],
    ) -> list[bool] | None:
        """
        Distribute collision start events to different methods.

        - Island: Shield falls to the ground and hovers over it when not in inventory
        - Bullet: The bulleQt calls hit to avoid hitting too much when tunneling
        - AerodynamicEntity: The entity calls hit
            to avoid hitting too much when tunneling
        - Grenade: Grenades bounce back from shields. No reaction to the shield
        - Player: Players collect the shield if they have no parent

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        """
        if (
            group_id == GameCollisions.collision_group_islands
            or group_id == GameCollisions.collision_group_players
            or group_id == GameCollisions.collision_group_bullets
        ):
            events: list[CollisionEvent[Island | Player | Bullet]]
            super()._collision_start(group_id, events)

    @tp.override
    def _update_collision(  # type: ignore
        self,
        *,
        position: Vec2 | EllipsisType = ...,
        size: Vec2 | EllipsisType = ...,
        rotation: float = 0.0,
        positions: list[Vec2] | None = None,
        centered: bool | EllipsisType = ...,
        radius: float | None = None,
        collision_active: bool | EllipsisType = ...,
        shift_history: bool = True,
    ) -> None:
        super()._update_collision(
            position=self.position + self.size / 2,
            size=size,
            rotation=self.facing.angle,
            positions=positions,
            centered=True,
            radius=radius,
            collision_active=collision_active,
            shift_history=shift_history,
        )

    @tp.override
    def item_pickupable(self) -> bool:
        return self._parent is None and super().item_pickupable()

    def hit(self, damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        if not self._in_use:
            super().hit(damage, hit_by)

        if not isinstance(hit_by, EllipsisType) and "bullet" in hit_by._tags:
            self._sound.play(pos=self.position)

        self._uses_left -= damage

        if self._uses_left <= 0:
            self.kill(killed_by=hit_by)

    @tp.override
    def _update(self, delta: float, **_) -> None:
        if self.parent:
            d = Vec2().from_polar(
                self.facing.angle, self._parent_position_offset.length
            )
            if self._in_use:
                self.size.xy = self._image_size
                self.position = self.parent.position + d - self.size / 2

            else:
                self.size.xy = self._image_size[0] * 0.1, self._image_size[1] * 0.3
                self.position = self.parent.position

            self.velocity *= 0
            self.acceleration *= 0
            self._velocity_to_add *= 0
            self._acceleration_to_add *= 0

            super()._update(delta, keep_position=True)
            return

        self.size.xy = self._image_size

        super()._update(delta)
