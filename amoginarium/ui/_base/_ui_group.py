"""
amoginarium/ui/_base/_ui_group.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from amoginarium.entities import BaseGroup


class UIGroup(BaseGroup):
    __visible: bool = False

    def __init__(self) -> None:
        super().__init__()

    def hide(self) -> None:
        self.__visible = False

    def gl_draw(self) -> None:
        self.__visible = True
        super().gl_draw()

    @property
    def visible(self) -> bool:
        return self.__visible
