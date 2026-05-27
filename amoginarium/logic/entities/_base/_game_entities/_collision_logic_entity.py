"""
Defines an entity that integrates with the collision manager.

Handles registering, updating, and removing hitboxes, as well as collision callbacks.

| ``Path``: amoginarium/logic/entities/_base/_game_entities/_collision_logic_entity.py
| ``Project``: amoginarium
| ``Created``: 23.04.2026
| ``Authors``: LukasKrah
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from amoginarium.shared import CollisionLogicEntityLike
from amoginarium.shared.utility import get_default

from .._base_entities import PositionedLogicEntity
from .._collision import GameCollisions
from .._debug import DebugCircleEntity, DebugPolygonEntity, DebugRectangleEntity

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, MurderViable
    from amoginarium.shared.collision_detection import CollisionEntityIDType
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionEventIDType
    from amoginarium.shared.collision_detection import CollisionExceptionIDType
    from amoginarium.shared.collision_detection import CollisionGroupIDType
    from amoginarium.shared.collision_detection import CollisionHitboxType
    from amoginarium.shared.utility import Vec2


class CollisionLogicEntity(PositionedLogicEntity, CollisionLogicEntityLike):
    """
    A logic entity that supports collision detection and response.

    Integrates with the global collision_manager to handle hitboxes, collision events,
    and collision filtering via exception IDs.

    :cvar __debug_draw_hitboxes: Whether to draw hitboxes for all collision entities.
    :cvar _DEFAULT_COLLISION_EXCEPTION_ROOT: Default value for
        self.__collision_exception_root, which defines whether this entity
        starts a new collision exception group for itself and its children.
        Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE: Default value for
        self.__collision_exception_root_additive, which defines whether root collision
         exception rules created from parents are also added to this entity and its
         children recursive. Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_GROUP: Default value for self.__collision_group, which is
        the collision group this entity belongs to.
        Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_HITBOX_TYPE: Default value for
        self._collision_hitbox_type, which overwrites the CollisionGroups' HitboxType.
        Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_AUTO_UPDATE_ENTITY: Default value for
        self._collision_auto_update_entity, which defines whether to
        automatically update the collision entity on self.update.
        Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_REMEMBER_ACTIVE: Default value for
        self._remember_active_collisions, which defines whether to track
        active collision events in a dictionary.
        Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_REMEMBER_ACTIVE_PER_GROUP: Default value for
        self._remember_active_collisions_per_group, which defines whether to track
        active collisions sorted by their collision group.
        Per Instance values can be set on init.
    :cvar _DEFAULT_COLLISION_REMEMBER_ACTIVE_NORMALS: Default value for
        self._remember_active_normals, which defines whether to pre-calculate and
        store collision normals.
        Per Instance values can be set on init.

    :ivar _parent: The parent entity of this entity, optional.
    :ivar _children: List of all children that this entity is the parent to.
    :ivar _centered: Whether the position is center or top left.
    :ivar __collision_entity_id: Private ID assigned by the collision manager.
    :ivar __collision_group: The collision group this entity belongs to.
    :ivar _collision_exception_ids: List of specific entity IDs to ignore.
    :ivar __collision_exception_root: Whether this entity starts a new exception group.
    :ivar __collision_exception_root_additive: Whether to inherit parent exceptions.
    :ivar __collision_exception_root_ids: Calculated exception IDs for this branch.
    :ivar _collision_active: Whether collision detection is currently enabled.
    :ivar _collision_auto_update_entity: Whether to automatically update the collision
        entity on self.update.
    :ivar _collision_hitbox_type: Overwrite the CollisionGroups' HitboxType.
        If set to None, it's not overwritten.
    :ivar _collision_remember_active_collisions: Whether to remember active collision
        events.
    :ivar _collision_active_collisions: Mapping of current active collision events.
        Must be activated on the class or init.
    :ivar _collision_remember_active_collisions_per_group: Whether to remember
        active collision, sorted by group.
    :ivar _collision_active_collisions_per_group: Mapping of active collisions
        by collision group. Must be activated on the class or init.
    :ivar _collision_remember_active_normals: Whether to remember active normals,
        sorted by group.
    :ivar _collision_active_normals: Mapping of collision normals grouped by collision
        group. Must be activated on the class or init.
    :ivar __collision_debug_entity: Reference to the debug visual for the hitbox.
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
        "_collision_auto_update_entity",
        "_collision_hitbox_type",
        "_collision_remember_active_collisions",
        "_collision_active_collisions",
        "_collision_remember_active_collisions_per_group",
        "_collision_active_collisions_per_group",
        "_collision_remember_active_normals",
        "_collision_active_normals",
        "__collision_debug_entity",
    )

    # region ClassVars
    __debug_draw_hitboxes: tp.ClassVar[bool] = False

    _DEFAULT_COLLISION_EXCEPTION_ROOT: tp.ClassVar[bool] = False
    _DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE: tp.ClassVar[bool] = True
    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionGroupIDType | None] = None
    _DEFAULT_COLLISION_HITBOX_TYPE: tp.ClassVar[CollisionHitboxType | None] = None
    _DEFAULT_COLLISION_AUTO_UPDATE_ENTITY: tp.ClassVar[bool] = True

    _DEFAULT_COLLISION_REMEMBER_ACTIVE: tp.ClassVar[bool] = False
    _DEFAULT_COLLISION_REMEMBER_ACTIVE_PER_GROUP: tp.ClassVar[bool] = False
    _DEFAULT_COLLISION_REMEMBER_ACTIVE_NORMALS: tp.ClassVar[bool] = False
    # endregion

    # region InstanceVars
    _parent: CollisionLogicEntity | None
    _children: list[CollisionLogicEntity]
    _centered: bool

    __collision_entity_id: CollisionEntityIDType | None
    __collision_group: CollisionGroupIDType | None
    _collision_exception_ids: list[CollisionExceptionIDType]
    __collision_exception_root: bool
    __collision_exception_root_additive: bool
    __collision_exception_root_ids: list[CollisionExceptionIDType]
    _collision_active: bool
    _collision_hitbox_type: CollisionHitboxType | None
    _collision_auto_update_entity: bool

    _collision_remember_active_collisions: bool
    _collision_active_collisions: dict[CollisionEventIDType, CollisionEvent]
    _collision_remember_active_collisions_per_group: bool
    _collision_active_collisions_per_group: dict[
        CollisionGroupIDType, list[CollisionEvent]
    ]
    _collision_remember_active_normals: bool
    _collision_active_normals: dict[CollisionGroupIDType, list[Vec2]]

    __collision_debug_entity: (
        DebugCircleEntity | DebugPolygonEntity | DebugRectangleEntity | None
    )
    # endregion

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
        collision_hitbox_type: CollisionHitboxType | EllipsisType | None = ...,
        collision_auto_update_entity: bool | EllipsisType = ...,
        collision_remember_active_collisions: bool | EllipsisType = ...,
        collision_remember_active_collisions_per_group: bool | EllipsisType = ...,
        collision_remember_active_normals: bool | EllipsisType = ...,
    ) -> None:
        """
        Create a logic entity with position, size, and optional collision detection.

        :param runtime_buffer: Logic runtime buffer.
        :param size: 2D size of the entity.
        :param position: 2D position of the entity.
        :param parent: Optional parent entity.
        :param centered: Whether the position is center or top left.
            (relevant for collision detection) Edit afterward with self._centered
        :param collision_group: Collision Group ID.
            Defaults to cls._DEFAULT_COLLISION_GROUP.
        :param collision_exception_ids: Optional list of collision exception rules.
            Edit afterward with self._collision_exception_ids
        :param collision_exception_root: Groups this entity
            and all its children recursive to a collision exception rule.
            Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT.
        :param collision_exception_root_additive: Whether root collision exception rules
            created from parents are also added to this entity and its children
            recursive. Defaults to cls._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE.
            Recurses until the next parents sets this to false
        :param collision_active: Whether the collision detection is active.
        :param collision_hitbox_type: Overwrite the CollisionGroups' HitboxType.
            If set to None, it's not overwritten.
            Defaults to cls._DEFAULT_COLLISION_HITBOX_TYPE.
        :param collision_auto_update_entity: Whether to automatically update the
            collision entity on self.update.
            Defaults to cls._DEFAULT_COLLISION_AUTO_UPDATE_ENTITY.
        :param collision_remember_active_collisions: Whether to remember active
            collision events. Defaults to cls._DEFAULT_COLLISION_REMEMBER_ACTIVE.
        :param collision_remember_active_collisions_per_group: Whether to remember
            active collision, sorted by group.
            Defaults to cls._DEFAULT_COLLISION_REMEMBER_ACTIVE_PER_GROUP.
        :param collision_remember_active_normals: Whether to remember active normals,
            sorted by group. Defaults to cls._DEFAULT_COLLISION_REMEMBER_ACTIVE_NORMALS.
        """
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            position=position,
            size=size,
        )

        self._centered = centered
        self.__collision_entity_id = None

        self._collision_active = collision_active
        self._collision_exception_ids = []
        self.__collision_exception_root_ids = []

        if collision_exception_ids is not None:
            if isinstance(collision_exception_ids, int):
                self._collision_exception_ids = [collision_exception_ids]
            elif isinstance(collision_exception_ids, list):
                self._collision_exception_ids = collision_exception_ids

        self._collision_active_collisions = {}
        self._collision_active_collisions_per_group = {}
        self._collision_active_normals = {}

        self.__collision_debug_entity = None

        # ruff: disable[SLF001]
        self.__collision_group = get_default(
            collision_group,
            self.__class__._DEFAULT_COLLISION_GROUP,
        )

        self.__collision_exception_root = get_default(
            collision_exception_root,
            self.__class__._DEFAULT_COLLISION_EXCEPTION_ROOT,
        )
        self.__collision_exception_root_additive = get_default(
            collision_exception_root_additive,
            self.__class__._DEFAULT_COLLISION_EXCEPTION_ROOT_ADDITIVE,
        )

        self._collision_hitbox_type = get_default(
            collision_hitbox_type,
            self.__class__._DEFAULT_COLLISION_HITBOX_TYPE,
        )

        self._collision_auto_update_entity = get_default(
            collision_auto_update_entity,
            self.__class__._DEFAULT_COLLISION_AUTO_UPDATE_ENTITY,
        )

        self._collision_remember_active_collisions = get_default(
            collision_remember_active_collisions,
            self.__class__._DEFAULT_COLLISION_REMEMBER_ACTIVE,
        )

        self._collision_remember_active_collisions_per_group = get_default(
            collision_remember_active_collisions_per_group,
            self.__class__._DEFAULT_COLLISION_REMEMBER_ACTIVE_PER_GROUP,
        )

        self._collision_remember_active_normals = get_default(
            collision_remember_active_normals,
            self.__class__._DEFAULT_COLLISION_REMEMBER_ACTIVE_NORMALS,
        )
        # ruff: enable[SLF001]

    # region Class-Methods
    @classmethod
    def debug_draw_hitboxes(cls, *, value: bool) -> None:
        """
        Enable or disable global debug rendering for hitboxes.

        :param value: True to enable, False to disable.
        """
        cls.__debug_draw_hitboxes = value

    # endregion

    # region Properties
    @property
    def _collision_entity_id(self) -> CollisionEntityIDType | None:
        """:return: Collision Entity ID or None if no collision not created."""
        return self.__collision_entity_id

    @property
    def _collision_group(self) -> CollisionGroupIDType | None:
        """:return: Collision Group ID."""
        return self.__collision_group

    # endregion

    # region Methods: Collision calculations
    @property
    def _collision_exception_root_ids(self) -> list[CollisionExceptionIDType]:
        """Returns root collision exceptions rules."""
        return self.__collision_exception_root_ids

    @_collision_exception_root_ids.setter
    def _collision_exception_root_ids(
        self, value: list[CollisionExceptionIDType]
    ) -> None:
        """Set root collision exceptions rules."""
        self.__collision_exception_root_ids = value
        for child in self._children:
            child._calculate_root_collision_exceptions()  # noqa: SLF001

    def _calculate_root_collision_exceptions(
        self,
    ) -> list[CollisionExceptionIDType] | None:
        """Calculate root collision exceptions rules."""
        collision_exception_root_ids: list[CollisionExceptionIDType] = []

        if self.__collision_exception_root:
            collision_exception_root_ids.append(GameCollisions.add_exception())

        if self.__collision_exception_root_additive and self._parent is not None:
            # ruff: disable[SLF001]
            collision_exception_root_ids += self._parent._collision_exception_root_ids
            # ruff: enable[SLF001]

        self._collision_exception_root_ids = collision_exception_root_ids

    def _change_parent(self, parent: CollisionLogicEntity | None) -> None:
        """
        Change parent and update root collision exceptions down the tree.

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
        Collision start callback.

        :param group_id: ID of the other group involved in the collision.
        :param events: All details regarding the collisions.
        :return: List of booleans stating whether each collision is accepted.
           If false, the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again
           if there still is a collision in the next update.
        """

    @tp.final
    def collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntity]],
    ) -> list[bool] | None:
        """
        Collision start callback, called by the collision manager.

        Shouldn't be overwritten in inheritance. Instead, use _collision_start

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        :return: List of booleans stating whether each collision is accepted.
           If false, the CollisionManager will not call COLLISION_END
           and will call COLLISION_START again
           if there still is a collision in the next update.
        """
        collisions_result: list[bool] | None = self._collision_start(group_id, events)

        # Save accepted collisions in self._active_collisions
        for i in range(len(events)):
            if collisions_result is not None and not collisions_result[i]:
                continue
            event = events[i]

            if self._collision_remember_active_collisions:
                self._collision_active_collisions[event.collision_id] = event

            if self._collision_remember_active_normals:
                if event.group_id not in self._collision_active_normals:
                    self._collision_active_normals[event.group_id] = []
                self._collision_active_normals[event.group_id].append(event.normal)

            if self._collision_remember_active_collisions_per_group:
                if event.group_id not in self._collision_active_collisions_per_group:
                    self._collision_active_collisions_per_group[event.group_id] = []
                self._collision_active_collisions_per_group[event.group_id].append(
                    event
                )

        if self._collision_auto_update_entity:
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
        Collision end callback.

        :param group_id: ID of the other group involved in the collision.
        :param events: All details regarding the collisions.
        """

    @tp.final
    def collision_end(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[CollisionLogicEntity]],
    ) -> None:
        """
        Collision end callback, called by the collision manager.

        :param group_id: ID of the other group involved in the collision.
        :param events: All details regarding the collisions.
        """
        if (
            self._collision_remember_active_collisions
            or self._collision_remember_active_collisions_per_group
            or self._collision_remember_active_normals
        ):
            for event in events:
                if (
                    self._collision_remember_active_collisions
                    and event.collision_id in self._collision_active_collisions
                ):
                    del self._collision_active_collisions[event.collision_id]
                if (
                    self._collision_remember_active_normals
                    and event.group_id in self._collision_active_normals
                    and event.normal in self._collision_active_normals[event.group_id]
                ):
                    self._collision_active_normals[event.group_id].remove(event.normal)
                if (
                    self._collision_remember_active_collisions_per_group
                    and event.group_id in self._collision_active_collisions_per_group
                    and event
                    in self._collision_active_collisions_per_group[event.group_id]
                ):
                    self._collision_active_collisions_per_group[event.group_id].remove(
                        event
                    )

        self._collision_end(group_id, events)

    # endregion

    # region Methods: Create/Update/Delete Collision
    # noinspection DuplicatedCode
    @tp.final
    def _create_collision(
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
        Register this entity with the collision manager.

        :param position: The 2D position for the hitbox. Defaults to self.position.
        :param size: The 2D size for the hitbox. Defaults to self.size.
        :param rotation: Rotation of the hitbox in radians.
        :param positions: Optional list of vertices for polygonal hitboxes.
        :param centered: Whether the hitbox is centered on the position.
        :param radius: Optional radius for circular hitboxes.
        :param collision_active: Whether the collision entity is active.
            Defaults to self._collision_active.
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
            ignore_collisions=self._collision_exception_ids  # type: ignore[pycharm]
            + self.__collision_exception_root_ids,
            is_active=collision_active,
        )

    # noinspection DuplicatedCode
    def _update_collision(  # noqa: C901, PLR0912
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
        Update the entity's hitbox parameters in the collision manager.

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

            if self.__collision_debug_entity is None:
                match hitbox:
                    case "aabb":
                        self.__collision_debug_entity = DebugRectangleEntity(
                            runtime_buffer=self._runtime_buffer,
                            position=self.position,
                            size=self.size,
                        )
                    case "circle":
                        self.__collision_debug_entity = DebugCircleEntity(
                            runtime_buffer=self._runtime_buffer,
                            position=self.position,
                            radius=self.size.x / 2,
                        )
                    case _:
                        self.__collision_debug_entity = DebugPolygonEntity(
                            runtime_buffer=self._runtime_buffer,
                        )
            if self.__collision_debug_entity is None:
                return
            collision_group: CollisionGroupIDType | None = self._collision_group
            if collision_group is not None and self.__collision_entity_id is not None:
                self.__collision_debug_entity.show()
                match hitbox:
                    case "aabb":
                        debug_pos: Vec2 | None = (
                            GameCollisions.collision_manager.get_position(
                                collision_group, self.__collision_entity_id
                            )
                        )
                        if debug_pos is not None:
                            self.__collision_debug_entity.position = debug_pos
                        debug_size: Vec2 | None = (
                            GameCollisions.collision_manager.get_size(
                                collision_group, self.__collision_entity_id
                            )
                        )
                        if debug_size is not None:
                            self.__collision_debug_entity.size = debug_size

                    case "circle":
                        debug_pos = GameCollisions.collision_manager.get_position(
                            collision_group, self.__collision_entity_id
                        )
                        if debug_pos is not None:
                            self.__collision_debug_entity.position = debug_pos
                        debug_radius = GameCollisions.collision_manager.get_radius(
                            collision_group, self.__collision_entity_id
                        )
                        if debug_radius is not None:
                            self.__collision_debug_entity.radius = debug_radius

                    case _:
                        # noinspection PyUnresolvedReferences
                        self.__collision_debug_entity.set_points(
                            GameCollisions.collision_manager.get_points(
                                collision_group, self.__collision_entity_id
                            )
                        )

        elif self.__collision_debug_entity is not None:
            self.__collision_debug_entity.hide()

    @tp.final
    def _delete_collision(self) -> None:
        """
        Remove the entity from the collision manager and cleans up debug visuals.
        """
        collision_group: CollisionGroupIDType | None = self._collision_group
        if self.__collision_entity_id is None or collision_group is None:
            return
        GameCollisions.collision_manager.delete_entity(
            collision_group, self.__collision_entity_id
        )
        self.__collision_entity_id = None
        if self.__collision_debug_entity is not None:
            self.__collision_debug_entity.kill()

    # endregion

    # region Methods: General Update & Kill
    @tp.override
    def _update(self, delta: float) -> None:
        """
        Update shared memory and collision entity.

        :param delta: Time since the last update.
        """
        if self._collision_auto_update_entity:
            self._update_collision()
        super()._update(delta)

    @tp.override
    def _kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> None:
        """
        Kill the entity and all its children.

        :param killed_by: Who killed this entity.
        :param kill_children: Whether to kill children as well recursively.
        """
        self._delete_collision()
        super()._kill(killed_by=killed_by, kill_children=kill_children)

    # endregion
