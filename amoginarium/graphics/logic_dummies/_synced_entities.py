"""
_synced_entities.py
30.03.2026

Shared memory synced graphics entities

Author:
Nilusink
"""

import math as m

from ...shared.utility import Vec2
from ..entities import BaseGraphicsEntity, Drawn_0, SyncedEntities
from ..render_bindings import renderer
from ... import pv


class SyncedGraphicsEntity(BaseGraphicsEntity):
    """
    Graphics entity synced with logic entity (via SHM)
    """

    __slots__ = [
        "pos", "facing", "size", "alive", "param0", "param1", "param2",
        "param3", "__id", "__was_alive", "param4", "_logic_visibility"
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

    def __init__(self, sync_id: int, parent: BaseGraphicsEntity | None = None) -> None:
        self.__id = sync_id
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

        self.__was_alive = False
        self._update_from_buffer()

        self.add(Drawn_0, SyncedEntities)

    # region properties
    @property
    def visible(self) -> bool:
        return self._visible and self._logic_visibility

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

        if not self.__was_alive:
            if self.alive:
                self.__was_alive = True

        else:
            if not self.alive:
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
                child._update_from_buffer()

    # endregion

    # region properties
    @property
    def world_position(self) -> Vec2:
        """
        entity position - world position offset
        """
        return self.pos - pv.global_vars.get_world_position()

    # endregion

    # region draw
    def _before_gl_draw(self, drawn: bool) -> None:
        if not self.alive and self._visible:
            self._visible = False

        elif self.alive and not self._visible:
            self._visible = True
    # endregion


class SyncedImageEntity(SyncedGraphicsEntity):
    __slots__ = ["_texture_id"]

    def __init__(
            self,
            sync_id: int,
            texture_id: int,
            parent: BaseGraphicsEntity | None = None
    ) -> None:
        self._texture_id = texture_id
        super().__init__(sync_id, parent)

    def _gl_draw(self, delta_cal: float):
        world_position = pv.global_vars.get_world_position()
        renderer.draw_textured_quad(
            self._texture_id,
            (
                self.pos.x - world_position.x,
                self.pos.y - world_position.y
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

    def _gl_draw(self, delta_cal: float):

        renderer.draw_textured_quad(
            self._texture_id_r if self.facing.x < 0 else self._texture_id_l,
            self.world_position - self.size / 2,
            self.size,
        )
