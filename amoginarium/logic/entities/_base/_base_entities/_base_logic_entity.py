"""
Defines BaseLogicEntity.

Defines the most basic logic entity structure.
Includes hierarchy management, lifecycle hooks, and bitwise buffer access.

| ``Path``: amoginarium/logic/entities/_base/_base_entities/_base_logic_entity.py
| ``Project``: amoginarium
| ``Created``: 28.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import ctypes
import typing as tp

from icecream import ic

from amoginarium import pv
from amoginarium.shared import BaseCommandType, BaseLogicEntityLike
from amoginarium.shared import ENTITY_COUNTER, ProcessCommand
from amoginarium.shared.debugging import SharedDebuggingInstance

from .._groups import Dead, Updated

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t, CIDType
    from amoginarium.shared import EntityChildViable, MurderViable

    from .._groups import LogicGroup


class BaseLogicEntity(BaseLogicEntityLike):
    """
    Most basic type of logic entity.

    - Parent/Children relations
    - Groups
    - Update
    - Visibility

    :ivar _sdi: shared debugging instance (if created)
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

    # region ClassVars
    _CID: tp.ClassVar[CIDType | EllipsisType] = ...  # for serialization
    _ADVANCED_DEBUGGING: tp.ClassVar[bool] = False
    _AD_VARS: tp.ClassVar[list[tuple[str, type | tuple[type, int]]]] = [
        ("_alive", bool),
    ]
    _AD_CONSOLE_LINES: tp.ClassVar[int] = 2
    # endregion

    # region InstanceVars
    _parent: BaseLogicEntity | None
    _children: list[EntityChildViable]
    _lifetime: float
    _runtime_buffer: Array[base_entity_t]
    __id: int
    __groups: list[LogicGroup]

    _alive: bool
    _sdi: SharedDebuggingInstance | None

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

        # create shared debugging instance if required
        if self._ADVANCED_DEBUGGING:
            self._sdi: SharedDebuggingInstance = SharedDebuggingInstance(
                pv.SH,
                self._AD_VARS,
                self._AD_CONSOLE_LINES,
            )
            self._sdi.create()

    # region properties (and other getters)
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

    def _get_ids(self) -> list[int]:
        """:return: list of all entity IDs including this one and parents"""
        if self._parent is None:
            return [self.id]
        return self._parent._get_ids() + [self.id]  # noqa: SLF001

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

        # commit suicide
        for group in self.__groups:
            group.remove(self)

        self._set_bit("flags", 0, False)  # set alive  # noqa: FBT003
        ENTITY_COUNTER.pop_id(self.__id)

        self.__groups.clear()

        # free buffer
        if self._ADVANCED_DEBUGGING:
            self._sdi.kill()

        # add to dead
        Dead.add(self)  # type: ignore[trust]

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

        if self._ADVANCED_DEBUGGING:
            self._sdi.write_from_object(self)

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

    # region Methods: component ID

    @classmethod
    def has_cid(cls) -> bool:
        """:return: Return True if the entity has a CID."""
        return cls._CID != ...

    @classmethod
    def cid(cls) -> CIDType:
        """
        Return CID.

        :return: The entities' component ID
        :raise ValueError: if the class has no __cid
        """
        if cls._CID == ...:
            raise ValueError("_CID is not defined for " + cls.__name__)

        return cls._CID.value  # type: ignore[Any]

    # endregion

    # region Methods: graphics sync
    def _spawn_graphics_entity(
        self,
        *args: tp.Any,
        skip_cid: bool = False,
        **kwargs: tp.Any,
    ) -> None:
        """
        Spawn graphics entity.
        """
        kwargs["id"] = self.id

        if not skip_cid:
            kwargs["cid"] = self.cid()

        if self._ADVANCED_DEBUGGING:
            kwargs["adv_debugging_data"] = self._sdi.get_spawn_data()

        pv.COQ.put(
            ProcessCommand(type=BaseCommandType.spawn_dummy, kwargs=kwargs, args=args)
        )

    # endregion
