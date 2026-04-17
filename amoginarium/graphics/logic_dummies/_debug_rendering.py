"""
amoginarium/graphics/logic_dummies/_dynamic_debug_rendering.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared.utility import coord_t, Vec2, color_t, convert_coord, convert_color
from amoginarium.shared import DebugRendering, GraphicsCIDs

from ._synced_entities import SyncedGraphicsEntity
from ..entities import Drawn_2, Drawn_0
from ..render_bindings import renderer


class DebugRenderingEntity(SyncedGraphicsEntity):
    _cid = GraphicsCIDs.debug_rendering

    __rendering: DebugRendering
    __convert_global: bool

    def __init__(
            self,
            sync_id: int,
            rendering: DebugRendering,
            color: tuple[int, int, int] | tuple[int, int, int, int],
            centered: bool = False,
            convert_global: bool = False,
            **_kwargs: tp.Any
    ) -> None:
        super().__init__(sync_id)
        self.__rendering = rendering
        self.__convert_global = convert_global
        self.__color = color
        self.__centered = centered

        self.add(Drawn_2)
        self.remove(Drawn_0)

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        pos = self.world_position - self.size / 2 if self.__centered else self.world_position
        match self.__rendering:
            case DebugRendering.RECTANGLE:
                renderer.draw_rect_line(start=pos, size=self.size, thickness=5,
                                        color=self.__color, convert_global=self.__convert_global)
