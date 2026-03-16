"""
_inventory.py
16.03.2026

basic inventory, can be used by all entities (players, chests, ...)

Author:
Nilusink
"""
from dataclasses import dataclass
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

    def add_item(self, item, count: int = 1) -> bool:
        """
        add an item to the inventory.
        :returns: if the item has been successfully added
        """
        if self.slots_used < self._num_slots:
            self._slots[self.slots_used].item = item
            self._slots[self.slots_used].count = count
            self._used_slots += 1
            return True

        else:
            return False

    def get_item(self, item_id: int):
        return self._slots[item_id].item

    def get_count(self, item_id: int) -> int:
        return self._slots[item_id].count

    def get_slot(self, item_id: int) -> ItemSlot:
        return self._slots[item_id]
