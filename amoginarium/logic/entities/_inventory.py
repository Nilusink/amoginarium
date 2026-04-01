"""
_inventory.py
16.03.2026

basic inventory, can be used by all entities (players, chests, ...)

Author:
Nilusink
"""
import typing as tp

from amoginarium.shared.utility import Vec2
from amoginarium.shared import ItemSlot

from ._visible_item import VisibleItem

type item_t = VisibleItem | None


class Inventory:
    __slots__ = (
        "_slots",
        "_num_slots",
        "_used_slots",
        "_ui",
        "_slot_colors",
        "_callbacks"
    )

    def __init__(
            self,
            slots: int,
            select_slot_callback: tp.Callable[[ItemSlot], None] = ...,
            unselect_slot_callback: tp.Callable[[ItemSlot], None] = ...,
    ) -> None:
        self._num_slots = slots
        self._used_slots = 0
        self._slots: list[ItemSlot] = [
            ItemSlot(None, 0, self, i) for i in range(slots)
        ]

        self._callbacks = {
            "select": select_slot_callback,
            "unselect": unselect_slot_callback
        }

        # self._slot_colors = {
        #     "basic": AnimatedColorValues(
        #         (70, 70, 70),
        #         (150, 150, 150),
        #         extend_duration=.1,
        #         collapse_duration=.8
        #     ),
        #     "border_basic": (80, 80, 80),
        #     "border_highlighted": (120, 120, 120)
        # }
        #
        # self._ui = {
        #     "root": Rectangle(
        #         (.5, .5),
        #         (.8, .8),
        #         bg_color=self._slot_colors["border_basic"],
        #         border_color=self._slot_colors["border_basic"]
        #     ), "slots": [
        #         Rectangle(
        #             (.5, .5),
        #             (.1, .1),
        #             bg_color=self._slot_colors["basic"],
        #             border_color=self._slot_colors["border_basic"],
        #             on_enter_callbacks=[lambda x=i: self._slot_hover(x)],
        #             on_leave_callbacks=[lambda x=i: self._slot_unhover(x)]
        #         ) for i in range(slots)
        #         ]
        # }

    def _slot_hover(self, slot_id: int) -> None:
        """
        called when a slot is hovered
        """
        if self._callbacks["select"] is not ...:
            self._callbacks["select"](self.get_slot(slot_id))

    def _slot_unhover(self, slot_id: int) -> None:
        if self._callbacks["unselect"] is not ...:
            self._callbacks["unselect"](self.get_slot(slot_id))

    @property
    def slots_used(self) -> int:
        return self._used_slots

    @property
    def num_slots(self) -> int:
        return self._num_slots

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
        if hasattr(item, "add_used_callback"):
            item.add_used_callback(
                lambda c: self.use_item(slot_id, c)
            )

        item.set_parent(self._slots[slot_id])

    def drop_item(self, item_id: int, pos: Vec2, vel: Vec2 = ...) -> None:
        if not self._slots[item_id].item:
            return

        # drop item
        item = self._slots[item_id].item
        item.remove_parent(pos, vel)

        # reset slot
        self.clear_slot(item_id)

    def clear_slot(self,  slot_id: int) -> None:
        """
        remove item from slot
        """
        if not self._slots[slot_id].item:
            return

        self._slots[slot_id].count = 0
        self._slots[slot_id].item = None
        self._used_slots -= 1

    def get_item(self, item_id: int) -> item_t:
        return self._slots[item_id].item

    def get_count(self, item_id: int) -> int:
        return self._slots[item_id].count

    def get_slot(self, item_id: int) -> ItemSlot:
        return self._slots[item_id]

    def __iter__(self) -> tp.Iterable[ItemSlot]:
        return iter(self._slots)
