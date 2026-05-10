"""
_weapons.py
02.04.2026

Weapon models

Author:
Nilusink
"""

from types import EllipsisType
import typing as tp
import math as m

from amoginarium.shared.utility import Vec2, Color, WtfError, convert_coord, RTD, PI
from amoginarium.base._textures import textures
from amoginarium.shared import WeaponCIDs
from amoginarium import pv

from ._synced_entities import SyncedLRImageEntity, Iconifyable
from ..entities import Drawn_1, Drawn_0, Drawn_2
from ..render_bindings import renderer
from ._bullet import BulletDummy


class WeaponDummy(Iconifyable, SyncedLRImageEntity):
    """

    ``flags[13]`` weapon loaded
    ``param0`` size fac
    ``param1`` mag state
    """

    __slots__ = ()

    # region class vars
    _CID = WeaponCIDs.base
    _image_name: tp.ClassVar[str] = "minigun"
    _image_mirror: tp.ClassVar[str] = ""
    _default_size: tp.ClassVar[tuple[int, int] | Vec2] = (128, 64)
    _image_rotate_anchor: tp.ClassVar[Vec2] = Vec2().from_cartesian(35, 30)
    _bar_colors: tp.ClassVar = (Color().from_1(.55, .55, 1),)
    _texture_id_l: tp.ClassVar[int | EllipsisType] = ...
    _texture_id_r: tp.ClassVar[int | EllipsisType] = ...

    # visible bullet params
    _bullet_type: tp.ClassVar[tp.Type[BulletDummy]] = BulletDummy
    _bullet_visible: tp.ClassVar[bool] = False
    _bullet_mount_point: tp.ClassVar[tuple[int, int] |  EllipsisType] = ...
    # endregion

    # region instance vars
    _bmp: Vec2
    # endregion

    @classmethod
    def load_textures(cls) -> None:
        """
        load weapon textures

        .. note:: only execute once!
        """
        mirror = cls._image_mirror

        cls._texture_id_l, _ = textures.get_texture(
            name=cls._image_name,
            size=cls._default_size,
            mirror=mirror,
            pixel_perfect=True,
        )

        if "x" in mirror:
            mirror = mirror.strip("x")

        else:
            mirror += "x"

        cls._texture_id_r, _ = textures.get_texture(
            name=cls._image_name,
            size=cls._default_size,
            mirror=mirror,
            pixel_perfect=True,
        )

    def __new__(cls, *args, **kwargs) -> tp.Self:
        if cls._texture_id_r is ...:
            cls.load_textures()

        return super().__new__(cls)

    def __init__(self, sync_id: int, ) -> None:
        super().__init__(
            sync_id=sync_id,
        )
        if not isinstance(self._default_size, Vec2):
            if isinstance(self._default_size, (tuple, list)):
                self._default_size: Vec2 = Vec2().from_cartesian(
                    self._default_size[0], self._default_size[1]
                )

            elif isinstance(self._default_size, (int, float)):
                self._default_size: Vec2 = Vec2().from_cartesian(
                    self._default_size, self._default_size
                )

        if isinstance(self._bullet_mount_point, EllipsisType):
            self._bmp = self._default_size / 2

        else:
            self._bmp = convert_coord(self._bullet_mount_point, Vec2)  # type: ignore

        self._default_size: Vec2

        self.remove(Drawn_0)
        self.add(Drawn_1)

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        """
        Draw weapon (centered) at a specified position

        :param delta_cal: used for the occasional calculation
        """
        angle = self.facing.angle * 180/m.pi
        world_pos = pv.global_vars.get_world_position()

        # draw bullet
        if self._bullet_visible and self._get_bit("flags", 13):
            bullet_size = self._bullet_type._default_size

            bmp = self._bmp.copy()

            if self.facing.x < 0:
                bmp.y *= -1

            bullet_offset = Vec2().from_polar(
                bmp.angle + self.facing.angle,
                bmp.length
            )

            bullet_pos = self.pos - bullet_size / 2
            bullet_pos += bullet_offset
            bullet_pos -= world_pos

            self._bullet_type.draw_at(
                bullet_pos,
                bullet_size,
                layer=layer,
                rotation=(self.facing.angle + PI) * RTD,
            )

        if self.facing.x < 0:
            anchor = Vec2().from_cartesian(
                (self._default_size.x - self._image_rotate_anchor.x) * self.param0,
                self._image_rotate_anchor.y * self.param0,
            )
            pos = self.pos - anchor
            pos -= world_pos

            renderer.draw_textured_quad(
                self._texture_id_l,
                pos,
                self._default_size,
                rotate_angle=angle - 180,
                rotate_anchor=anchor,
                layer=layer
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
                self._default_size,
                rotate_angle=angle,
                rotate_anchor=anchor,
                layer=layer
            )

        # draw ammo bar
        if self._get_bit("flags", 15):  # has parent
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

    @classmethod
    def get_icon(cls) -> tuple[int, tuple[float, float]]:
        if isinstance(cls._default_size, Vec2):
            size: tuple[float, float] = cls._default_size.xy

        elif isinstance(cls._default_size, tuple):
            size: tuple[float, float] = cls._default_size

        else:
            raise WtfError("?")

        return cls._texture_id_r, size


class HandThrownGrenade(WeaponDummy):
    _CID = WeaponCIDs.h_grenade
    _image_name: str = "grenade"
    _image_mirror = "x"
    _default_size: tuple[int, int] = (32, 32)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(16, 16)


class ExactoSniper(WeaponDummy):
    _CID = WeaponCIDs.exacto_sniper
    _image_name: str = "exacto_sniper"
    _default_size: tuple[int, int] = (120, 60)
    _image_rotate_anchor: Vec2 = Vec2().from_cartesian(25, 33)

    def __init__(self, max_range: float, **kwargs):
        super().__init__(**kwargs)
        self.add(Drawn_2)
        self._max_range = max_range

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        if layer == 1:
            super()._gl_draw(delta_cal, layer)
            return

        # draw laser to target
        if self.param4:
            laser_end = (
                Vec2().from_polar(self.param3 / 10_000, self.param4)
                - pv.global_vars.get_world_position()
            )
            laser_start = (
                self.world_position
                + Vec2().from_polar(self.facing.angle, 100)
                + Vec2().from_polar(self.facing.angle - m.pi / 2, 2)
            )
            renderer.draw_thick_line(
                laser_start,
                laser_end,
                Color().from_1(1, 0, 0, .2),
                thickness=3,
            )
            renderer.draw_circle(
                laser_end,
                8, 16,
                Color().from_1(1, 0, 0, .6),
            )
