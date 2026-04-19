"""
amoginarium/logic/entities/_base_entities/_positioned_logic_entity.py

Project: amoginarium
Created: 28.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

from types import EllipsisType
from ctypes import Array
from icecream import ic
import typing as tp

from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared import base_entity_t, CIDType
from amoginarium.shared.utility import Vec2

from .._collision.collision_manager import collision_manager
from ._base_logic_entity import BaseLogicEntity
if tp.TYPE_CHECKING:
    from .._debug import PolyDebugRenderingEntity

class PositionedLogicEntity(BaseLogicEntity):
    """
    A logic entity with position and size.
    Optional collision detection
    """
    _cid: tp.ClassVar[CIDType | EllipsisType] = ...  # for serialization

    DRAW_DEBUG_HITBOXES: tp.ClassVar[bool] = True
    DEBUG_ENTITY_CLASS: tp.ClassVar[type["PolyDebugRenderingEntity"]]

    __slots__ = ("position", "size", "_has_collision", "_collision_id", "active_normals", "_centered", "__debug")

    position: Vec2  # public / no property for faster access
    size: Vec2  # public / no property for faster access
    _centered: bool

    _collision_group: tp.ClassVar[int | None] = None
    _has_collision: bool
    _collision_id: int | None

    active_normals: dict[int, list[Vec2]]

    __debug: PolyDebugRenderingEntity | None

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            *,
            parent: BaseLogicEntity | None = None,
            centered: bool = False,
    ) -> None:
        """
        A logic entity with position, size, and optional collision detection
        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param parent: Optional parent entity
        :param centered: Whether the position is center or top left (relevant for collision detection)
        """
        super().__init__(runtime_buffer=runtime_buffer, parent=parent)
        self.position = position
        self.size = size
        self._centered = centered

        self.active_normals = {}
        self._collision_id = None
        self.__debug = None

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

        if self._collision_id is not None:
            self._update_collision(shift_history=False)

    @tp.final
    def set_normals(self, group_id: int, normals: list[Vec2]) -> None:
        """
        Called when normal configuration updates
        :param group_id: Event group id
        :param normals: list of updated normals
        """
        # ic("SET NORMALS:", self, group_id, normals)
        self.active_normals[group_id] = normals

    def _create_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...,
    ) -> None:
        if position == ...:
            position = self.position
        if size == ...:
            size = self.size
        if centered == ...:
            centered = self._centered

        self._collision_id = collision_manager.register_entity(
            group_id=self._collision_group,
            instance=self,
            pos=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered
        )
        if PositionedLogicEntity.DRAW_DEBUG_HITBOXES:
            self.__debug = PositionedLogicEntity.DEBUG_ENTITY_CLASS(
                self._runtime_buffer, radius=1
            )

    def _update_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...,
            shift_history: bool = True
    ) -> None:
        if self._collision_id is None:
            return

        if position == ...:
            position = self.position
        if size == ...:
            size = self.size
        if centered == ...:
            centered = self._centered

        collision_manager.update_entity(
            group_id=self._collision_group,
            entity_id=self._collision_id,
            pos=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            shift_history=shift_history
        )
        if PositionedLogicEntity.DRAW_DEBUG_HITBOXES:
            self.__debug.set_points(collision_manager.get_points(self._collision_group, self._collision_id))

    def _delete_collision(self) -> None:
        if self._collision_id is None:
            return

        collision_manager.delete_entity(self._collision_group, self._collision_id)
        self._collision_id = None

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
        self._update_collision()
        super()._update(delta)

    def kill(self, killed_by: tp.Any = ...) -> None:
        """
        Remove from groups and collision manager
        :param killed_by: who killed this entity
        """
        self._delete_collision()
        if self.__debug is not None:
            self.__debug.kill()
        super().kill(killed_by)

    # endregion