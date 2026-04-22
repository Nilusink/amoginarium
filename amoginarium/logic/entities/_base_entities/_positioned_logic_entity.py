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

from .._collision.collision_manager import collision_manager
from ._base_logic_entity import BaseLogicEntity

if tp.TYPE_CHECKING:
    from .._debug import PolyDebugRenderingEntity


class PositionedLogicEntity(BaseLogicEntity):
    """
    A logic entity with position and size.
    Optional collision detection
    """
    _COMPONENT_ID: tp.ClassVar[CIDType | EllipsisType] = ...  # for serialization

    __debug_draw_hitboxes: tp.Final[bool] = False
    __debug_entity_class: tp.ClassVar[type["PolyDebugRenderingEntity"]]  # todo - add: setter

    _DEFAULT_COLLISION_ROOT: bool = False
    _DEFAULT_COLLISION_ROOT_ADDITIVE: bool = False  # whether to check for the collision roots above or stop here
    _DEFAULT_COLLISION_GROUP: tp.ClassVar[int | None] = None

    __slots__ = ("position", "size", "_centered",
                 "_collision_id", "active_collisions",
                 "__debug", "active_normals", "__ignore_collision_ids")

    position: Vec2  # public / no property for faster access
    size: Vec2  # public / no property for faster access
    _centered: bool

    _collision_id: int | None

    # collision_id -> CollisionEvent
    active_collisions: dict[int, CollisionEvent]  # public / no property for faster access
    # group_id -> normals
    active_normals: dict[int, list[Vec2]]  # public / no property for faster access

    __debug: PolyDebugRenderingEntity | None

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            *,
            parent: BaseLogicEntity | None = None,
            centered: bool = False,
            collision_exceptions: list[int] | int | None = None,
            collision_exception_root: bool | None = None,
            collision_exception_root_additive: bool | None = None
    ) -> None:
        """
        A logic entity with position, size, and optional collision detection
        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param parent: Optional parent entity
        :param centered: Whether the position is center or top left (relevant for collision detection)
        :param collision_exceptions: Optional list of collision exception rules
        :param collision_exception_root: Groups this entity and all its children recursive to a collision exception rule
        :param collision_exception_root_additive: Whether root collision exception rules created from parents are also
            added to this entity and its children recursive
        """
        super().__init__(runtime_buffer=runtime_buffer, parent=parent)

        self.position = position
        self.size = size
        self._centered = centered

        self.active_collisions = {}
        self.active_normals = {}
        self._collision_id = None
        self.__debug = None

        self.__ignore_collision_id = []
        if collision_exceptions is not None:
            self.__ignore_collision_id.append(collision_exceptions)

    def _get_ids(self) -> list[int]:
        if self.parent is None:
            return [self.id]
        return self.parent._get_ids() + [self.id]

    # region Class-Methods
    @classmethod
    def cid(cls) -> CIDType:
        """
        :return: the entities' component ID
        :raises ValueError: if the class has no __cid
        """
        if isinstance(cls._COMPONENT_ID, EllipsisType):
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._COMPONENT_ID

    # endregion

    # region Methods: Collision
    def __calc_normals(self) -> None:
        active_normals: dict[int, list[Vec2]] = {}

        for event in self.active_collisions.values():
            if event.group_id not in active_normals:
                active_normals[event.group_id] = []
            active_normals[event.group_id].append(event.normal)

        self.active_normals = active_normals

    def _collision_start(self, event: list[CollisionEvent]) -> list[bool] | None:
        ...

    @tp.final
    def collision_start(self, events: list[CollisionEvent]) -> list[bool] | None:
        collisions_result = self._collision_start(events)

        for i in range(len(events)):
            if collisions_result is not None:
                if not collisions_result[i]:
                    continue
            self.active_collisions[events[i].collision_id] = events[i]

        self.__calc_normals()

        if self._collision_id is not None:
            self._update_collision(shift_history=False)
        return collisions_result

    def _collision_end(self, events: list[CollisionEvent]) -> None:
        ...

    @tp.final
    def collision_end(self, events: list[CollisionEvent]) -> None:
        actual_events = [
            event for event in events if event.collision_id in self.active_collisions.keys()
        ]
        for event in actual_events:
            if event.collision_id in self.active_collisions.keys():
                del self.active_collisions[event.collision_id]

        self.__calc_normals()
        self._collision_end(actual_events)

    def _create_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...
    ) -> None:
        if position == ...:
            position = self.position
        if size == ...:
            size = self.size
        if centered == ...:
            centered = self._centered

        collision_root = self.collision_root()
        if collision_root is not None:
            self.__ignore_collision_id.append(collision_root.id)
        self._collision_id = collision_manager.register_entity(
            group_id=self._DEFAULT_COLLISION_GROUP,
            instance=self,
            position=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            ignore_collisions=self.__ignore_collision_id
        )
        if PositionedLogicEntity.__debug_draw_hitboxes:
            self.__debug = PositionedLogicEntity.__debug_entity_class(
                self._runtime_buffer, radius=1
            )

    def collision_root(self) -> PositionedLogicEntity | None:
        if self._DEFAULT_COLLISION_ROOT:
            return self
        if self.parent:
            return self.parent.collision_root()
        return None

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
            group_id=self._DEFAULT_COLLISION_GROUP,
            entity_id=self._collision_id,
            position=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            shift_history=shift_history,
            ignore_collisions=self.__ignore_collision_id
        )
        self._update_size_and_pos_in_runtime_buffer()
        if PositionedLogicEntity.__debug_draw_hitboxes:
            self.__debug.set_points(collision_manager.get_points(self._DEFAULT_COLLISION_GROUP, self._collision_id))

    def _delete_collision(self) -> None:
        if self._collision_id is None:
            return
        collision_manager.delete_entity(self._DEFAULT_COLLISION_GROUP, self._collision_id)
        self._collision_id = None

    def _update_size_and_pos_in_runtime_buffer(self) -> None:
        self._runtime_buffer[self.id].pos_x = self.position.x
        self._runtime_buffer[self.id].pos_y = self.position.y
        self._runtime_buffer[self.id].size_x = int(self.size.x)
        self._runtime_buffer[self.id].size_y = int(self.size.y)

    # endregion

    # region Methods: Update, Kill
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity
        :param delta: time since the last update
        """
        if self._collision_id is not None:
            self._update_collision()
        else:
            self._update_size_and_pos_in_runtime_buffer()
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