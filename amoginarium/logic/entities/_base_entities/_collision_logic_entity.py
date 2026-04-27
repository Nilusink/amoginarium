"""
amoginarium/logic/entities/_base_entities/_collision_logic_entity.py

Project: amoginarium
Created: 23.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

from icecream import ic
import typing as tp

from amoginarium.shared.utility import get_default

from ._positioned_logic_entity import PositionedLogicEntity
from .._collision import collision_manager

if tp.TYPE_CHECKING:
    from types import EllipsisType
    from ctypes import Array

    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared import base_entity_t
    from amoginarium.shared.utility import Vec2

    from ._base_logic_entity import BaseLogicEntity
    from .._debug import PolyDebugRenderingEntity
    from .._collision import CollisionType


class CollisionLogicEntity(PositionedLogicEntity):
    """
    A logic entity that supports collision detection and response.
    Integrates with the global collision_manager to handle hitboxes, collision events,
    and collision filtering via exception IDs.
    """
    __slots__ = (
        "_centered", "__collision_entity_id", "__collision_group", "_collision_exception_ids",
        "__collision_exception_root", "__collision_exception_root_additive", "__collision_exception_root_ids",
        "_active_collisions", "_active_normals", "__debug_entity"
    )

    # region ClassVars
    __debug_draw_hitboxes: tp.ClassVar[bool] = False
    __debug_entity_class: tp.ClassVar[
        type["DebugPolygonEntity"]
    ]

    _DEFAULT_COLLISION_EXCEPTION_ROOT: tp.ClassVar[bool] = False
    _DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE: tp.ClassVar[bool] = True
    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionType.GroupID | None] = None

    # endregion

    # region InstanceVars
    _parent: CollisionLogicEntity | None

    _centered: bool

    __collision_entity_id: CollisionType.EntityID | None  # Private: Shouldn't be changed from the outside
    __collision_group: CollisionType.GroupID | None  # Private: Cannot be changed after creation.
    _collision_exception_ids: list[CollisionType.ExceptionID]  # Can be changed after creation
    __collision_exception_root: bool
    __collision_exception_root_additive: bool
    __collision_exception_root_ids: list[CollisionType.ExceptionID]  # Calculated/Used only internally

    _active_collisions: dict[CollisionType.CollisionID, CollisionEvent]  # protected / no property for faster access
    _active_normals: dict[CollisionType.GroupID, list[Vec2]]  # protected / no property for faster access

    __debug_entity: DebugRectangle | None

    # endregion

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            *,
            parent: CollisionLogicEntity | None = None,
            centered: bool = False,
            collision_group: CollisionType.GroupID | EllipsisType | None = ...,
            collision_exception_ids: list[int] | int | None = None,
            collision_exception_root: bool | EllipsisType = ...,
            collision_exception_root_additive: bool | EllipsisType = ...,
    ) -> None:
        """
        A logic entity with position, size, and optional collision detection
        :param runtime_buffer: Logic runtime buffer
        :param size: 2D size of the entity
        :param position: 2D position of the entity
        :param parent: Optional parent entity
        :param centered: Whether the position is center or top left (relevant for collision detection)
            Edit afterward with self._centered
        :param collision_group: Collision Group ID. Defaults to cls._DEFAULT_COLLISION_GROUP.
        :param collision_exception_ids: Optional list of collision exception rules.
            Edit afterward with self._collision_exception_ids
        :param collision_exception_root: Groups this entity and all its children recursive to a collision exception
            rule. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT.
        :param collision_exception_root_additive: Whether root collision exception rules created from parents are also
            added to this entity and its children recursive. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE.
            Recurses until the next parents sets this to false
        """
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            position=position,
            size=size
        )

        self._centered = centered
        self.__collision_entity_id = None
        self.__collision_group = get_default(collision_group, self.__class__._DEFAULT_COLLISION_GROUP)

        self._collision_exception_ids = []
        if collision_exception_ids is not None:
            if isinstance(collision_exception_ids, int):
                self._collision_exception_ids = [collision_exception_ids]
            elif isinstance(collision_exception_ids, list):
                self._collision_exception_ids = collision_exception_ids
        self.__collision_exception_root = get_default(
            collision_exception_root,
            self.__class__._DEFAULT_COLLISION_EXCEPTION_ROOT
        )
        self.__collision_exception_root_additive = get_default(
            collision_exception_root_additive,
            self.__class__._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE
        )
        self.__collision_exception_root_ids = []

        self._active_collisions = {}
        self._active_normals = {}

        self.__debug_entity = None

    # region Class-Methods
    @classmethod
    def debug_draw_hitboxes(cls, value: bool) -> None:
        """
        Enables or disables global debug rendering for hitboxes.
        :param value: True to enable, False to disable.
        """
        cls.__debug_draw_hitboxes = value

    @classmethod
    def debug_entity_class(cls, value: type[PolyDebugRenderingEntity]) -> None:
        """
        Sets the class used for rendering debug hitboxes.
        :param value: A subclass of DebugPolygonEntity.
        """
        cls.__debug_entity_class = value

    # endregion

    # region Properties
    @property
    def _collision_entity_id(self) -> CollisionType.EntityID | None:
        """:return: Collision Entity ID or None if no collision not created"""
        return self.__collision_entity_id

    @property
    def _collision_group(self) -> CollisionType.GroupID | None:
        """:return: Collision Group ID"""
        return self.__collision_group

    @property
    def _collision_exception_root_ids(self) -> list[CollisionType.ExceptionID]:
        """:return: Root Collision exceptions rules. Maybe an empty list if they haven't been calculated yet"""
        return self.__collision_exception_root_ids

    # endregion

    # region Methods: Collision calculations
    def __calculate_active_normals(self) -> None:
        """Pre-calculates active normals grouped by collision group ID for faster access"""
        active_normals: dict[int, list[Vec2]] = {}

        for event in self._active_collisions.values():
            if event.group_id not in active_normals:
                active_normals[event.group_id] = []
            active_normals[event.group_id].append(event.normal)

        self._active_normals = active_normals

    def _get_root_collision_exceptions(self) -> list[CollisionType.ExceptionID]:
        """Calculates root collision exceptions rules"""
        my_add: list[CollisionType.ExceptionID] = []
        if self.__collision_exception_root:
            my_add.append(self.id)
        # todo: update func - update on tree update
        if self.__collision_exception_root_additive and self._parent is not None:
            return self._parent._get_root_collision_exceptions() + my_add
        return my_add

    # endregion

    # region Methods: Collision Start
    def _collision_start(self, event: list[CollisionEvent[CollisionLogicEntity]]) -> list[bool] | None:
        """
        Called on collision start
        :param event: All details regarding the collisions
        :return: List of bools stating whether each collision is accepted.
           If False the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again if there still is a collision in the next update
        """

    @tp.final
    def collision_start(self, events: list[CollisionEvent[CollisionLogicEntity]]) -> list[bool] | None:
        """
        Callback for collision start, called by the collision manager
        Shouldn't be overwritten in inheritance. Instead, use _collision_start
        :param events: All details regarding the collisions
        :return: List of bools stating whether each collision is accepted.
           If False the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again if there still is a collision in the next update
        """
        # ic(self, [event.other_entity for event in events])
        collisions_result: list[bool] | None = self._collision_start(events)

        # Save accepted collisions in self._active_collisions
        for i in range(len(events)):
            if collisions_result is not None:
                if not collisions_result[i]:
                    continue
            self._active_collisions[events[i].collision_id] = events[i]

        self.__calculate_active_normals()

        self._update_collision(shift_history=False)
        return collisions_result

    # endregion

    # region Methods: Collision End
    def _collision_end(self, events: list[CollisionEvent[CollisionLogicEntity]]) -> None:
        """
        Called on collision end
        :param events: All details regarding the collisions
        """

    @tp.final
    def collision_end(self, events: list[CollisionEvent[CollisionLogicEntity]]) -> None:
        """
        Callback on COLLISION_END, called by the collision manager
        :param events: All details regarding the collisions
        """
        # Filter for collisions that are still active
        actual_events = [
            event for event in events if event.collision_id in self._active_collisions.keys()
        ]
        for event in actual_events:
            if event.collision_id in self._active_collisions.keys():
                del self._active_collisions[event.collision_id]

        self.__calculate_active_normals()
        self._collision_end(actual_events)

    # endregion

    # region Methods: Create/Update/Delete Collision
    @tp.final
    def _create_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...
    ) -> None:
        """
        Registers this entity with the collision manager.

        :param position: The 2D position for the hitbox. Defaults to self.position.
        :param size: The 2D size for the hitbox. Defaults to self.size.
        :param rotation: Rotation of the hitbox in radians.
        :param positions: Optional list of vertices for polygonal hitboxes.
        :param centered: Whether the hitbox is centered on the position.
        """
        if position == ...:
            position = self.position
        if size == ...:
            size = self.size
        if centered == ...:
            centered = self._centered

        self.__collision_exception_root_ids = self._get_root_collision_exceptions()

        self.__collision_entity_id = collision_manager.register_entity(
            group_id=self.__collision_group,
            instance=self,
            position=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            ignore_collisions=self._collision_exception_ids
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
        """
        Updates the entity's hitbox parameters in the collision manager.

        :param position: New 2D position.
        :param size: New 2D size.
        :param rotation: New rotation in radians.
        :param positions: New list of vertices for polygonal hitboxes.
        :param centered: Whether the hitbox is centered.
        :param shift_history: Whether to update the previous position state for CCD.
        """
        if self.__collision_entity_id is None:
            return

        if position == ...:
            position = self.position
        if size == ...:
            size = self.size
        if centered == ...:
            centered = self._centered

        collision_manager.update_entity(
            group_id=self._DEFAULT_COLLISION_GROUP,
            entity_id=self.__collision_entity_id,
            position=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            shift_history=shift_history,
        )
        if CollisionLogicEntity.__debug_draw_hitboxes:
            if self.__debug_entity is None:
                self.__debug_entity = CollisionLogicEntity.__debug_entity_class(
                    self._runtime_buffer, radius=1
                )
            self.__debug_entity.set_points(
                collision_manager.get_points(self._DEFAULT_COLLISION_GROUP, self.__collision_entity_id)
            )

    @tp.final
    def _delete_collision(self) -> None:
        """
        Removes the entity from the collision manager and cleans up debug visuals.
        """
        if self.__collision_entity_id is None:
            return
        collision_manager.delete_entity(self._DEFAULT_COLLISION_GROUP, self.__collision_entity_id)
        self.__collision_entity_id = None
        if self.__debug_entity is not None:
            self.__debug_entity.kill()

    # endregion

    # region Methods: General Update & Kill
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity
        :param delta: time since the last update
        """
        self._update_collision()
        super()._update(delta)

    def _kill(self, killed_by: BaseLogicEntity | EllipsisType = ...) -> None:
        """
        Remove from groups and collision manager
        :param killed_by: who killed this entity
        """
        self._delete_collision()
        super()._kill(killed_by)

    # endregion