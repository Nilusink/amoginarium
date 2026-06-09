"""
Defines PositionedLogicEntity.

Defines an entity with spatial properties (position and size).
Extends BaseLogicEntity to synchronize its spatial properties with the C-level buffer.

| ``Path``: amoginarium/logic/entities/_base/_base_entities/_positioned_logic_entity.py
| ``Project``: amoginarium
| ``Created``: 28.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import PositionedLogicEntityLike

from ._base_logic_entity import BaseLogicEntity

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.utility import Vec2


class PositionedLogicEntity(BaseLogicEntity, PositionedLogicEntityLike):
    """A logic entity with position and size."""

    __slots__ = ("position", "size")

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
        Logic entity with position and size.

        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param parent: Optional parent entity
        """
        super().__init__(runtime_buffer=runtime_buffer, parent=parent)
        self.position = position
        self.size = size

    # region Methods: Update
    @tp.override
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity.

        :param delta: Time since the last update
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
