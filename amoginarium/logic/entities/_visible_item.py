"""
_visible_item.py
01.04.2026

Wrapper for items that tells them where to render

Author:
Nilusink
"""
from ctypes import Array
from icecream import ic

from amoginarium.shared import base_entity_t, ItemSlot
from amoginarium.shared.utility import Vec2

from ._logic_groups import GravityAffected, CollisionDestroyed, Updated
from ._logic_groups import WallCollider
from ._base_entity import LogicGameEntity


class VisibleItem(LogicGameEntity):
    # _parent: ItemSlot
    _drop_timeout = 1

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            item#: ItemLike | WeaponLike
    ) -> None:
        self._item = item
        self._visible = False
        self._runtime_buffer = runtime_buffer
        self.size = Vec2()  #item._size.copy()
        self._current_timeout = 0
        super().__init__(runtime_buffer, size=self.size, position=Vec2())
        self.remove(GravityAffected, CollisionDestroyed, Updated)

    @property
    def parent(self) -> ItemSlot | None:
        if self._parent is ...:
            return None

        return self._parent

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def item(self):
        return self._item

    def hide(self) -> None:
        if self._visible:
            self._visible = False
            self._runtime_buffer[self.id].param0 = False

    def show(self) -> None:
        if not self._visible:
            self._visible = True
            self._runtime_buffer[self.id].param0 = True

    def hit(self, damage: float, hit_by=...) -> None:
        if self._current_timeout > 0:
            return

        if hasattr(hit_by, "pickup_item"):
            hit_by.pickup_item(self)
            self._current_timeout = self._drop_timeout

    def set_parent(self, parent: ItemSlot) -> None:
        self._parent = parent
        self.remove(GravityAffected, CollisionDestroyed, Updated)
        self.hide()

    def remove_parent(self, at_pos: Vec2, velocity: Vec2 = ...) -> None:
        self._parent = ...
        self.acceleration *= 0
        self.velocity *= 0
        self.position = at_pos.copy()
        self._current_timeout = self._drop_timeout

        ic(at_pos, velocity)

        if velocity is not ...:
            self.velocity.x = velocity.x
            self.velocity.y = velocity.y

        self.add(GravityAffected, CollisionDestroyed, Updated)
        self.show()

    def _update(self, delta: float) -> None:
        if self.parent:
            return

        self._current_timeout -= delta

        # wall stuff
        if self._current_timeout <= self._drop_timeout - .1:
            res = WallCollider.collides_with(self)
            if res:
                # wall, pos = res
                self.acceleration *= 0
                self.velocity *= 0

        super().update(delta)
