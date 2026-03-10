"""
amoginarium/entities/_ui/_ui_entity.py

Project: amoginarium
"""

from __future__ import annotations

from ._group import UIGroup
from ..entities import BaseEntity

import typing as tp


##################################################
#                     Code                       #
##################################################

class UIEntity(BaseEntity):
    """
    Basically UI-Element, no UI, just basic logic
    """

    __group: UIGroup | None

    def __init__(self, parent: UIEntity | None = None) -> None:
        super().__init__(parent)

        self._children = []

        if parent is None:
            self.__group = UIGroup()
            self.add(self.__group)
            self.__dict__["root"] = self
        else:
            self.__group = None
            parent._add_child(self)

    def _add_child(self, child: UIEntity) -> None:
        self._children.append(child)
        child._parent = self._parent if self._parent is not None else self
        child.add(self.__group)

    def group_update(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        if self.__group is None:
            self.root.group_update(args=args, kwargs=kwargs)
            return
        self.__group.update(args=args, kwargs=kwargs)

    def group_draw(self) -> None:
        if self.__group is None:
            self.root.group_draw()
            return
        self.__group.gl_draw()

    def update(self, delta: float) -> None:
        return

    def gl_draw(self) -> None:
        return
