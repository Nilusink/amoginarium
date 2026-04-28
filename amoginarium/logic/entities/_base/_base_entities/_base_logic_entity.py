"""
amoginarium/logic/entities/_base_entities/_base_logic_entity.py

Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import ENTITY_COUNTER
from amoginarium import pv

from .._groups import Updated

if tp.TYPE_CHECKING:
    from types import EllipsisType
    from ctypes import Array

    from amoginarium.shared import base_entity_t

    from .._groups import LogicGroup


class EntityChildViable(tp.Protocol):
    """Minimum requirements for an object to be assigned as a child of a logic entity."""

    def update(self, delta: float) -> None:
        """
        Update function
        :param delta: Tme since the last update
        """

    def kill(self) -> None:
        """Clean up and terminate the child."""


class BaseLogicEntity:
    """
    Most basic type of logic entity.
    - Parent/Children relations
    - groups
    - update
    - visibility
    """
    __slots__ = ("_parent", "_children", "_lifetime", "_runtime_buffer", "__id", "__groups", "__alive")

    # region InstanceVars
    _parent: BaseLogicEntity | None
    _children: list[EntityChildViable]
    _lifetime: float
    _runtime_buffer: Array[base_entity_t]
    __id: int
    __groups: list[LogicGroup]

    __alive: bool

    # endregion

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            *,
            parent: BaseLogicEntity | None = None,
    ) -> None:
        """
        most basic type of logics entity
        :param runtime_buffer: Logic runtime buffer
        :param parent: Optional parent entity
        """
        self._parent = parent
        self._children = []
        self._lifetime = 0
        self.__groups = []
        self.__alive = True

        # data block
        self.__id = ENTITY_COUNTER.get_id()
        self._runtime_buffer = runtime_buffer

        self._set_bit("flags", 0, True)  # set alive
        self._set_bit("flags", 1, True)  # set visible

        # directly write to RAM to make sure the graphics entity has correct data
        pv.E_BUFF[self.__id] = self._runtime_buffer[self.__id]

        self.add(Updated)

    # region Properties
    @property
    def id(self) -> int:
        """:return: entity id (+ buffer location)"""
        return self.__id

    @property
    def parent(self) -> BaseLogicEntity | None:
        """:return: entities parent if present"""
        return self._parent

    @property
    def root(self) -> BaseLogicEntity:
        """:return: root entity; entity parent if present else self"""
        if self._parent:
            return self._parent.root
        return self

    @property
    def children(self) -> list[EntityChildViable]:
        """:return: list of all children of this entity"""
        return self._children

    @property
    def _buffer(self) -> base_entity_t:
        """:return: runtime buffer data for this entity"""
        return self._runtime_buffer[self.__id]

    # endregion

    # region Methods: bitwise fun
    def _set_bit(self, param: str, bit_index: int, value: bool) -> None:
        """
        set (or reset) on a specified bit
        :param param: what parameter to set the bit at
        :param bit_index: bit to set
        :param value: what to set the bit to
        """
        # get value from the buffer
        attribute = getattr(self._runtime_buffer[self.id], param)

        # set bit (bitwise or)
        if value:
            attribute |= (1 << bit_index)

        # reset bit (bitwise and with inverted mask)
        else:
            attribute &= ~(1 << bit_index)

        # write value to buffer
        setattr(self._runtime_buffer[self.id], param, attribute)

    # endregion

    # region Methods: Groups + Kill
    def add(self, *groups: LogicGroup) -> None:
        """
        add entity to one or more logic groups
        :param groups: to add entity to
        """
        has = self.__groups.__contains__

        for group in groups:
            if not has(group):
                group.add(self)
                self.__groups.append(group)

    def remove(self, *groups: LogicGroup) -> None:
        """
        remove entity from one or more logic groups
        :param groups: to remove entity from
        """
        has = self.__groups.__contains__

        for group in groups:
            if has(group):
                group.remove(self)
                self.__groups.remove(group)

    def _kill(self, killed_by: BaseLogicEntity | EllipsisType = ...) -> None:
        """
        Kill entity and all its children
        :param killed_by: who killed this entity
        """
        # kill children first
        for child in self._children:
            child.kill()

        for group in self.__groups:
            group.remove(self)

        self._set_bit("flags", 0, False)  # set alive
        ENTITY_COUNTER.pop_id(self.__id)

        self.__groups.clear()

    @tp.final
    def kill(self, killed_by: BaseLogicEntity | EllipsisType = ...) -> None:
        """
        Kill entity and all its children
        :param killed_by: who killed this entity
        """
        if self.__alive:
            self.__alive = False
            self._kill(killed_by)

    # endregion

    # region Methods: update
    def _update(self, delta: float) -> None:
        """
        Update function for the entity
        :param delta: time since the last update
        """
        self._lifetime += delta

    @tp.final
    def update(self, delta: float, recursive: bool = True) -> None:
        """
        Update entity and their children
        :param delta: time since the last update
        :param recursive: Whether to update children recursively
        """
        self._update(delta)

        if recursive:
            for child in self._children:
                child.update(delta)

    # endregion

    # region Methods: visibility
    def show(self) -> None:
        """Set visibility to 1"""
        self._set_bit("flags", 1, True)

    def hide(self) -> None:
        """Set visibility to 0"""
        self._set_bit("flags", 1, False)

    def highlight(self) -> None:
        """highlight the graphics entity"""
        self._set_bit("flags", 2, True)

    def stop_highlight(self) -> None:
        """stop highlighting the graphics entity"""
        self._set_bit("flags", 2, False)

    # endregion
