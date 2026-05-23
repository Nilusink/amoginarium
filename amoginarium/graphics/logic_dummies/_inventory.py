"""
Inventory dummy (+UI) for logic.

| Path: amoginarium/graphics/logic_dummies/_inventory.py
| Project: amoginarium
| Created: 06.04.2026
| Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amoginarium import pv
from amoginarium.shared.utility import Vec2

from ..entities import BaseGraphicsEntity, Drawn_0
from ..render_bindings import renderer
from ..ui import AnimatedColorValues, UIRectangle
from ._synced_entities import SE_MANAGER

if TYPE_CHECKING:
    from ._synced_entities import SyncedGraphicsEntity


class Inventory(BaseGraphicsEntity):
    """inventory entity."""

    __slots__ = ["__id", "_slot_colors", "_ui"]

    def __init__(self, sync_id: int, parent: int | SyncedGraphicsEntity) -> None:
        # try to get parent by sync_id
        if isinstance(parent, int):
            parent: SyncedGraphicsEntity = SE_MANAGER.get_entity(parent)

        # init parent + remove from any groups
        super().__init__(parent)
        self.remove(Drawn_0)

        # save sync id
        self.__id = sync_id

        # create UI
        self._slot_colors = {
            "basic": AnimatedColorValues(
                (70, 70, 70),
                (150, 150, 150),
                extend_duration=0.1,
                collapse_duration=0.8,
            ),
            "border_basic": (80, 80, 80),
            "border_highlighted": (120, 120, 120),
        }

        self._ui = {
            "root": UIRectangle(
                (0.5, 0.5),
                (0.8, 0.8),
                bg_color=self._slot_colors["border_basic"],
                border_color=self._slot_colors["border_basic"],
            ),
            "slots": [
                UIRectangle(
                    (0.5, 0.5),
                    (0.1, 0.1),
                    bg_color=self._slot_colors["basic"],
                    border_color=self._slot_colors["border_basic"],
                    on_enter_callbacks=[lambda x=i: self.__slot_hover(x)],
                    on_leave_callbacks=[lambda x=i: self.__slot_unhover(x)],
                )
                for i in range(self.buff.size)
            ],
        }

        # add to parent
        self.parent.add_child(self)

    # region properties
    @property
    def buff(self):
        """The inventories SHM buffer."""
        return pv.I_BUFF[self.__id]

    @property
    def size(self) -> int:
        """Inventory slot size."""
        return self.buff.size

    # endregion

    # region internal methods
    def __slot_hover(self, slot_id: int) -> None:
        """Set hover to a slot."""
        if not (0 <= slot_id < 255):
            msg = f"slot id out of range: {slot_id}"
            raise ValueError(msg)

        self.buff.hover = slot_id

    def __slot_unhover(self, slot_id: int) -> None:
        """Reset hover (only when slot_id matches hover)."""
        if slot_id != self.buff.hover:
            return

        self.buff.hover = 255  # 255 = none

    # endregion

    # region drawing
    def draw_at(
        self,
        position: tuple[float, float],
        slots_per_row: int,
        width: float,
        delta_cal: float,
        layer: int,
    ) -> None:
        """Draw inventory at center of screen."""
        self._ui["root"].position.relative_global = position

        slot_size = width / (slots_per_row + 0.1)
        rows = round(self.buff.size / slots_per_row)

        slots: list[UIRectangle] = self._ui["slots"]  # ignore: type

        slots[0].size.relative_global = slot_size, slot_size
        slots[0].size.relative_global.y = slots[0].size.relative_global.x
        slot_size = (
            slots[0].size.absolute.x,
            slots[0].size.absolute.x,
        )

        width = slot_size[0] * (slots_per_row + 0.1)
        height = slot_size[1] * (rows + 0.1)
        size = Vec2().from_cartesian(width, height)
        self._ui["root"].size.absolute = size

        # if draw_background:
        self._ui["root"].gl_draw(force_draw=True, delta_cal=delta_cal)

        start = self._ui["root"].position.absolute_global.copy()
        start.x -= slot_size[0] * (slots_per_row / 2)
        start.y -= slot_size[1] * (rows / 2)

        for row in range(rows):
            for col in range(slots_per_row):
                slot_id = row * slots_per_row + col
                highlight = slot_id == self.buff.selected

                ui_slot = self._ui["slots"][slot_id]
                ui_slot.position.absolute_global = (
                    start.x + (0.5 + col) * slot_size[0],
                    start.y + (0.5 + row) * slot_size[0],
                )
                ui_slot.size.absolute = slot_size

                if highlight:
                    ui_slot.border_color = self._slot_colors["border_highlighted"]

                else:
                    ui_slot.border_color = self._slot_colors["border_basic"]

                ui_slot.gl_draw(force_draw=True, delta_cal=delta_cal)

                slot = self.buff.slots[slot_id]
                if slot.count > 0:
                    if slot.item_id == 0:
                        continue

                    item = SE_MANAGER.get_entity(slot.item_id)
                    if not item:
                        continue

                    texture, size = item.get_icon()

                    if texture is ...:
                        continue

                    max_size = max(size)
                    factor = (slot_size[0] * 0.8) / max_size

                    pos = ui_slot.position.absolute_global
                    pos -= ui_slot.size.absolute / 2
                    pos.x += slot_size[0] * 0.1 + (max_size - size[0]) * factor / 2
                    pos.y += slot_size[0] * 0.1 + (max_size - size[1]) * factor / 2

                    renderer.draw_textured_quad(
                        texture,
                        pos,
                        (size[0] * factor, size[1] * factor),
                        convert_global=False,
                        layer=layer,
                    )

    # endregion
