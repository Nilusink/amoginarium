"""
_base_entity.py
28.03.2026

defines the most basic form of logic entity
"""
from __future__ import annotations
from types import EllipsisType
from icecream import ic
from ctypes import Array
import pygame as pg
import typing as tp

from amoginarium.shared import Coalitions, base_entity_t, ENTITY_COUNTER, CIDType
from amoginarium.shared.debugging import print_ic_style, CC
from amoginarium.shared.utility import Vec2, normalize_angle

from ._logic_groups import Updated
from ... import pv


class BaseLogicEntity:
    """most basic type of logics entity"""

    __slots__ = [
        "_parent", "_children", "_lifetime", "__id", "_runtime_buffer", "__g",
    ]

    _children: list[BaseLogicEntity]
    _lifetime: float
    _parent: BaseLogicEntity | None

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: BaseLogicEntity | None = None,
    ) -> None:

        # pygame groups
        self.__g = []

        self._parent = parent
        self._children = []
        self._lifetime = 0

        # data block
        self.__id = ENTITY_COUNTER.get_id()
        self._runtime_buffer = runtime_buffer

        self._set_bit("flags", 0, True)  # set alive
        self._set_bit("flags", 1, True)  # set visible

        self.add(Updated)

    # region properties
    @property
    def id(self) -> int:
        """entity id (+ buffer location)"""
        return self.__id

    @property
    def parent(self) -> BaseLogicEntity | None:
        """entities parent if present"""
        return self._parent

    @property
    def root(self) -> BaseLogicEntity:
        """root entity; entity parent if present else self"""
        if self._parent:
            return self._parent.root

        return self

    @property
    def children(self) -> list[BaseLogicEntity]:
        """all children of entity"""
        return self._children
    # endregion

    # region bitwise fun
    def _set_bit(self, param: str, bit_index: int, value: bool) -> None:
        """
        set (or reset) on specified bit

        :param param: what parameter to set the bit at
        :param bit_index: bit to set
        :param value: what to set the bit to
        """

        # get value from buffer
        attribute = getattr(self._runtime_buffer[self.id], param)

        # set bit (bitwise or)
        if value:
            attribute |= (1 << bit_index)

        # reset bit (bitwise and with inverted mask)
        else:
            attribute &= ~(1 << bit_index)

        # write value to buffer
        setattr(self._runtime_buffer[self.id], param, attribute)

    # endregion

    # region pygame methods
    def add(self, *groups) -> None:
        """
        add entity to one or more groups
        """
        has = self.__g.__contains__

        for group in groups:
            if not has(group):
                group.add_internal(self)
                self.__g.append(group)

    def remove(self, *groups) -> None:
        """
        remove entity from one or more groups
        """
        has = self.__g.__contains__

        for group in groups:
            if has(group):
                group.remove_internal(self)
                self.__g.remove(group)

    def kill(self, killed_by=...) -> None:
        """
        remove entity from all groups
        """
        # kill children first
        for child in self._children:
            child.kill()

        # commit suicide
        for group in self.__g:
            group.remove_internal(self)

        self._set_bit("flags", 0, False)  # set alive
        ENTITY_COUNTER.pop_id(self.__id)

        self.__g.clear()

    # endregion

    # region update methods
    def _update(self, delta: float) -> None:
        """
        actual update function for the entity
        """
        self._lifetime += delta

    @tp.final
    def update(self, delta: float, recursive: bool = True) -> None:
        """
        update entity and their children
        """
        self._update(delta)

        if recursive:
            for child in self._children:
                update = getattr(child, "update", lambda _: ...)
                update(delta)
    # endregion

    # region visibility
    def show(self) -> None:
        """
        set visibility to 1
        """
        self._set_bit("flags", 1, True)

    def hide(self) -> None:
        """
        set visibility to 0
        """
        self._set_bit("flags", 1, False)

    def highlight(self) -> None:
        """highlight the graphics entity"""
        self._set_bit("flags", 2, True)

    def stop_highlight(self) -> None:
        """stop highlighting the graphics entity"""
        self._set_bit("flags", 2, False)

    # endregion


class PositionedLogicEntity(BaseLogicEntity):
    """a logic entity with position and size"""

    # don't use properties for position and size for faster access
    __slots__ = ["position", "size"]

    _cid: CIDType | EllipsisType = ...  # for serialization
    position: Vec2
    size: Vec2

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            parent: BaseLogicEntity | None = None,
    ) -> None:
        super().__init__(runtime_buffer=runtime_buffer, parent=parent)
        self.position = position
        self.size = size

    # region class methods
    @classmethod
    def cid(cls) -> CIDType:
        """
        :return: the entities' component ID 
        """
        if isinstance(cls._cid, EllipsisType):
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._cid
    # endregion

    def _update(self, delta: float) -> None:
        # update shared memory
        self._runtime_buffer[self.id].pos_x = self.position.x
        self._runtime_buffer[self.id].pos_y = self.position.y
        self._runtime_buffer[self.id].size_x = int(self.size.x)
        self._runtime_buffer[self.id].size_y = int(self.size.y)

        super()._update(delta)


class LogicGameEntity(PositionedLogicEntity):
    __slots__ = [
        "facing", "velocity", "acceleration", "_coalition", "_velocity_to_add",
        "_acceleration_to_add", "mask", "rect", "__world_position"
    ]

    mask: pg.Mask
    rect: pg.Rect
    facing: Vec2
    velocity: Vec2
    acceleration: Vec2

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            size: Vec2,
            position: Vec2,
            initial_velocity: Vec2 | None = None,
            parent: LogicGameEntity | None = None,
            coalition: Coalitions | EllipsisType = ...
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            parent=parent
        )
        # region default parameters
        self._velocity_to_add = Vec2()
        self._acceleration_to_add = Vec2()

        if not initial_velocity:
            self.velocity = Vec2()

        else:
            self.velocity = initial_velocity

        if coalition is ...:
            self._coalition = Coalitions.neutral

        else:
            self._coalition = coalition

        self.update_rect()
        self._generate_collision_mask()

        self.acceleration = Vec2()
        self.__world_position = Vec2()  # actual world position
        self.facing = Vec2().from_polar(0, 1)
        # endregion

    # region properties
    @property
    def world_position(self) -> Vec2:
        """entity position on screen"""
        return self.position - self.__world_position

    @property
    def is_bullet(self) -> bool:
        """no"""
        return False

    @property
    def coalition(self) -> Coalitions:
        """which coalition the entity belongs to"""
        return self._coalition

    @property
    def serializable(self) -> bool:
        """whether the entity is serializable or not"""
        return self._cid is not ...

    # endregion

    # region methods
    def to_dict(self) -> dict | None:
        """convert the entity to a dict if possible"""
        if not self.serializable:
            print_ic_style(
                f"{CC.fg.RED}Entity of type {self.__class__.__name__} is not"
                f"serializable{CC.ctrl.ENDL}",
            )

        return {
            "type": self.cid(),
            "pos": self.position
        }

    def add_velocity(self, value: Vec2) -> None:
        """
        add velocity to the entity and guarantee that it will be valid
        (for short bursts)
        """
        self._velocity_to_add += value

    def add_acceleration(self, value: Vec2) -> None:
        """
        add acceleration to the entity and guarantee that it will be valid
        (for long accelerations)
        """
        self._acceleration_to_add += value

    def _generate_collision_mask(self) -> None:
        """
        generate the mask used for precise collision
        """
        self.mask = pg.mask.Mask(self.size.xy, True)

    @staticmethod
    def on_ground() -> bool:
        """is entity on ground?"""
        return True

    def update_rect(self) -> None:
        """update position rectangle"""
        self.rect = pg.Rect(
            self.position.x - self.size.x / 2,
            self.position.y - self.size.y / 2,
            self.size.x,
            self.size.y
        )

    def _update(self, delta: float) -> None:
        self.__world_position = pv.global_vars.get_world_position()

        # update velocity and position
        self.velocity += (
            self._acceleration_to_add + self.acceleration
        ) * delta + self._velocity_to_add
        self.position += self.velocity * delta
        self.acceleration.x *= 0

        self._velocity_to_add *= 0
        self._acceleration_to_add *= 0

        self.update_rect()

        # update timer
        super()._update(delta)

        # update runtime buffer
        self._runtime_buffer[self.id].facing = int(
            normalize_angle(self.facing.angle) * 10_000
        )

    # endregion
