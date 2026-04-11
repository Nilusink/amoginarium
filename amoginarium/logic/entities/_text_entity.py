"""
amoginarium/logic/entities/_text_entity.py

Project: amoginarium
Created: 11.04.2026
Authors: LukasKrah
"""

from ctypes import Array
import typing as tp

from amoginarium.shared import GraphicsCIDs, base_entity_t, BaseCommandType, ProcessCommand, Coalitions
from amoginarium.shared.utility import Vec2
from amoginarium import pv

from ._base_entity import LogicGameEntity
from ._logic_groups import Updated


class TextEntity(LogicGameEntity):
    """
    Static text logic game entity
    """
    _cid = GraphicsCIDs.static_text

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
            **kwargs: tp.Any
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
        :param kwargs: Other arguments passed such as coalition
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

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs=kwargs
        ))
