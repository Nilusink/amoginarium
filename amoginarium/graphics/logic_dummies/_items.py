"""
_items.py
08.04.2026

item dummies

Author:
Nilusink
"""

import typing as tp
import math as m

from amoginarium.shared.utility import Vec2, Color, normalize_angle
from amoginarium.base._textures import textures
from amoginarium.shared import ItemCIDs

from ..entities import Drawn_1, Drawn_0, Animation
from ..render_bindings import renderer
from ._synced_entities import Iconifyable, SyncedLRImageEntity


class BaseItem(Iconifyable, SyncedLRImageEntity):
    """
    base graphics item

    ``param1``: usage
    """

    __slots__ = ("_internal_offset", "_bar_colors")

    _image_name: tuple[str, str] | str = "bullet"
    _image_size: tuple[int, int] = (32, 32)
    _texture_id_r: int = ...
    _texture_id_l: int = ...

    @classmethod
    def load_textures(cls) -> None:
        """load textures for class"""
        if cls._texture_id_r is not ...:
            return

        if isinstance(cls._image_name, str):
            cls._texture_id_r, _ = textures.get_texture(
                cls._image_name, cls._image_size, pixel_perfect=True
            )
            cls._texture_id_l, _ = textures.get_texture(
                cls._image_name, cls._image_size, mirror="x", pixel_perfect=True
            )

        else:
            cls._texture_id_r, _ = textures.get_texture(
                cls._image_name[1],
                cls._image_size,
                scope=cls._image_name[0],
                pixel_perfect=True,
            )
            cls._texture_id_l, _ = textures.get_texture(
                cls._image_name[1],
                cls._image_size,
                mirror="x",
                scope=cls._image_name[0],
                pixel_perfect=True,
            )

    def __new__(cls, *args, **kwargs) -> tp.Self:
        if cls._texture_id_r is ...:
            cls.load_textures()

        return super().__new__(cls)

    def __init__(self, sync_id: int) -> None:
        super().__init__(sync_id)

        self._internal_offset = Vec2()
        square_size = max(self._image_size)
        self._internal_offset.x = (square_size - self._image_size[0]) / 2
        self._internal_offset.y = (square_size - self._image_size[1]) / 2

        self._bar_colors = (Color().from_1(0.55, 0.55, 1),)

        self.remove(Drawn_0)
        self.add(Drawn_1)

    def get_icon(self) -> tuple[int, tuple[int, int]]:
        return self._texture_id_r, self._image_size

    def _gl_draw(self, delta_cal: float, layer: int = 0, draw_item: bool = True):
        if draw_item:
            angle = self.facing.angle * (180/m.pi)
            if self.facing.x < 0:
                renderer.draw_textured_quad(
                    self._texture_id_l,
                    self.world_position,
                    self.size,
                    rotate_angle=angle - 180,
                    layer=layer,
                )

            else:
                renderer.draw_textured_quad(
                    self._texture_id_r,
                    self.world_position,
                    self.size,
                    rotate_angle=angle,
                    layer=layer,
                )

        # draw usage bar
        if self._get_bit("flags", 15):
            if self.parent:
                pos = self.parent.world_position
                size = self.parent.size

            else:
                pos = self.world_position
                size = self.size

            renderer.draw_bar(
                (pos.x - size.x / 2, pos.y + size.y / 2 + 10 + 1.5 * 7),
                (size.x, 7),
                self._bar_colors,
                self.param1,
            )


class Shield(BaseItem):
    """
    protective shield

    ``param1``: usage
    """
    __slots__ = ()

    _CID = ItemCIDs.shield
    _image_name: tuple[str, str] | str = ("Shield_6", "4")
    _image_size: tuple[int, int] = (45, 80)


class HealingPotion(BaseItem):
    """
    healing potion

    ``param0``: fluid tilt
    ``param1``: usage
    """

    __slots__ = ()

    _CID = ItemCIDs.healing_potion
    _image_name = ("potions", "empty")
    _image_size = (32, 32)
    _empty_mask = ("potions", "empty_mask")
    _mask_texture = ...

    @classmethod
    def load_textures(cls) -> None:
        if cls._texture_id_r is not ...:
            return

        cls._mask_texture, _ = textures.get_texture(
            cls._empty_mask[1],
            cls._image_size,
            scope=cls._empty_mask[0]
        )

        super().load_textures()

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        angle = normalize_angle(self.facing.angle) * (180/m.pi)
        own_pos = self.world_position

        # noinspection PyTypeChecker
        renderer.apply_stencil(
            renderer.draw_textured_quad,
            False,
            self._mask_texture,
            own_pos + self._internal_offset,
            self._image_size,
            rotate_angle=angle - (180 if 90 < angle < 270 else 0),
            layer=layer
        )

        fill_line = 5 + (self.size.y - 10) * (1 - self.param1)
        renderer.draw_polygon(
            [
                own_pos + Vec2().from_cartesian(
                    -self.size.x,
                    self.size.y
                ),
                own_pos + Vec2().from_cartesian(
                    2 * self.size.x,
                    self.size.y
                ),
                own_pos + Vec2().from_cartesian(
                    self.size.x / 2, fill_line
                ) + Vec2().from_polar(
                    (angle + self.param0) * m.pi / 180,
                    self.size.x) + Vec2().from_cartesian(
                    0, 5
                ),
                own_pos + Vec2().from_cartesian(
                    self.size.x / 2, fill_line
                ) - Vec2().from_polar(
                    (angle + self.param0) * m.pi / 180,
                    self.size.x) + Vec2().from_cartesian(
                    0, 5
                ),
            ],
            (0, .8, 0),
        )

        if not self._highlight:
            renderer.disable_stencil()

        super()._gl_draw(delta_cal, layer=layer)


class JetBag(BaseItem):
    """makes you flyyy (not actually, but it makes it look like you do)"""
    
    __slots__ = ()

    _CID = ItemCIDs.jetbag
    _image_name: tuple[str, str] | str = ("missiles", "Missile02F")
    _image_size: tuple[int, int] = (32, 64)
    _animation_scope: str = "flame"
    _animation_size: tuple[int, int] = (32, 32)
    _animation_textures: list[int] = ...

    @classmethod
    def load_textures(cls) -> None:
        if cls._texture_id_r is not ...:
            return

        cls._animation_textures = [
            t[0]
            for t in textures.get_all_from_scope(
                cls._animation_scope, cls._animation_size, pixel_perfect=True
            )
        ]

        super().load_textures()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._animation = Animation(
            self._animation_textures,
            self._animation_size,
            0.05,
            position_reference=self._flame_position,
            loop=True,
        )

    def _flame_position(self) -> Vec2:
        return self.pos + Vec2().from_cartesian(
            self.size.x / 2
            * (1 if self.facing else -1),
            self.size.y / 2 + 36
        )

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        angle = normalize_angle(self.facing.angle) * (180 / m.pi)
        own_pos = self.world_position

        if self._get_bit("flags", 14):  # active
            self._animation.play()

        else:
            self._animation.stop()

        if 90 < angle < 270:
            renderer.draw_textured_quad(
                self._texture_id_l,
                own_pos,
                (
                    self.size.x,
                    self.size.y
                ),
                layer=layer
            )
            self._facing = False

        else:
            renderer.draw_textured_quad(
                self._texture_id_r,
                own_pos,
                (
                    self.size.x,
                    self.size.y
                ),
                layer=layer
            )
            self._facing = True

        # draw usage bar
        super()._gl_draw(delta_cal, layer=layer, draw_item=False)
