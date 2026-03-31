"""
_synced_entities.py
30.03.2026

Shared memory synced graphics entities

Author:
Nilusink
"""
from icecream import ic
import typing as tp
import math as m

from ...shared.utility import Vec2
from ..entities import BaseGraphicsEntity, Drawn, SyncedEntities
from ..render_bindings import renderer
from ... import pv


class SyncedGraphicsEntity(BaseGraphicsEntity):
    __slots__ = [
        "pos", "facing", "size", "alive", "param0", "param1", "param2",
        "param3", "__id"
    ]
    pos: Vec2
    facing: Vec2
    size: Vec2
    alive: bool

    param0: float
    param1: float
    param2: float
    param3: float

    def __init__(self, sync_id: int, parent: tp.Self | None = None) -> None:
        self.__id = sync_id
        super().__init__(parent)

        # initialize defaults
        self.pos = Vec2()
        self.facing = Vec2()
        self.size = Vec2()
        self.alive = True

        self.param0 = 0
        self.param1 = 0
        self.param2 = 0
        self.param3 = 0

        self._update_from_buffer()

        self.add(Drawn, SyncedEntities)

    # region buffer control
    def _update_from_buffer(self) -> None:
        """
        update entity values from shared buffer
        """
        self.pos.x = pv.E_BUFF[self.__id].pos_x
        self.pos.y = pv.E_BUFF[self.__id].pos_y

        self.facing.x = pv.E_BUFF[self.__id].facing_x
        self.facing.y = pv.E_BUFF[self.__id].facing_y

        self.size.x = pv.E_BUFF[self.__id].size_x
        self.size.y = pv.E_BUFF[self.__id].size_y

        self.alive = pv.E_BUFF[self.__id].alive

        self.param0 = pv.E_BUFF[self.__id].param0
        self.param1 = pv.E_BUFF[self.__id].param1
        self.param2 = pv.E_BUFF[self.__id].param2
        self.param3 = pv.E_BUFF[self.__id].param3

    def update_from_buffer(self, recursive: bool = True) -> None:
        self._update_from_buffer()

        if recursive:
            for child in self._children:
                child._update_from_buffer()

    # endregion

    # region properties
    @property
    def world_position(self) -> Vec2:
        return self.pos - pv.global_vars.get_world_position()

    # endregion

    # region draw
    def _before_gl_draw(self, drawn: bool) -> None:
        if not self.alive and self.visible:
            self.visible = False

        elif self.alive and not self.visible:
            self.visible = True
    # endregion


class SyncedImageEntity(SyncedGraphicsEntity):
    __slots__ = ["_texture_id"]

    def __init__(
            self,
            sync_id: int,
            texture_id: int,
            parent: tp.Self | None = None
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
    __slots__ = ["_texture_id_l", "_texture_id_r"]

    def _gl_draw(
            self,
            delta_cal: float,
            draw_at: Vec2 = ...,
            size: Vec2 = ...,
            convert_global: bool = True
    ):
        if draw_at is not ...:
            pos = draw_at

        else:
            pos = self.world_position

        if size is ...:
            size = self.size

        renderer.draw_textured_quad(
            self._texture_id_r if self.facing.x < 0 else self._texture_id_l,
            pos - size / 2,
            size,
            convert_global=convert_global
        )
