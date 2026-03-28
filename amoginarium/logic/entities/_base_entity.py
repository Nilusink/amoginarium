"""
_base_entity.py
28.03.2026

defines the most basic form of logic entity
"""
from __future__ import annotations
from multiprocessing.shared_memory import SharedMemory
import pygame as pg
import typing as tp

from amoginarium.shared.debugging import print_ic_style, CC
from amoginarium.shared import Coalitions, global_vars
from .._sharing import base_entity_t
from amoginarium.shared.utility import Vec2


class BaseLogicEntity:
    __slots__ = ["_parent", "_children", "_lifetime", "__id", "__shm", "__g"]

    _children: list[tp.Self]
    _lifetime: float
    _parent: tp.Self | None

    def __init__(
            self,
            id: int,
            shm: SharedMemory,
            parent: tp.Self | None = None,
    ) -> None:
        # pygame groups
        self.__g = []

        self._parent = parent
        self._children = []
        self._lifetime = 0

        # data block
        self.__id = id
        self.__shm = (base_entity_t * MAX_CAMS).from_buffer(cams_shm.buf)

    # region properties
    @property
    def id(self) -> int:
        return self.__id

    @property
    def parent(self) -> tp.Self | None:
        return self._parent

    @property
    def root(self) -> tp.Self:
        if self._parent:
            return self._parent.root

        return self

    @property
    def children(self) -> list[tp.Self]:
        return self._children
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

    def kill(self) -> None:
        """
        remove entity from all groups
        """
        # kill children first
        for child in self._children:
            child.kill()

        # commit suicide
        for group in self.__g:
            group.remove_internal(self)

        self.__g.clear()

    # endregion

    # region entity methods
    def _update(self, delta: float) -> None:
        """
        actual update function for the entity
        """
        self._lifetime += delta

        # update shared memory
        self.__shm[self.__id].pos_x = 0

    @tp.final
    def update(self, delta: float) -> None:
        """
        update entity and their children
        """
        self._update(delta)
        for child in self._children:
            child.update(delta)
    # endregion


class PositionedLogicEntity(BaseLogicEntity):
    # don't use properties for position and size for faster access
    __slots__ = ["position", "size"]

    position: Vec2
    size: Vec2

    def __init__(
            self,
            id: int,
            shm: SharedMemory,
            size: Vec2,
            position: Vec2,
            parent: tp.Self | None = None,
    ) -> None:
        super().__init__(id=id, shm=shm, parent=parent)
        self.position = position
        self.size = size


class LogicGameEntity(PositionedLogicEntity):
    _cid: str = ...  # for serialization

    __slots__ = [
        "facing", "velocity", "acceleration", "_coalition", "_velocity_to_add",
        "_acceleration_to_add", "mask", "rect"
    ]

    mask: pg.Mask
    rect: pg.Rect
    facing: Vec2
    velocity: Vec2
    acceleration: Vec2

    def __init__(
            self,
            id: int,
            shm: SharedMemory,
            size: Vec2,
            position: Vec2,
            initial_velocity: Vec2 | None = None,
            parent: tp.Self | None = None,
            coalition: Coalitions = ...
    ) -> None:
        super().__init__(
            id=id,
            shm=shm,
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
        # endregion

    # region properties
    @property
    def world_position(self) -> Vec2:
        return self.position - global_vars.world_position

    @property
    def is_bullet(self) -> bool:
        return False

    @property
    def coalition(self) -> Coalitions:
        return self.coalition

    @property
    def serializable(self) -> bool:
        return self._cid is not ...

    #endregion

    # region class methods
    @classmethod
    def cid(cls) -> str:
        if cls._cid is ...:
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._cid
    # endregion

    # region methods
    def to_dict(self) -> dict:
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
        return True

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x - self.size.x / 2,
            self.position.y - self.size.y / 2,
            self.size.x,
            self.size.y
        )

    def _update(self, delta: float) -> None:
        # update velocity and position
        self.velocity += (self._acceleration_to_add + self.acceleration) * delta + self._velocity_to_add
        self.position += self.velocity * delta
        self.acceleration.x *= 0

        self._velocity_to_add *= 0
        self._acceleration_to_add *= 0

        self.update_rect()

        # update timer
        super()._update(delta)

    # endregion
