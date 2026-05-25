"""
Defines a synced graphics entity for rendering static text.

| ``Path``: amoginarium/graphics/logic_dummies/_text_entity.py
| ``Project``: amoginarium
| ``Created``: 12.04.2026
| ``Authors``: LukasKrah
"""

import typing as tp

from icecream import ic

from amoginarium.shared import GraphicsCIDs
from amoginarium.shared.utility import Color

from ..render_bindings import renderer
from ._synced_entities import SyncedGraphicsEntity


class TextEntity(SyncedGraphicsEntity):
    """
    Static text synced graphics entity.
    """

    _CID = GraphicsCIDs.static_text

    def __init__(
        self,
        sync_id: int,
        text: str,
        color: tuple[int, int, int] | tuple[int, int, int, int],
        bg_color: tuple[int, int, int] | tuple[int, int, int, int],
        size: int,
        family: str,
        bold: bool,
        italic: bool,
        **_kwargs: tp.Any,
    ) -> None:
        """
        Create a static text entity
        :param sync_id: Sync id
        :param text: Text to be displayed
        :param color: Color of the text
        :param bg_color: Background color
        :param size: Font size
        :param family: Font family
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param _kwargs: Other arguments passed such as coalition.
        """
        super().__init__(sync_id)

        self._text_id = renderer.generate_static_text(
            text,
            Color().from_255(*color),
            Color().from_255(*bg_color),
            font_size=size,
            font_family=family,
            bold=bold,
            italic=italic,
        )

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)

        renderer.draw_static_text(
            self.world_position,
            self._text_id,
        )
