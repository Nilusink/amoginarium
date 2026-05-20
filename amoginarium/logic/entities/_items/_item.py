"""
All items should inherit from this.

Path: amoginarium/logic/entities/_items/_item.py
Project: amoginarium
Created: 01.04.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import math as m
import typing as tp
from types import EllipsisType

from amoginarium import pv
from amoginarium.shared import BaseCommandType, ProcessCommand
from amoginarium.shared.utility import Vec2

from .._base import GameCollisions, GravityAffected, LogicGameEntity, Updated

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.collision_detection import CollisionEvent

    from .._base import CollisionGroupIDType
    from .._player import Player
    from .._weaponry.templates import Bullet
    from .._world import Island


class Item(LogicGameEntity):
    """base item class."""

    __slots__ = ("_current_timeout",)

    # region ClassVars
    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionGroupIDType] = (
        GameCollisions.collision_group_items
    )
    _drop_timeout: tp.ClassVar[int] = 1
    # endregion
    # region InstanceVars
    _current_timeout: int  # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        size: Vec2,
        spawn_args: dict[str, tp.Any] | EllipsisType = ...,
        create_collision: bool = True,
        collision_active: bool = False,
    ) -> None:
        # init logic entity
        super().__init__(
            runtime_buffer,
            size=size,
            position=Vec2(),
            collision_active=collision_active,
        )
        if create_collision:
            self._create_collision()

        # set defaults
        self._current_timeout = 0

        # spawn graphics counterpart
        kwargs = {} if isinstance(spawn_args, EllipsisType) else spawn_args

        kwargs.update({"id": self.id, "cid": self.cid()})
        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs=kwargs,
            )
        )

    def item_pickupable(self) -> bool:
        """:return: Whether this item can be picked up"""
        return self._current_timeout <= 0

    def set_parent(self, parent: LogicGameEntity) -> None:
        """Assign parent to item and remove own physics."""
        self._change_parent(parent)
        self._set_bit("flags", 15, True)
        self.remove(GravityAffected, Updated)
        self.hide()
        self.stop_highlight()
        self._collision_active = False

    def __collision_player(self, events: list[CollisionEvent["Player"]]) -> None:
        if not self.item_pickupable():
            return

        for event in events:
            if not event.other_entity.can_pickup_item:
                continue
            event.other_entity.pickup_item(self)

    def _collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[tp.Union["Player", "Island", "Bullet"]]],
    ) -> list[bool] | None:
        """
        Distribute collision start events to different methods

        - Player: Player picks up the item if both sides agree
        - Island: Item falls to the ground and hovers over it when not in inventory

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        """

        if group_id == GameCollisions.collision_group_islands:
            events: list[CollisionEvent["Island"]]
            self.position = events[0].position
        elif group_id == GameCollisions.collision_group_players:
            events: list[CollisionEvent["Player"]]
            self.__collision_player(events)
        return None

    def remove_parent(self, at_pos: Vec2, velocity: Vec2 | EllipsisType = ...) -> None:
        """Remove parent from item and run own physics."""
        self._change_parent(None)
        self._set_bit("flags", 15, False)
        self.acceleration *= 0
        self.velocity *= 0
        self.position = at_pos.copy()
        self.facing.angle = 0
        self._current_timeout = self._drop_timeout

        if not isinstance(velocity, EllipsisType):
            self.velocity.x = velocity.x
            self.velocity.y = velocity.y

        self.add(GravityAffected, Updated)
        self.show()
        self.highlight()
        self._collision_active = True

    def _update(self, delta: float, *, keep_position: bool = False) -> None:
        if self._parent:
            if not keep_position:
                self.position = self.parent.position

            super()._update(delta)
            return

        self._current_timeout -= delta

        # wall stuff
        if GameCollisions.collision_group_islands in self._active_normals:
            if self._active_normals[GameCollisions.collision_group_islands]:
                # wall, pos = res
                self.acceleration *= 0
                self.velocity *= 0

        super()._update(delta)

        # add "floating" effect
        self._runtime_buffer[self.id].pos_y = (
            self.position.y - (m.sin(self._lifetime * 2) + 1) * 10
        )
