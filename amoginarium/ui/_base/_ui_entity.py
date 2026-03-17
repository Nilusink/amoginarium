"""
amoginarium/ui/_base/_ui_entity.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

from amoginarium.entities import BaseEntity

from ._ui_group import UIGroup


class UIEntity(BaseEntity):
    """Base UI-Entity, no UI, just default entity relation / method stuff"""
    # Note: There is no advanced group/parent/child setting after creation yet.
    # As long as there is no need, I would keep it simple.
    __group: UIGroup | None

    def __init__(self, parent: UIEntity | None = None) -> None:
        """
        Create base UI-Entity
        :param parent: Optional parent UI-Entity
        """
        super().__init__(parent)

        self._children = []

        if parent is None:
            # If no parent is given, assume this is a root UI-Entity
            self.__group = UIGroup()
            self.add(self.__group)
            self.__dict__["root"] = self
        else:
            self.__group = None
            parent._add_child(self)
            self.add(self.group)

    def _add_child(self, child: UIEntity) -> None:
        """
        Add a child UI-Entity to this UI-Entity
        :param child: Child UI-Entity
        """
        self._children.append(child)

    def update(self, delta: float) -> None:
        """
        Update, that is called by the update loop of the game
        :param delta: Time since the last update in seconds
        """
        return

    def hide(self) -> None:
        """Reset the UI-Entity"""
        return

    def gl_draw(self) -> None:
        """Draw, that is called by the game loop every frame"""
        return

    @property
    def group(self) -> UIGroup:
        """:return: The group where this UI-Entity belongs to"""
        if self.__group is None:
            return self.root.group
        return self.__group
