"""
amoginarium/ui/_base/_ui_group.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from amoginarium.entities import BaseGroup


class UIGroup(BaseGroup):
    """UI root group"""
    __visible: bool

    def __init__(self) -> None:
        super().__init__()
        self.__visible = False

    def hide(self) -> None:
        """Hide the group"""
        self.__visible = False
        for sprite in self.sprites():
            sprite.hide()

    def gl_draw(self) -> None:
        self.__visible = True
        super().gl_draw()

    @property
    def visible(self) -> bool:
        """:return: Whether the group is visible"""
        return self.__visible
