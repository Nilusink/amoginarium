"""
Shared memory synced graphics entities.

| ``Path``: amoginarium/graphics/logic_dummies/_synced_entities.py
| ``Project``: amoginarium
| ``Created``: 30.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import math as m
import time
from abc import ABC, abstractmethod
from contextlib import suppress
import typing as tp

from icecream import ic

from amoginarium import pv
from amoginarium.shared.utility import Color, Vec2
from amoginarium.shared.debugging import SharedDebuggingInstance

from ..entities import BaseGraphicsEntity, Drawn_0, SyncedEntities
from ..render_bindings import renderer

if tp.TYPE_CHECKING:
    from amoginarium.shared.utility import coord_t


class _SyncedEntitiesManager:
    __slots__ = ["_entities"]

    def __init__(self) -> None:
        self._entities: dict[int, SyncedGraphicsEntity] = {}

    def add_entity(self, sync_id: int, entity: SyncedGraphicsEntity) -> None:
        """
        Add an entity to the manager.
        """
        # delete old entity if it already exists
        if sync_id in self._entities:
            e = self.get_entity(sync_id)
            if e:
                e.kill()

            self.del_entity(sync_id)  # in case entitie ``kill`` has been overwritten

        self._entities[sync_id] = entity

    def del_entity(self, sync_id: int) -> bool:
        """
        Remove an entity from the manager.

        :returns: true if entity was removed, false if not present
        """
        if sync_id not in self._entities:
            return False

        self._entities.pop(sync_id)
        return True

    def get_entity(self, sync_id: int) -> SyncedGraphicsEntity | None:
        """
        Get a graphics entity by ID.

        :returns: None if not found, entity if present
        """
        if sync_id not in self._entities:
            return None

        return self._entities[sync_id]

    def reset(self) -> None:
        """Kill all entities and reset buffer."""
        for eid, entity in self._entities.copy().items():
            self.del_entity(eid)
            entity.kill()


SE_MANAGER = _SyncedEntitiesManager()


class SyncedGraphicsEntity(BaseGraphicsEntity):
    """
    Graphics entity synced with logic entity (via SHM).

    :ivar pos: Position
    :ivar facing: Facing
    :ivar size: Size
    :ivar alive: is alive
    :ivar _logic_visibility: Is set visible by logic process?
    :ivar _sdi: Shared Debugging Instance
    """

    __slots__ = [
        "pos",
        "facing",
        "size",
        "alive",
        "param0",
        "param1",
        "param2",
        "param3",
        "__id",
        "_sdi",
        "param4",
        "_logic_visibility",
    ]
    pos: Vec2
    facing: Vec2
    size: Vec2
    alive: bool
    _logic_visibility: bool
    _sdi: SharedDebuggingInstance | None

    param0: float
    param1: float
    param2: float
    param3: int
    param4: int

    def __init__(
        self,
        sync_id: int,
        parent: int | None = None,
        adv_debugging_data: dict | None = None
    ) -> None:
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

        self._update_from_buffer()

        # add to manager
        SE_MANAGER.add_entity(self.__id, self)
        self.add(Drawn_0, SyncedEntities)

        # create debugging instance
        self._sdi = None
        if adv_debugging_data:
            self._sdi = SharedDebuggingInstance.from_data(
                sh=pv.SH,
                data=adv_debugging_data,
            )

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
        Entity position - world position offset.
        """
        return self.pos - pv.global_vars.get_world_position()

    @property
    def _buff(self):
        """:return: runtime buffer data for this entity"""
        return pv.E_BUFF[self.__id]

    @property
    def id(self) -> int:
        """Sync ID."""
        return self.__id

    # endregion

    # region buffer control
    def _get_bit(self, param: str, bit_index: int) -> bool:
        """
        Get one single bits value.

        :param param: param to get bit from
        :param bit_index: which bit to get
        :return: value of bit
        """
        value = getattr(pv.E_BUFF[self.__id], param)

        return value & (1 << bit_index)

    def _update_from_buffer(self) -> None:
        """
        Update entity values from shared buffer.
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
        Update entity values from shared buffer.
        """
        self._update_from_buffer()

        if recursive:
            for child in self._children:
                child: SyncedGraphicsEntity
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

        if self._sdi:
            ic(self.id, self._sdi.read())

    def _after_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        """
        Run after gl_draw.

        :param drawn: Whether the UI-entity was drawn
        :param layer: what layer the draw function has been called by.
        """
        if self._highlight:
            renderer.enable_stencil(True)
            renderer.draw_rect(
                (0, 0),
                (2000, 2000),
                Color().from_1(
                    0.6, 0.6, 0.7, 0.125 + m.sin(2 * time.perf_counter() + self.id) / 8
                ),
            )
            renderer.disable_stencil()

    # endregion


class SyncedImageEntity(SyncedGraphicsEntity):
    __slots__ = ["_texture_id", "_lifetime"]

    def __init__(
        self,
        sync_id: int,
        texture_id: int,
        parent: int | None = None,
        adv_debugging_data: dict | None = None,
    ) -> None:
        self._texture_id = texture_id
        super().__init__(sync_id, parent, adv_debugging_data=adv_debugging_data)

    @property
    def texture_id(self) -> int:
        """Image texture id."""
        return self._texture_id

    def draw_at(
        self,
        position: coord_t,
        size: coord_t,
        layer: int,
        *,
        rotation: float = 0,
    ) -> None:
        """Draw an entity at specified position and size."""
        renderer.draw_textured_quad(
            self._texture_id,
            position,
            size,
            rotate_angle=rotation,
            layer=layer,
        )

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        self._lifetime += delta_cal

        world_position = pv.global_vars.get_world_position()

        self.draw_at(
            (
                self.pos.x - world_position.x - self.size.x / 2,
                self.pos.y - world_position.y - self.size.y / 2,
            ),
            (self.size.x, self.size.y),
            layer=layer,
            rotation=self.facing.angle * (180 / m.pi),
        )


class SyncedLRImageEntity(SyncedGraphicsEntity):
    """
    entity with two textures used depending on facing.x.
    """

    __slots__ = ["_texture_id_l", "_texture_id_r"]

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        renderer.draw_textured_quad(
            self._texture_id_r if self.facing.x < 0 else self._texture_id_l,
            self.world_position - self.size / 2,
            self.size,
            layer=layer,
        )


class Iconifyable(ABC):
    """entities that can be represented in an icon."""

    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        # call next class in MRO
        super().__init__(*args, **kwargs)

    @abstractmethod
    def get_icon(self) -> tuple[int, tuple[int, int]]:
        """
        Get icon of item.

        :returns: icon texture id, icon size
        """
        raise NotImplementedError
