"""
amoginarium/logic/entities/_base_entities/_positioned_logic_entity.py

Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared import base_entity_t, CIDType
from amoginarium.shared.utility import Vec2

from .._collision import collision_manager
from ._base_logic_entity import BaseLogicEntity


class PositionedLogicEntity(BaseLogicEntity):
    """
    A logic entity with position and size.
    Optional collision detection
    """
    _cid: tp.ClassVar[CIDType | EllipsisType] = ...  # for serialization

    __slots__ = ("position", "size", "_has_collision", "_collision_id", "_centered")

    position: Vec2  # public / no property for faster access
    size: Vec2  # public / no property for faster access
    _centered: bool

    _collision_group: tp.ClassVar[int | None] = None
    _has_collision: bool
    _collision_id: int | None

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            *,
            parent: BaseLogicEntity | None = None,
            centered: bool = False,
            has_collision: bool = False,
    ) -> None:
        """
        A logic entity with position, size, and optional collision detection
        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param parent: Optional parent entity
        :param centered: Whether the position is center or top left (relevant for collision detection)
        :param has_collision: Whether the entity has collision detection
        """
        super().__init__(runtime_buffer=runtime_buffer, parent=parent)
        self.position = position
        self.size = size

        self._centered = centered
        self._has_collision = has_collision

        if self._collision_group is not None and self._has_collision:
            self._collision_id = collision_manager.register_entity(
                group_id=self._collision_group,
                instance=self,
                pos=self.position,
                size=self.size,
                centered=self._centered)
        else:
            self._collision_id = None

    # region Class-Methods
    @classmethod
    def cid(cls) -> CIDType:
        """
        :return: the entities' component ID
        :raises ValueError: if the class has no __cid
        """
        if isinstance(cls._cid, EllipsisType):
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._cid

    # endregion

    # region Methods: Collision
    def _on_collision(self, event: CollisionEvent) -> None:
        """
        Reaction to collision
        :param event: Event details
        """
        ...

    @tp.final
    def on_collision(self, event: CollisionEvent) -> None:
        """
        Calls _on_collision and updates collision entity
        :param event: Event details
        """
        self._on_collision(event)

        if self._collision_id is not None:  # just to be safe xD
            collision_manager.update_entity(
                group_id=self._collision_group,
                entity_id=self._collision_id,
                pos=self.position + event.normal,
                size=self.size,
                centered=self._centered
            )

    # endregion

    # region Methods: Update, Kill
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity
        :param delta: time since the last update
        """
        self._runtime_buffer[self.id].pos_x = self.position.x
        self._runtime_buffer[self.id].pos_y = self.position.y
        self._runtime_buffer[self.id].size_x = int(self.size.x)
        self._runtime_buffer[self.id].size_y = int(self.size.y)

        if self._collision_id is not None:
            collision_manager.update_entity(
                group_id=self._collision_group,
                entity_id=self._collision_id,
                pos=self.position,
                size=self.size,
                centered=self._centered
            )

        super()._update(delta)

    def kill(self, killed_by: tp.Any = ...) -> None:
        """
        Remove from groups and collision manager
        :param killed_by: who killed this entity
        """
        if self._collision_id is not None:
            collision_manager.delete_entity(self._collision_group, self._collision_id)
            self._collision_id = None
        super().kill(killed_by)

    # endregion