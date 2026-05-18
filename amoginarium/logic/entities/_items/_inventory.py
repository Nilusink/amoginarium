"""
Basic inventory can be used by all entities (players, chests, ...).

Path: amoginarium/logic/entities/_items/_inventory.py
Project: amoginarium
Created: 16.03.2026
Authors: Nilusink, LukasKrah
"""

import typing as tp

from amoginarium import pv
from amoginarium.shared import INVENTORY_COUNTER, ItemSlot
from amoginarium.shared.utility import Vec2

from .._base import LogicGameEntity
from ._item import Item

type item_t = Item | None


class Inventory:
    """inventory"""

    __slots__ = ("_slots", "_num_slots", "_used_slots", "_callbacks", "__id", "_parent")

    _slots: list[ItemSlot]
    _num_slots: int
    _used_slots: int
    _callbacks: dict[str, tp.Callable[[ItemSlot], None]]
    __id: int
    _parent: LogicGameEntity

    def __init__(
        self,
        parent: LogicGameEntity,
        slots: int,
        select_slot_callback: tp.Callable[[ItemSlot], None] = ...,
        unselect_slot_callback: tp.Callable[[ItemSlot], None] = ...,
    ) -> None:
        self.__id = INVENTORY_COUNTER.get_id()
        self._parent = parent

        self._num_slots = slots
        self._used_slots = 0
        self._slots = [ItemSlot(None, 0, self, i) for i in range(slots)]

        # init SHM
        self._buff.size = self._num_slots
        self._buff.hover = 255  # 255 := invalid
        self._buff.selected = 255

        self._set_flag(0, True)  # alive
        self._set_flag(1, False)  # visible

        # set all slots to 255 (invalid item)
        for i in range(slots):
            self._buff.slots[i].item_id = 0

        self._callbacks = {
            "select": select_slot_callback,
            "unselect": unselect_slot_callback,
        }

    # region flag access
    def _set_flag(self, flag_id: int, value: bool) -> None:
        """
        set (or reset) a specified flag

        :param flag_id: the flag to set
        :param value: what to set the flag to
        """
        flags = self._buff.flags

        if value:
            self._buff.flags = flags | (1 << flag_id)

        else:
            self._buff.flags = flags & ~(1 << flag_id)

    # endregion

    # region slot hover
    def _slot_hover(self, slot_id: int) -> None:
        """
        called when a slot is hovered
        """
        if self._callbacks["select"] is not ...:
            self._callbacks["select"](self.get_slot(slot_id))

    def _slot_unhover(self, slot_id: int) -> None:
        if self._callbacks["unselect"] is not ...:
            self._callbacks["unselect"](self.get_slot(slot_id))

    # endregion

    # region properties
    @property
    def slots_used(self) -> int:
        return self._used_slots

    @property
    def num_slots(self) -> int:
        return self._num_slots

    @property
    def id(self) -> int:
        return self.__id

    @property
    def _buff(self):
        return pv.I_BUFF[self.__id]

    # endregion

    # region logic interface
    def add_item(self, item: item_t, count: int = 1) -> int:
        """
        add an item to the inventory.
        :returns: -1 if fail else item id
        """
        if self.slots_used < self._num_slots:
            item_id = self.slots_used
            self.set_slot(item_id, item, count)
            return item_id

        else:
            return -1

    def try_add_item(self, item: item_t, count: int = 1) -> int:
        """
        tries to add the item to the inventory. returns -1 if fail
        """
        if self.slots_used < self._num_slots:
            for i, slot in enumerate(self._slots):
                if not slot.item:
                    new_item_id = i
                    break

            else:
                return -1

            self.set_slot(new_item_id, item, count)
            return new_item_id

        return -1

    def use_item(self, item_id: int, count: int = 1) -> bool:
        """
        :param item_id: item id
        :param count: how many to use
        :returns: True if there is more than 0 left of item
        """
        self._slots[item_id].count -= count
        self._buff.slots[item_id].count -= count
        if self._slots[item_id].count <= 0:
            return False

        return True

    def set_slot(self, slot_id: int, item: item_t, count: int = 1) -> None:
        """
        clear said slot and set it to the new item
        """
        self.clear_slot(slot_id)

        if not item:
            return

        # set new item
        self._used_slots += 1
        self._slots[slot_id].item = item
        self._slots[slot_id].count = count
        self._buff.slots[slot_id].item_id = item.id
        self._buff.slots[slot_id].count = count

        if hasattr(item, "add_used_callback"):
            item.add_used_callback(lambda c: self.use_item(slot_id, c))

        item.set_parent(self._parent)

    def drop_item(self, item_id: int, pos: Vec2, vel: Vec2 = ...) -> None:
        if not self._slots[item_id].item:
            return

        # drop item
        item = self._slots[item_id].item
        item.remove_parent(
            pos - Vec2().from_cartesian(item.size.x / 2, item.size.y), vel
        )

        # reset slot
        self.clear_slot(item_id)

    def clear_slot(self, slot_id: int) -> None:
        """
        remove item from slot
        """
        if not self._slots[slot_id].item:
            return

        self._buff.slots[slot_id].count = 0
        self._buff.slots[slot_id].item_id = 0
        self._slots[slot_id].count = 0
        self._slots[slot_id].item = None
        self._used_slots -= 1

    # endregion

    # region getters
    def get_item(self, item_id: int) -> item_t:
        return self._slots[item_id].item

    def get_count(self, item_id: int) -> int:
        return self._slots[item_id].count

    def get_slot(self, item_id: int) -> ItemSlot:
        return self._slots[item_id]

    # endregion

    # region graphics interface
    def show(self) -> None:
        """show the inventory"""
        self._set_flag(1, True)

    def hide(self) -> None:
        """hide the inventory"""
        self._set_flag(1, False)

    def set_highlight(self, slot: int) -> None:
        """set one slot to be highlighted"""
        self._buff.selected = slot

    def kill(self) -> None:
        """kill the inventory"""
        self._set_flag(0, False)

    # endregion

    def __iter__(self) -> tp.Iterable[ItemSlot]:
        return iter(self._slots)
