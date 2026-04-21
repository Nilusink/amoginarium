"""
_synced_entities.py
30.03.2026

Shared memory synced graphics entities

Author:
Nilusink
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from contextlib import suppress
from icecream import ic
import math as m

from amoginarium.shared.utility import Vec2, Color
from amoginarium import pv

from ..entities import BaseGraphicsEntity, Drawn_0, SyncedEntities
from ..render_bindings import renderer


class _SyncedEntitiesManager:
    __slots__ = ["_entities"]
    
    def __init__(self) -> None:
        self._entities: dict[int, SyncedGraphicsEntity] = {}

    def add_entity(self, sync_id: int, entity: SyncedGraphicsEntity) -> None:
        """
        add an entity to the manager
        """
        # delete old entity if it already exists
        if sync_id in self._entities:
            self.get_entity(sync_id).kill()
            self.del_entity(sync_id)  # in case entitie ``kill`` has been overwritten

        #     raise RuntimeError(f"entity with id {sync_id} already in manager")

        self._entities[sync_id] = entity

    def del_entity(self, sync_id: int) -> bool:
        """
        remove an entity from the manager

        :returns: true if entity was removed, false if not present
        """
        if sync_id not in self._entities:
            return False

        self._entities.pop(sync_id)
        return True

    def get_entity(self, sync_id: int) -> SyncedGraphicsEntity | None:
        """
        get a graphics entity by ID

        :returns: None if not found, entity if present
        """
        if sync_id not in self._entities:
            return None

        return self._entities[sync_id]

    def reset(self) -> None:
        """kill all entities and reset buffer"""
        for eid, entity in self._entities.copy().items():
            self.del_entity(eid)
            entity.kill()


SE_MANAGER = _SyncedEntitiesManager()


class SyncedGraphicsEntity(BaseGraphicsEntity):
    """
    Graphics entity synced with logic entity (via SHM)
    """

    __slots__ = [
        "pos", "facing", "size", "alive", "param0", "param1", "param2",
        "param3", "__id", "param4", "_logic_visibility"
    ]
    pos: Vec2
    facing: Vec2
    size: Vec2
    alive: bool
    _logic_visibility: bool

    param0: float
    param1: float
    param2: float
    param3: int
    param4: int

    def __init__(self, sync_id: int, parent: int | None = None) -> None:
        self.__id = sync_id

        # try to get parent by sync_id
        if isinstance(parent, int):
            parent: SyncedGraphicsEntity | None = SE_MANAGER.get_entity(parent)

        super().__init__(parent)

        # initialize defaults
        self.pos = Vec2()
        self.facing = Vec2().from_polar(0, 1)
        self.size = Vec2()
        self.alive = True
        self._logic_visibility = False

        self.param0 = 0
        self.param1 = 0
        self.param2 = 0
        self.param3 = 0
        self.param4 = 0

        self.add(Drawn_0, SyncedEntities)
        self._update_from_buffer()

        # add to manager
        SE_MANAGER.add_entity(self.__id, self)

    # region entity management
    def kill(self) -> None:
        SE_MANAGER.del_entity(self.__id)
        super().kill()

    # endregion

    # region properties
    @property
    def visible(self) -> bool:
        return self._visible and self._logic_visibility

    @property
    def world_position(self) -> Vec2:
        """
        entity position - world position offset
        """
        return self.pos - pv.global_vars.get_world_position()

    @property
    def _buff(self):
        """:return: runtime buffer data for this entity"""
        return pv.E_BUFF[self.__id]
    # endregion

    # region buffer control
    def _get_bit(self, param: str, bit_index: int) -> bool:
        """
        get one single bits value

        :param param: param to get bit from
        :param bit_index: which bit to get
        :return: bit value
        """
        value = getattr(pv.E_BUFF[self.__id], param)

        return value & (1 << bit_index)

    def _update_from_buffer(self) -> None:
        """
        update entity values from shared buffer
        """
        self.pos.x = pv.E_BUFF[self.__id].pos_x
        self.pos.y = pv.E_BUFF[self.__id].pos_y

        self.facing.angle = pv.E_BUFF[self.__id].facing / 10_000

        self.size.x = pv.E_BUFF[self.__id].size_x
        self.size.y = pv.E_BUFF[self.__id].size_y

        self.alive = self._get_bit("flags", 0)
        self._logic_visibility = self._get_bit("flags", 1)
        self._highlight = self._get_bit("flags", 2)

        if not self.alive:
            self._logic_visibility = True
            self._visible = True
            self.kill()

        self.param0 = pv.E_BUFF[self.__id].param0
        self.param1 = pv.E_BUFF[self.__id].param1
        self.param2 = pv.E_BUFF[self.__id].param2
        self.param3 = pv.E_BUFF[self.__id].param3
        self.param4 = pv.E_BUFF[self.__id].param4

    def update_from_buffer(self, recursive: bool = True) -> None:
        """
        update entity values from shared buffer
        """
        self._update_from_buffer()

        if recursive:
            for child in self._children:
                with suppress(AttributeError):
                    child.update_from_buffer()

    # endregion

    # region draw
    def _before_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        if not self.alive and self._visible:
            self._visible = False

        elif self.alive and not self._visible:
            self._visible = True

        if self._highlight:
            renderer.start_stencil(True)

    def _after_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        """
        Called after gl_draw
        :param drawn: Whether the UI-entity was drawn
        :param layer: what layer the draw function has been called by
        """
        if self._highlight:
            renderer.enable_stencil(True)
            renderer.draw_rect(
                (0, 0),
                (2000, 2000),
                Color().from_1(0.6, 0.6, .7, 0.125 + m.sin(self._lifetime) / 8),
            )
            renderer.disable_stencil()
    # endregion


class SyncedImageEntity(SyncedGraphicsEntity):
    __slots__ = ["_texture_id", "_lifetime"]

    def __init__(
            self,
            sync_id: int,
            texture_id: int,
            parent: int | None = None
    ) -> None:
        self._texture_id = texture_id
        self._lifetime = 0
        super().__init__(sync_id, parent)

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        self._lifetime += delta_cal

        world_position = pv.global_vars.get_world_position()
        renderer.draw_textured_quad(
            self._texture_id,
            (
                self.pos.x - world_position.x - self.size.x / 2,
                self.pos.y - world_position.y - self.size.y / 2
            ),
            (
                self.size.x,
                self.size.y
            ),
            rotate_angle=self.facing.angle * (180 / m.pi)
        )


class SyncedLRImageEntity(SyncedGraphicsEntity):
    """
    entity with two textures used depending on facing.x
    """

    __slots__ = ["_texture_id_l", "_texture_id_r"]

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        renderer.draw_textured_quad(
            self._texture_id_r if self.facing.x < 0 else self._texture_id_l,
            self.world_position - self.size / 2,
            self.size,
        )


class Iconifyable(ABC):
    """entities that can be represented in an icon"""

    def __init__(self, *args, **kwargs) -> None:

        # call next class in MRO
        super().__init__(*args, **kwargs)

    @abstractmethod
    def get_icon(self) -> tuple[int, tuple[int, int]]:
        """
        get icon of item

        :returns: icon texture id, icon size
        """
        raise NotImplementedError
