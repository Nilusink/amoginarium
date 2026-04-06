"""
_inventory.py
06.04.2026

Inventory dummy (+UI) for logic

Author:
Nilusink
"""
from icecream import ic

from amoginarium.shared.utility import Vec2
from amoginarium import pv

from ..entities import BaseGraphicsEntity, Drawn_0
from ..ui import Rectangle, AnimatedColorValues
from ..render_bindings import renderer
from ._synced_entities import SyncedGraphicsEntity, SE_MANAGER
from ._drawable_items import ITEM_IDS


class Inventory(BaseGraphicsEntity):
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
                extend_duration=.1,
                collapse_duration=.8
            ),
            "border_basic": (80, 80, 80),
            "border_highlighted": (120, 120, 120)
        }

        self._ui = {
            "root": Rectangle(
                (.5, .5),
                (.8, .8),
                bg_color=self._slot_colors["border_basic"],
                border_color=self._slot_colors["border_basic"]
            ), "slots": [
                Rectangle(
                    (.5, .5),
                    (.1, .1),
                    bg_color=self._slot_colors["basic"],
                    border_color=self._slot_colors["border_basic"],
                    on_enter_callbacks=[lambda x=i: self.__slot_hover(x)],
                    on_leave_callbacks=[lambda x=i: self.__slot_unhover(x)]
                ) for i in range(self._buff.size)
                ]
        }

        # add to parent
        self.parent.add_child(self)

    # region properties
    @property
    def _buff(self):
        return pv.I_BUFF[self.__id]

    @property
    def size(self) -> int:
        return self._buff.size

    # endregion

    # region internal methods
    def __slot_hover(self, slot_id: int) -> None:
        """set hover to a slot"""
        if not (0 < slot_id < 255):
            raise ValueError(f"slot id out of range: {slot_id}")

        self._buff.hover = slot_id

    def __slot_unhover(self, slot_id: int) -> None:
        """reset hover (only when slot_id matches hover)"""
        if not slot_id == self._buff.hover:
            return

        self._buff.hover = 255  # 255 = none

    # endregion

    # region drawing
    def draw_at(
        self, position: tuple[float, float], slots_per_row: int, width: float
    ) -> None:
        """draw inventory at center of screen"""
        self._ui["root"].position.relative_global = position

        slot_size = width / (slots_per_row + 0.1)
        rows = round(self._buff.size / slots_per_row)

        slots: list[Rectangle] = self._ui["slots"]  # ignore: type

        slots[0].size.relative_global = slot_size, slot_size
        slots[0].size.relative_global.y = slots[
            0
        ].size.relative_global.x
        slot_size = (
            slots[0].size.absolute.x,
            slots[0].size.absolute.x,
        )

        width = slot_size[0] * (slots_per_row + 0.1)
        height = slot_size[1] * (rows + 0.1)
        size = Vec2().from_cartesian(width, height)
        self._ui["root"].size.absolute = size

        # if draw_background:
        self._ui["root"].gl_draw(force_draw=True, delta_cal=0)

        start = self._ui["root"].position.absolute_global.copy()
        start.x -= slot_size[0] * (slots_per_row / 2)
        start.y -= slot_size[1] * (rows / 2)

        for row in range(rows):
            for col in range(slots_per_row):
                slot_id = row * slots_per_row + col
                if slot_id == self._buff.selected:
                    highlight = True

                else:
                    highlight = False

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

                ui_slot.gl_draw(force_draw=True, delta_cal=0)

                slot = self._buff.slots[slot_id]
                if slot.count > 0:
                    if slot.item_id == 255:
                        continue

                    texture, size = ITEM_IDS[slot.item_id].get_icon()

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
                    )

    # endregion
