"""
amoginarium/entities/_ui/_ui_entity.py

Project: amoginarium
"""

from .._base_entity import BaseEntity, PositionedEntity
from ...base import Drawn, Updated
from ...logic import Vec2


##################################################
#                     Code                       #
##################################################

class UIEntity(PositionedEntity):
    """
    Basically UI-Element, no UI, just basic logic
    """

    def __init__(
            self,
            position: Vec2,
            size: Vec2,
            parent: BaseEntity = ...
    ) -> None:
        super().__init__(position, size, parent)
        self.add(Drawn)
        self.add(Updated)

    def update(self, delta: float) -> None:
        pass

    def gl_draw(self) -> None:
        pass
