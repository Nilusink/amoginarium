"""
_inventory.py
16.03.2026

basic inventory, can be used by all entities (players, chests, ...)

Author:
Nilusink
"""
from dataclasses import dataclass
from icecream import ic
import typing as tp


@dataclass
class ItemSlot:
    item: tp.Any
    count: int


class Inventory:
    __slots__ = ("_slots", "_num_slots", "_used_slots")

    def __init__(
            self,
            slots: int
    ) -> None:
        self._num_slots = slots
        self._used_slots = 0
        self._slots: list[ItemSlot] = [
            ItemSlot(None, 0) for _ in range(slots)
        ]

    @property
    def slots_used(self) -> int:
        return self._used_slots

    def add_item(self, item, count: int = 1) -> int:
        """
        add an item to the inventory.
        :returns: -1 if fail else item id
        """
        if self.slots_used < self._num_slots:
            item_id = self.slots_used
            self._slots[item_id].item = item

            if hasattr(item, "add_used_callback"):
                item.add_used_callback(
                    lambda c: self.use_item(item_id, c)
                )

            self._slots[item_id].count = count
            self._used_slots += 1
            return item_id

        else:
            return -1

    def use_item(self, item_id: int, count: int = 1) -> bool:
        """
        :param item_id: item id
        :param count: how many to use
        :returns: True if there is more than 0 left of item
        """
        self._slots[item_id].count -= count
        if self._slots[item_id].count <= 0:
            return False

        return True

    def get_item(self, item_id: int):
        return self._slots[item_id].item

    def get_count(self, item_id: int) -> int:
        return self._slots[item_id].count

    def get_slot(self, item_id: int) -> ItemSlot:
        return self._slots[item_id]

    def __iter__(self):
        return iter(self._slots)
