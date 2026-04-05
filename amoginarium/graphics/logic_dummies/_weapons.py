"""
_weapons.py
02.04.2026

Weapon models

Author:
Nilusink
"""

import typing as tp
import math as m

from amoginarium.shared.utility import Vec2, Color
from amoginarium.base._textures import textures
from amoginarium.shared import WeaponCIDs
from amoginarium import pv

from ._synced_entities import SyncedLRImageEntity
from ..render_bindings import renderer
from ..entities import Drawn_1, Drawn_0


class WeaponDummy(SyncedLRImageEntity):
    """
    ``param0`` size fac
    ``param1`` mag state
    ``param3`` charge state if applicable
    """

    __slots__ = ["_bar_colors"]

    _cid = WeaponCIDs.base
    _image_name: str = "minigun"
    _image_size: tuple[int, int] = (128, 64)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(35, 30)
    _image_mirror: bool = False
    _texture_id_l: int = ...
    _texture_id_r: int = ...

    @classmethod
    def load_textures(cls) -> None:
        """
        load weapon textures

        .. note:: only execute once!
        """
        cls._texture_id_r, _ = textures.get_texture(
            name=cls._image_name,
            size=cls._image_size,
            mirror="" if cls._image_mirror else "x",
        )
        cls._texture_id_l, _ = textures.get_texture(
            name=cls._image_name,
            size=cls._image_size,
            mirror="x" if cls._image_mirror else "",
        )

    def __new__(cls, *args, **kwargs) -> tp.Self:
        if cls._texture_id_r is ...:
            cls.load_textures()

        return super().__new__(cls)

    def __init__(self, sync_id: int, parent: int) -> None:
        super().__init__(
            sync_id=sync_id,
            parent=parent
        )
        self.remove(Drawn_0)
        self.add(Drawn_1)
        self._bar_colors = (Color().from_1(.55, .55, 1),)

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        """
        Draw weapon (centered) at a specified position

        :param delta_cal: used for the occasional calculation
        """
        angle = self.facing.angle * 180/m.pi
        world_pos = pv.global_vars.get_world_position()

        if self.facing.x < 0:
            anchor = Vec2().from_cartesian(
                (self._image_size[0] - self._image_rotate_anchor.x) * self.param0,
                self._image_rotate_anchor.y * self.param0,
            )
            pos = self.pos - anchor
            pos -= world_pos

            renderer.draw_textured_quad(
                self._texture_id_l,
                pos,
                self._image_size,
                rotate_angle=angle - 180,
                rotate_anchor=anchor,
            )

        else:
            anchor = Vec2().from_cartesian(
                self._image_rotate_anchor.x * self.param0,
                self._image_rotate_anchor.y * self.param0
            )
            pos = self.pos - anchor
            pos -= world_pos

            renderer.draw_textured_quad(
                self._texture_id_r,
                pos,
                self._image_size,
                rotate_angle=angle,
                rotate_anchor=anchor,
            )

        # draw ammo bar
        if self.parent:
            pos = self.parent.world_position
            size = self.parent.size

        else:
            pos = self.world_position
            size = self.size

        renderer.draw_bar(
            (pos.x - size.x / 2, pos.y + size.y / 2 + 10 + 1.5*7),
            (size.x, 7),
            self._bar_colors,
            self.param1,
        )


class Minigun(WeaponDummy):
    _cid = WeaponCIDs.minigun
    _image_name: str = "minigun"
    _image_size: tuple[int, int] = (128, 64)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(35, 30)


class Ak47(WeaponDummy):
    _cid = WeaponCIDs.ak47
    _image_name: str = "ak47"
    _image_size: tuple[int, int] = (80, 40)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(30, 20)


class Sniper(WeaponDummy):
    _cid = WeaponCIDs.sniper
    _image_name: str = "sniper"
    _image_size: tuple[int, int] = (120, 60)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(25, 33)


class Mortar(WeaponDummy):
    _cid = WeaponCIDs.mortar
    _image_name: str = "mortar"
    _image_size: tuple[int, int] = (25 * 1.5, 17 * 1.5)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(7.5 * 1.5, 8 * 1.5)


class Flak(WeaponDummy):
    _cid = WeaponCIDs.flak
    _image_name: str = "FLAK_canon"
    _image_size: tuple[int, int] = (256, 128)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(83, 59)


class CRAM(WeaponDummy):
    _cid = WeaponCIDs.cram
    _image_name: str = "CRAM_canon"
    _image_mirror = True
    _image_size: tuple[int, int] = (128, 128)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(32, 79)


class HandThrownGrenade(WeaponDummy):
    _cid = WeaponCIDs.h_grenade
    _image_name: str = "grenade"
    _image_mirror = True
    _image_size: tuple[int, int] = (32, 32)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(16, 16)
