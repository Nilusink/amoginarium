"""
_base_entity.py
29.03.2026

Graphics base entity

Author:
Nilusink
"""
import typing as tp


class BaseGraphicsEntity:
    __slots__ = ["__g", "_children", "_parent"]

    _parent: tp.Self | None
    _children: list[tp.Self]

    def __init__(self, parent: tp.Self | None) -> None:
        # pygame groups
        self.__g = []

        self._parent = parent
        self._children = []

    # region Methods: pygame
    def add(self, *groups) -> None:
        """
        add entity to one or more groups
        """
        has = self.__g.__contains__

        for group in groups:
            if not has(group):
                group.add_internal(self)
                self.__g.append(group)

    def remove(self, *groups) -> None:
        """
        remove entity from one or more groups
        """
        has = self.__g.__contains__

        for group in groups:
            if has(group):
                group.remove_internal(self)
                self.__g.remove(group)

    def kill(self) -> None:
        """
        remove entity from all groups
        """
        # kill children first
        for child in self._children:
            child.kill()

        # commit suicide
        for group in self.__g:
            group.remove_internal(self)

        self.__g.clear()

    # endregion
