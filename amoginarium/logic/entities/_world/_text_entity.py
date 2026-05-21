"""
Logic representation for static text elements.

Path: amoginarium/logic/entities/_world/_text_entity.py
Project: amoginarium
Created: 11.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium import pv
from amoginarium.shared import BaseCommandType, Coalitions, GraphicsCIDs, ProcessCommand
from amoginarium.shared.utility import Vec2

from .._base import LogicGameEntity, Updated

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, CIDType


class TextEntity(LogicGameEntity):
    """
    Static text logic game entity.
    """

    __slots__ = ()
    _CID: tp.ClassVar[CIDType] = GraphicsCIDs.static_text

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        position: Vec2,
        text: str,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (0, 0, 0),
        bg_color: tuple[int, int, int] | tuple[int, int, int, int] = (0, 0, 0, 0),
        size: int = 64,
        family: str = "arial",
        bold: bool = False,
        italic: bool = False,
        **kwargs: tp.Any,
    ) -> None:
        """
        Create a static text entity
        :param runtime_buffer: Runtime buffer synced between logic and graphic process
        :param position: Position of the text
        :param text: Text to be displayed
        :param color: Color of the text
        :param bg_color: Background color
        :param size: Font size
        :param family: Font family
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param kwargs: Other arguments passed such as coalition.
        """
        super().__init__(runtime_buffer, Vec2(), position, coalition=Coalitions.neutral)

        self.remove(Updated)
        self.update(0)
        kwargs["coalition"] = Coalitions.neutral
        kwargs["id"] = self.id
        kwargs["cid"] = self.cid()
        kwargs["text"] = text
        kwargs["color"] = color
        kwargs["bg_color"] = bg_color
        kwargs["size"] = size
        kwargs["family"] = family
        kwargs["bold"] = bold
        kwargs["italic"] = italic

        pv.COQ.put(ProcessCommand(type=BaseCommandType.spawn_dummy, kwargs=kwargs))
