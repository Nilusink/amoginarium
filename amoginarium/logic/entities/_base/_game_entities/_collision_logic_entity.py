"""
Defines an entity that integrates with the collision manager.

Handles registering, updating, and removing hitboxes, as well as collision callbacks.

Path: amoginarium/logic/entities/_base/_game_entities/_collision_logic_entity.py
Project: amoginarium
Created: 23.04.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from icecream import ic

from amoginarium.shared import CollisionLogicEntityLike, MurderViable
from amoginarium.shared.utility import get_default

from .._base_entities import PositionedLogicEntity
from .._collision import GameCollisions
from .._debug import DebugCircleEntity, DebugPolygonEntity, DebugRectangleEntity

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.collision_detection import CollisionEntityIDType
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionEventIDType
    from amoginarium.shared.collision_detection import CollisionExceptionIDType
    from amoginarium.shared.collision_detection import CollisionGroupIDType
    from amoginarium.shared.collision_detection import CollisionHitboxType
    from amoginarium.shared.utility import Vec2

    from .._base_entities import BaseLogicEntity


class CollisionLogicEntity(PositionedLogicEntity, CollisionLogicEntityLike):
    """
    A logic entity that supports collision detection and response.
    Integrates with the global collision_manager to handle hitboxes, collision events,
    and collision filtering via exception IDs.
    """

    __slots__ = (
        "_centered",
        "__collision_entity_id",
        "__collision_group",
        "_collision_exception_ids",
        "__collision_exception_root",
        "__collision_exception_root_additive",
        "__collision_exception_root_ids",
        "_collision_active",
        "_active_collisions",
        "_active_normals",
        "__debug_entity",
    )

    # region ClassVars
    __debug_draw_hitboxes: tp.ClassVar[bool] = False

    _DEFAULT_COLLISION_EXCEPTION_ROOT: tp.ClassVar[bool] = False
    _DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE: tp.ClassVar[bool] = True
    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionGroupIDType | None] = None

    # endregion

    # region InstanceVars
    _parent: CollisionLogicEntity | None
    _children: list[CollisionLogicEntity]

    _centered: bool

    __collision_entity_id: (
        CollisionEntityIDType | None
    )  # Private: Shouldn't be changed from the outside
    __collision_group: (
        CollisionGroupIDType | None
    )  # Private: Cannot be changed after creation.
    _collision_exception_ids: list[
        CollisionExceptionIDType
    ]  # Can be changed after creation
    __collision_exception_root: bool
    __collision_exception_root_additive: bool
    __collision_exception_root_ids: list[
        CollisionExceptionIDType
    ]  # Calculated/Used only internally
    _collision_active: bool

    _active_collisions: dict[
        CollisionEventIDType, CollisionEvent
    ]  # protected / no property for faster access
    _active_normals: dict[
        CollisionGroupIDType, list[Vec2]
    ]  # protected / no property for faster access

    __debug_entity: (
        DebugCircleEntity | DebugPolygonEntity | DebugRectangleEntity | None
    )  # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        size: Vec2,
        position: Vec2,
        *,
        parent: CollisionLogicEntity | None = None,
        centered: bool = False,
        collision_group: CollisionGroupIDType | EllipsisType | None = ...,
        collision_exception_ids: list[int] | int | None = None,
        collision_exception_root: bool | EllipsisType = ...,
        collision_exception_root_additive: bool | EllipsisType = ...,
        collision_active: bool = True,
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
        :param collision_active: Whether the collision detection is active.
        """
        super().__init__(
            runtime_buffer=runtime_buffer, parent=parent, position=position, size=size
        )

        self._centered = centered
        self.__collision_entity_id = None
        self.__collision_group = get_default(
            collision_group, self.__class__._DEFAULT_COLLISION_GROUP
        )

        self._collision_exception_ids = []
        if collision_exception_ids is not None:
            if isinstance(collision_exception_ids, int):
                self._collision_exception_ids = [collision_exception_ids]
            elif isinstance(collision_exception_ids, list):
                self._collision_exception_ids = collision_exception_ids
        self.__collision_exception_root = get_default(
            collision_exception_root, self.__class__._DEFAULT_COLLISION_EXCEPTION_ROOT
        )
        self.__collision_exception_root_additive = get_default(
            collision_exception_root_additive,
            self.__class__._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE,
        )
        self.__collision_exception_root_ids = []

        self._collision_active = collision_active

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

    # endregion

    # region Properties
    @property
    def _collision_entity_id(self) -> CollisionEntityIDType | None:
        """:return: Collision Entity ID or None if no collision not created"""
        return self.__collision_entity_id

    @property
    def _collision_group(self) -> CollisionGroupIDType | None:
        """:return: Collision Group ID"""
        return self.__collision_group

    # endregion

    # region Methods: Collision calculations
    def __calculate_active_normals(self) -> None:
        """Pre-calculates active normals grouped by collision group ID for faster access."""
        active_normals: dict[int, list[Vec2]] = {}

        for event in self._active_collisions.values():
            if event.group_id not in active_normals:
                active_normals[event.group_id] = []
            active_normals[event.group_id].append(event.normal)

        self._active_normals = active_normals

    @property
    def _collision_exception_root_ids(self) -> list[CollisionExceptionIDType]:
        """Returns root collision exceptions rules."""
        return self.__collision_exception_root_ids

    @_collision_exception_root_ids.setter
    def _collision_exception_root_ids(
        self, value: list[CollisionExceptionIDType]
    ) -> None:
        """Sets root collision exceptions rules."""
        self.__collision_exception_root_ids = value
        for child in self._children:
            child._calculate_root_collision_exceptions()

    def _calculate_root_collision_exceptions(
        self,
    ) -> list[CollisionExceptionIDType] | None:
        """Calculates root collision exceptions rules."""
        collision_exception_root_ids: list[CollisionExceptionIDType] = []

        if self.__collision_exception_root:
            collision_exception_root_ids.append(GameCollisions.add_exception())

        if self.__collision_exception_root_additive and self._parent is not None:
            collision_exception_root_ids += self._parent._collision_exception_root_ids

        self._collision_exception_root_ids = collision_exception_root_ids

    def _change_parent(self, parent: CollisionLogicEntity | None) -> None:
        """
        Change parent and update root collision exceptions down the tree
        :param parent: New parent.
        """
        self._parent = parent
        self._calculate_root_collision_exceptions()

    # endregion

    # region Methods: Collision Start
    def _collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntity]],
    ) -> list[bool] | None:
        """
        Called on collision start
        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collisions
        :return: List of booleans stating whether each collision is accepted.
           If false, the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again
           if there still is a collision in the next update
        """

    @tp.final
    def collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntity]],
    ) -> list[bool] | None:
        """
        Callback for collision start, called by the collision manager.
        Shouldn't be overwritten in inheritance. Instead, use _collision_start
        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        :return: List of booleans stating whether each collision is accepted.
           If false, the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again
           if there still is a collision in the next update
        """
        # ic("COL START", self, events)
        collisions_result: list[bool] | None = self._collision_start(group_id, events)

        # Save accepted collisions in self._active_collisions
        for i in range(len(events)):
            if collisions_result is not None and not collisions_result[i]:
                continue
            self._active_collisions[events[i].collision_id] = events[i]

        self.__calculate_active_normals()

        self._update_collision(shift_history=False)
        return collisions_result

    # endregion

    # region Methods: Collision End
    def _collision_end(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntity]],
    ) -> None:
        """
        Called on collision end
        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collisions
        """

    @tp.final
    def collision_end(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntity]],
    ) -> None:
        """
        Callback on COLLISION_END, called by the collision manager
        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collisions
        """
        # ic("COL END", self, events)
        # Filter for collisions that are still active
        actual_events = [
            event
            for event in events
            if event.collision_id in self._active_collisions.keys()
        ]
        for event in actual_events:
            if event.collision_id in self._active_collisions.keys():
                del self._active_collisions[event.collision_id]

        self.__calculate_active_normals()
        self._collision_end(group_id, actual_events)

    # endregion

    # region Methods: Create/Update/Delete Collision
    @tp.final
    def _create_collision(  # type: ignore
        self,
        *,
        position: Vec2 | EllipsisType = ...,
        size: Vec2 | EllipsisType = ...,
        rotation: float = 0.0,
        positions: list[Vec2] | None = None,
        centered: bool | EllipsisType = ...,
        radius: float | None = None,
        collision_active: bool | EllipsisType = ...,
    ) -> None:
        """
        Registers this entity with the collision manager.
        :param position: The 2D position for the hitbox. Defaults to self.position.
        :param size: The 2D size for the hitbox. Defaults to self.size.
        :param rotation: Rotation of the hitbox in radians.
        :param positions: Optional list of vertices for polygonal hitboxes.
        :param centered: Whether the hitbox is centered on the position.
        :param radius: Optional radius for circular hitboxes.
        :param collision_active: Whether the collision entity is active.
            Defaults to self._collision_active
        """
        if self.__collision_group is None:
            return
        if isinstance(position, EllipsisType):
            position = self.position
            position: Vec2
        if isinstance(size, EllipsisType):
            size = self.size
            size: Vec2
        if isinstance(centered, EllipsisType):
            centered = self._centered
            centered: bool
        if isinstance(collision_active, EllipsisType):
            collision_active = self._collision_active
            collision_active: bool

        self._calculate_root_collision_exceptions()

        self.__collision_entity_id = GameCollisions.collision_manager.register_entity(
            group_id=self.__collision_group,
            instance=self,
            position=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            radius=radius,
            ignore_collisions=self._collision_exception_ids
            + self.__collision_exception_root_ids,
            is_active=collision_active,
        )

    def _update_collision(  # type: ignore
        self,
        *,
        position: Vec2 | EllipsisType = ...,
        size: Vec2 | EllipsisType = ...,
        rotation: float = 0.0,
        positions: list[Vec2] | None = None,
        centered: bool | EllipsisType = ...,
        radius: float | None = None,
        collision_active: bool | EllipsisType = ...,
        shift_history: bool = True,
    ) -> None:
        """
        Updates the entity's hitbox parameters in the collision manager.
        :param position: The 2D position for the hitbox. Defaults to self.position.
        :param size: The 2D size for the hitbox. Defaults to self.size.
        :param rotation: Rotation of the hitbox in radians.
        :param positions: Optional list of vertices for polygonal hitboxes.
        :param centered: Whether the hitbox is centered on the position.
        :param radius: Optional radius for circular hitboxes.
        :param collision_active: Whether the collision entity is active.
            Defaults to self._collision_active.
        :param shift_history: Whether to update the previous position state for CCD.
        """
        if self.__collision_entity_id is None or self.__collision_group is None:
            return
        if isinstance(position, EllipsisType):
            position = self.position
            position: Vec2
        if isinstance(size, EllipsisType):
            size = self.size
            size: Vec2
        if isinstance(centered, EllipsisType):
            centered = self._centered
            centered: bool
        if isinstance(collision_active, EllipsisType):
            collision_active = self._collision_active
            collision_active: bool

        GameCollisions.collision_manager.update_entity(
            group_id=self.__collision_group,
            entity_id=self.__collision_entity_id,
            position=position,
            size=size,
            rotation=rotation,
            positions=positions,
            centered=centered,
            radius=radius,
            is_active=collision_active,
            ignore_collisions=self._collision_exception_ids
            + self.__collision_exception_root_ids,
            shift_history=shift_history,
        )
        if CollisionLogicEntity.__debug_draw_hitboxes and self._collision_active:
            hitbox: CollisionHitboxType = GameCollisions.hitboxes[
                self.__collision_group
            ]

            if self.__debug_entity is None:
                match hitbox:
                    case CollisionHitboxType.aabb:
                        self.__debug_entity = DebugRectangleEntity(
                            runtime_buffer=self._runtime_buffer,
                            position=self.position,
                            size=self.size,
                        )
                    case CollisionHitboxType.circle:
                        self.__debug_entity = DebugCircleEntity(
                            runtime_buffer=self._runtime_buffer,
                            position=self.position,
                            radius=self.size.x / 2,
                        )
                    case _:
                        self.__debug_entity = DebugPolygonEntity(
                            runtime_buffer=self._runtime_buffer,
                        )
            if self.__debug_entity is None:
                return
            collision_group: CollisionGroupIDType | None = self._collision_group
            if collision_group is not None and self.__collision_entity_id is not None:
                self.__debug_entity.show()
                match hitbox:
                    case CollisionHitboxType.aabb:
                        debug_pos: Vec2 | None = (
                            GameCollisions.collision_manager.get_position(
                                collision_group, self.__collision_entity_id
                            )
                        )
                        if debug_pos is not None:
                            self.__debug_entity.position = debug_pos
                        debug_size: Vec2 | None = (
                            GameCollisions.collision_manager.get_size(
                                collision_group, self.__collision_entity_id
                            )
                        )
                        if debug_size is not None:
                            self.__debug_entity.size = debug_size

                    case CollisionHitboxType.circle:
                        debug_pos = GameCollisions.collision_manager.get_position(
                            collision_group, self.__collision_entity_id
                        )
                        if debug_pos is not None:
                            self.__debug_entity.position = debug_pos
                        debug_radius = GameCollisions.collision_manager.get_radius(
                            collision_group, self.__collision_entity_id
                        )
                        if debug_radius is not None:
                            self.__debug_entity.radius = debug_radius

                    case _:
                        self.__debug_entity.set_points(  # type: ignore
                            GameCollisions.collision_manager.get_points(
                                collision_group, self.__collision_entity_id
                            )
                        )

        else:
            if self.__debug_entity is not None:
                self.__debug_entity.hide()

    @tp.final
    def _delete_collision(self) -> None:
        """
        Removes the entity from the collision manager and cleans up debug visuals.
        """
        collision_group: CollisionGroupIDType | None = self._collision_group
        if self.__collision_entity_id is None or collision_group is None:
            return
        GameCollisions.collision_manager.delete_entity(
            collision_group, self.__collision_entity_id
        )
        self.__collision_entity_id = None
        if self.__debug_entity is not None:
            self.__debug_entity.kill()

    # endregion

    # region Methods: General Update & Kill
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity
        :param delta: time since the last update.
        """
        self._update_collision()
        super()._update(delta)

    def _kill(
        self,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> None:
        """
        Remove from groups and collision manager
        :param killed_by: who killed this entity.
        """
        self._delete_collision()
        super()._kill(killed_by=killed_by, kill_children=kill_children)

    # endregion
