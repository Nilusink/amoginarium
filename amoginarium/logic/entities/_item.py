"""
_item.py
06.04.2026

all items should inherit from this

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
from icecream import ic
import math as m

from amoginarium.shared import base_entity_t, ProcessCommand, BaseCommandType, ItemSlot
from amoginarium.shared.utility import Vec2
from amoginarium import pv

from ._logic_groups import GravityAffected, CollisionDestroyed, Updated, WallCollider
from ._base_entity import LogicGameEntity


class Item(LogicGameEntity):
    """base item class"""

    __slots__ = ("_current_timeout",)
    _drop_timeout = 1

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        size: Vec2,
    ) -> None:
        
        # init logic entity
        super().__init__(runtime_buffer, size=size, position=Vec2())

        # set defaults
        self._current_timeout = 0

        # spawn graphics counterpart
        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={"id": self.id, "cid": self.cid()},
        ))

    def hit(self, _damage: float, hit_by=...) -> None:
        """get hit by ``player``"""
        if self._current_timeout > 0:
            return

        if hasattr(hit_by, "pickup_item"):
            hit_by.pickup_item(self)
            self._current_timeout = self._drop_timeout

    def set_parent(self, parent: LogicGameEntity) -> None:
        """assign parent to item and remove own physics"""
        self._parent = parent
        self._set_bit("flags", 15, True)
        self.remove(GravityAffected, CollisionDestroyed, Updated)
        self.hide()
        self.stop_highlight()

    def remove_parent(self, at_pos: Vec2, velocity: Vec2 | EllipsisType = ...) -> None:
        """remove parent from item and run own physics"""
        self._parent = None
        self._set_bit("flags", 15, False)
        self.acceleration *= 0
        self.velocity *= 0
        self.position = at_pos.copy()
        self.facing.angle = 0
        self._current_timeout = self._drop_timeout

        ic(at_pos, velocity)

        if velocity is not ...:
            self.velocity.x = velocity.x
            self.velocity.y = velocity.y

        self.add(GravityAffected, CollisionDestroyed, Updated)
        self.show()
        self.highlight()

    def _update(self, delta: float) -> None:
        if self.parent:
            self.position = self.parent.position
            super()._update(delta)
            return

        self._current_timeout -= delta

        # wall stuff
        if self._current_timeout <= self._drop_timeout - .1:
            res = WallCollider.collides_with(self)
            if res:
                # wall, pos = res
                self.acceleration *= 0
                self.velocity *= 0

        super()._update(delta)

        # add "floating" effect
        self._runtime_buffer[self.id].pos_y = self.position.y - (
            m.sin(self._lifetime*2) + 1
        ) * 10
