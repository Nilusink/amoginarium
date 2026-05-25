"""
Charged weapon dummies.

| ``Path``: amoginarium/graphics/logic_dummies/_charged_weapons.py
| ``Project``: amoginarium
| ``Created``: 11.04.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amoginarium.shared import WeaponCIDs
from amoginarium.shared.utility import Color, Vec2

from ..render_bindings import renderer
from ..textures import textures
from ._weapons import WeaponDummy

if TYPE_CHECKING:
    from types import EllipsisType


class ChargedWeaponDummy(WeaponDummy):
    """
    weapon with charging bar.

    ``param2``: charge state
    """

    _c_bar_colors: tuple[Color] = (Color().from_255(143, 0, 124),)

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        super()._gl_draw(delta_cal, layer)

        # draw charge bar
        if self._get_bit("flags", 15):  # has parent
            # don't draw bar if not charged at all
            if not self.param2:
                return

            if self.parent:
                pos = self.parent.world_position
                size = self.parent.size

            else:
                pos = self.world_position
                size = self.size

            renderer.draw_bar(
                (pos.x - size.x / 2, pos.y + size.y / 2 + 10 + 3 * 7),
                (size.x, 7),
                self._c_bar_colors,
                self.param2,
            )


class ChargedDynamicWeaponDummy(ChargedWeaponDummy):
    """weapon with changing textures."""

    _image_name = ...
    _image_scope: str = "railgun"
    _images: list[int] | EllipsisType = ...
    _images_m: list[int] | EllipsisType = ...

    @classmethod
    def load_textures(cls) -> None:
        if cls._images is not ...:
            return

        cls._images = [
            t[0]
            for t in textures.get_all_from_scope(
                cls._image_scope, cls._default_size, mirror="x", pixel_perfect=True
            )
        ]
        cls._images_m = [
            t[0]
            for t in textures.get_all_from_scope(
                cls._image_scope, cls._default_size, pixel_perfect=True
            )
        ]

    @classmethod
    def get_icon(cls) -> tuple[int, tuple[int, int]]:
        return cls._images[0], cls._default_size

    @property
    def _texture_id_r(self) -> int:
        """Texture id right."""
        return self._images[round(self.param2 * (len(self._images) - 1))]

    @property
    def _texture_id_l(self) -> int:
        """Texture id left."""
        return self._images_m[round(self.param2 * (len(self._images) - 1))]


class RailGunDummy(ChargedDynamicWeaponDummy):
    _CID = WeaponCIDs.railgun
    _image_scope = "railgun"
    _default_size = (128, 64)
    _image_rotate_anchor = Vec2().from_cartesian(24, 32)
