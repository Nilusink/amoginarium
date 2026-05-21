"""
Defines BaseLogicEntity.

Defines the most basic logic entity structure.
Includes hierarchy management, lifecycle hooks, and bitwise buffer access.

Path: amoginarium/logic/entities/_base/_base_entities/_base_logic_entity.py
Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium import pv
from amoginarium.shared import BaseLogicEntityLike, ENTITY_COUNTER

from .._groups import Updated

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t, EntityChildViable, MurderViable

    from .._groups import LogicGroup


class BaseLogicEntity(BaseLogicEntityLike):
    """
    Most basic type of logic entity.

    - Parent/Children relations
    - Groups
    - Update
    - Visibility
    """

    __slots__ = [
        "_parent",
        "_children",
        "_lifetime",
        "_runtime_buffer",
        "__id",
        "__groups",
        "_alive",
    ]

    # region InstanceVars
    _parent: BaseLogicEntity | None
    _children: list[EntityChildViable]
    _lifetime: float
    _runtime_buffer: Array[base_entity_t]
    __id: int
    __groups: list[LogicGroup]

    _alive: bool

    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        *,
        parent: BaseLogicEntity | None = None,
    ) -> None:
        """
        Most basic type of logic entity.

        :param runtime_buffer: Logic runtime buffer
        :param parent: Optional parent entity
        """
        self._parent = parent
        self._children = []
        self._lifetime = 0
        self.__groups = []
        self._alive = True

        # data block
        self.__id = ENTITY_COUNTER.get_id()
        self._runtime_buffer = runtime_buffer

        self._set_bit("flags", 0, True)  # set alive # noqa: FBT003
        self._set_bit("flags", 1, True)  # set visible # noqa: FBT003

        # directly write to RAM to make sure the graphics entity has correct data
        pv.E_BUFF[self.__id] = self._runtime_buffer[self.__id]

        self.add(Updated)

    # region Properties
    @property
    def alive(self) -> bool:
        """Whether the entity is alive."""
        return self._alive

    @property
    def id(self) -> int:
        """:return: entity id (+ buffer location)"""
        return self.__id

    @property
    def parent(self) -> BaseLogicEntity | None:
        """:return: Entity parent if present"""
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

    @property
    def lifetime(self) -> float:
        """Time since entity spawn."""
        return self._lifetime

    @property
    def runtime_buffer(self) -> Array[base_entity_t]:
        """Entity runtime buffer."""
        return self._runtime_buffer

    # endregion

    # region Methods: bitwise fun
    def _set_bit(
        self,
        param: str,
        bit_index: int,
        value: bool,  # noqa: FBT001
    ) -> None:
        """
        Set (or reset) on a specified bit.

        :param param: What parameter to set the bit at
        :param bit_index: Bit to set
        :param value: What to set the bit to
        """
        # get value from the buffer
        attribute = getattr(self._runtime_buffer[self.id], param)

        # set bit (bitwise or)
        if value:
            attribute |= 1 << bit_index

        # reset bit (bitwise and with inverted mask)
        else:
            attribute &= ~(1 << bit_index)

        # write value to buffer
        setattr(self._runtime_buffer[self.id], param, attribute)

    # endregion

    # region Methods: Groups + Kill
    def add(self, *groups: LogicGroup) -> None:
        """
        Add entity to one or more logic groups.

        :param groups: To add entity to
        """
        has = self.__groups.__contains__

        for group in groups:
            if not has(group):
                group.add(self)
                self.__groups.append(group)

    def remove(self, *groups: LogicGroup) -> None:
        """
        Remove entity from one or more logic groups.

        :param groups: To remove entity from
        """
        has = self.__groups.__contains__

        for group in groups:
            if has(group):
                group.remove(self)
                self.__groups.remove(group)

    # noinspection PyUnusedLocal, PyMethodMayBeStatic
    def _before_kill(  # noqa: PLR6301
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,  # noqa: ARG002
        kill_children: bool = True,  # noqa: ARG002
    ) -> bool:
        """
        Whether the entity can be killed. Called before _kill.

        :param killed_by: Who killed this entity
        :param kill_children: Whether to kill children as well recursively
        :return: Whether the entity kill is accepted
        """
        return True

    def _kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,  # noqa: ARG002
        kill_children: bool = True,
    ) -> None:
        """
        Kill the entity and all its children.

        :param killed_by: Who killed this entity
        :param kill_children: Whether to kill children as well recursively
        """
        # kill children first
        if kill_children:
            for child in self._children:
                child.kill()

        for group in self.__groups:
            group.remove(self)

        self._set_bit("flags", 0, False)  # set alive  # noqa: FBT003
        ENTITY_COUNTER.pop_id(self.__id)

        self.__groups.clear()

    def _after_kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
        killed: bool = True,
    ) -> None:
        """
        Reaction at the end of kill no matter if the kill was accepted or not.

        :param killed_by: Who killed this entity
        :param kill_children: Whether to kill children as well recursively
        :param killed: Whether the entity kill was accepted or not
        """

    @tp.final
    def kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
        force_kill: bool = False,
    ) -> bool | None:
        """
        Kill the entity and all its children.

        :param killed_by: Who killed this entity
        :param kill_children: Whether to kill children as well as recursively
        :param force_kill: Whether to kill even if before kill returns False
        :return: Whether the entity wa0s killed or not. May be denied by _before_kill.
            None if the entity is already dead.
        """
        if self._alive:
            killed: bool = False

            kill_entity: bool | None = self._before_kill(
                killed_by=killed_by, kill_children=kill_children
            )

            if force_kill or kill_entity is True or kill_entity is None:
                self._alive = False
                self._kill(killed_by=killed_by, kill_children=kill_children)
                killed = True

            self._after_kill(
                killed_by=killed_by, kill_children=kill_children, killed=killed
            )
            return killed
        return None

    # endregion

    # region Methods: update
    def _update(self, delta: float) -> None:
        """
        Update function for the entity.

        :param delta: Time since the last update
        """
        self._lifetime += delta

    @tp.final
    def update(self, delta: float, *, recursive: bool = True) -> None:
        """
        Update entity and their children.

        :param delta: Time since the last update
        :param recursive: Whether to update children recursively
        """
        self._update(delta)

        if recursive:
            for child in self._children:
                child.update(delta)

    # endregion

    # region Methods: visibility
    def show(self) -> None:
        """Set visibility to 1."""
        self._set_bit("flags", 1, True)  # noqa: FBT003

    def hide(self) -> None:
        """Set visibility to 0."""
        self._set_bit("flags", 1, False)  # noqa: FBT003

    def highlight(self) -> None:
        """Highlight the graphics entity."""
        self._set_bit("flags", 2, True)  # noqa: FBT003

    def stop_highlight(self) -> None:
        """Stop highlighting the graphics entity."""
        self._set_bit("flags", 2, False)  # noqa: FBT003

    # endregion
