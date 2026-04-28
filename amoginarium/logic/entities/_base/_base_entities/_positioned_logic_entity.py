"""
amoginarium/logic/entities/_base/_base_entities/_positioned_logic_entity.py

Defines an entity with spatial properties (position and size).
Extends BaseLogicEntity to synchronize its spatial properties with the C-level buffer.

Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from ._base_logic_entity import BaseLogicEntity

if tp.TYPE_CHECKING:
    from types import EllipsisType
    from ctypes import Array

    from amoginarium.shared import base_entity_t, CIDType
    from amoginarium.shared.utility import Vec2


class PositionedLogicEntity(BaseLogicEntity):
    """A logic entity with position and size."""
    __slots__ = ("position", "size")

    # region ClassVars
    _CID: tp.ClassVar[CIDType | EllipsisType] = ...  # for serialization

    # endregion

    # region InstanceVars
    _parent: PositionedLogicEntity | None

    # public / no property for faster access
    position: Vec2
    size: Vec2

    # endregion

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            *,
            parent: PositionedLogicEntity | None = None,
    ) -> None:
        """
        A logic entity with position and size
        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param parent: Optional parent entity
        """
        super().__init__(runtime_buffer=runtime_buffer, parent=parent)
        self.position = position
        self.size = size

    # region Class-Methods
    @classmethod
    def cid(cls) -> CIDType:
        """
        :return: the entities' component ID
        :raises ValueError: if the class has no __cid
        """
        if cls._CID == ...:
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._CID.value  # type: ignore

    # endregion

    # region Properties (and other getters)
    def _get_ids(self) -> list[int]:
        """:return: list of all entity IDs including this one and its parents recursively"""
        if self.parent is None:
            return [self.id]
        return self.parent._get_ids() + [self.id]

    # endregion

    # region Methods: Update
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity
        :param delta: time since the last update
        """
        pos: Vec2 = self.position
        size: Vec2 = self.size
        buf_entry: base_entity_t = self._runtime_buffer[self.id]

        buf_entry.pos_x = pos.x
        buf_entry.pos_y = pos.y
        buf_entry.size_x = int(size.x)
        buf_entry.size_y = int(size.y)

        super()._update(delta)

    # endregion
