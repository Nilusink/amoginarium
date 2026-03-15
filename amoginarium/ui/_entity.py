"""
amoginarium/entities/_ui/_ui_entity.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from ..entities import BaseEntity

from ._group import UIGroup


class UIEntity(BaseEntity):
    """Base UI-Entity, no UI, just default entity relation / method stuff"""
    __group: UIGroup | None

    def __init__(self, parent: UIEntity | None = None) -> None:
        """
        Create base UI-Entity
        :param parent: Optional parent UI-Entity
        """
        super().__init__(parent)

        self._children = []

        if parent is None:
            # If no parent is given, this is a root UI-Entity
            self.__group = UIGroup()
            self.add(self.__group)
            self.__dict__["root"] = self
        else:
            self.__group = None
            parent._add_child(self)

    def _add_child(self, child: UIEntity) -> None:
        """
        Add a child UI-Entity to this UI-Entity
        :param child: Child UI-Entity
        """
        self._children.append(child)
        child.add(self.__group)

    def group_update(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """
        Update all in the root-group where this UI-Entity belongs to
        :param args: Passed to update
        :param kwargs: Passed to update
        """
        if self.__group is None:
            self.root.group_update(args=args, kwargs=kwargs)
            return
        self.__group.update(args=args, kwargs=kwargs)

    def group_draw(self) -> None:
        """GL-Draw all in the root-group where this UI-Entity belongs to"""
        if self.__group is None:
            self.root.group_draw()
            return
        self.__group.gl_draw()

    def update(self, delta: float) -> None:
        """
        Update, that is called by the update loop of the game
        :param delta: Time since the last update in seconds
        """
        return

    def gl_draw(self) -> None:
        """Draw, that is called by the game loop every frame"""
        return
