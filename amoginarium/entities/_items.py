"""
_items.py
12.03.2026

various items that are not weapons

Author:
Nilusink
"""
from OpenGL.GL import glBindTexture, glGetTexImage, GL_TEXTURE_2D, GL_RGBA
from OpenGL.GL import GL_UNSIGNED_BYTE
from icecream import ic
import typing as tp
import pygame as pg
import math as m

from ..debugging import run_with_debug
from ..render_bindings import renderer
from ..logic import coord_t, convert_coord, Vec2
from ..base._textures import textures
from ..base import CollisionDestroyed, Updated
from ._base_entity import PositionedEntity
from ._entity_hints import PlayerLike, BaseEntityLike


class BaseItem(PositionedEntity):
    _image_texture_r: int = ...
    _image_texture_l: int = ...
    _image_name: tuple[str, str] | str = "bullet"
    _image_size: tuple[int, int] = (32, 32)
    _max_uses: int = 1

    @classmethod
    def load_textures(cls) -> None:
        if cls._image_texture_r is not ...:
            return

        if isinstance(cls._image_name, str):
            cls._image_texture_r, _ = textures.get_texture(
                cls._image_name,
                cls._image_size
            )
            cls._image_texture_l, _ = textures.get_texture(
                cls._image_name,
                cls._image_size,
                mirror="x"
            )

        else:
            cls._image_texture_r, _ = textures.get_texture(
                cls._image_name[1],
                cls._image_size,
                scope=cls._image_name[0]
            )
            cls._image_texture_l, _ = textures.get_texture(
                cls._image_name[1],
                cls._image_size,
                mirror="x",
                scope=cls._image_name[0]
            )

    def __init__(
            self,
            parent: PlayerLike,
            used_callback: tp.Callable[[int], bool],
            parent_position_offset: coord_t
    ) -> None:
        self._position_offset = convert_coord(parent_position_offset, Vec2)
        self._uses_left = self._max_uses
        self._used_callback = used_callback

        square_size = max(self._image_size)
        self._internal_offset = Vec2().from_cartesian(
            (square_size - self._image_size[0]) / 2,
            (square_size - self._image_size[1]) / 2
        )
        ic(self._image_size, self._internal_offset.xy)

        super().__init__(
            parent.position + self._position_offset,
            Vec2().from_cartesian(square_size, square_size),
            parent
        )

        self._current_angle = Vec2().from_cartesian(1, 0)

        self.load_textures()
        self._generate_collision_mask()
        self.update_rect()

    @property
    def parent(self) -> PlayerLike:
        return self._parent

    @property
    def world_position(self) -> Vec2:
        """
        return the position relative to the world center
        """
        return self.position - Updated.world_position

    @property
    def max_uses(self) -> int:
        return self._max_uses

    @property
    def uses_left(self) -> int:
        return self._uses_left

    def _generate_collision_mask(self) -> None:
        """
        generate the mask used for precise collision
        """
        glBindTexture(GL_TEXTURE_2D, self._image_texture_l)
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        img = pg.image.frombuffer(data, self._image_size, "RGBA")
        surf = pg.Surface(self.size.xy, pg.SRCALPHA, 32)
        ic(surf.size, self.size)
        surf.blit(
            img,
            (
                (self.size.x - img.size[0]) / 2,
                (self.size.y - img.size[1]) / 2
            )
        )
        self._mask_left_surf = surf

        self._mask_right_surf = pg.transform.flip(self._mask_left_surf, True, False)
        self._update_mask()

    def _update_mask(self) -> None:
        angle = self._current_angle.angle * 180/m.pi
        angle = angle % 360

        if 90 < angle < 270:
            surf = pg.transform.rotate(
                self._mask_left_surf,
                -(angle - 180)
            )

        else:
            surf = pg.transform.rotate(
                self._mask_right_surf,
                -angle
            )

        offset = (surf.size[0] - self.size.x) / 2

        surf = surf.subsurface(
            (offset, offset),
            self.size.xy
        )

        self.mask = pg.mask.from_surface(surf)

    def get_mag_state(
            self,
            max_out: float
    ) -> tuple[float, int] | tuple[float, float]:
        """
        returns the current uses (rising when reloading)
        naming borrowed from BaseWeapon for compatability

        :param max_out: output size
        :returns: x out of max_out, value of current state
        """
        return self._uses_left * (
            max_out / self._max_uses
        ), self._uses_left

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x,
            self.position.y,
            self.size.x,
            self.size.y
        )

    def use(self) -> None:
        raise NotImplementedError

    def stop_use(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        ...

    def kill(self, killed_by=...) -> None:
        if self._used_callback(1):
            self._uses_left = self._max_uses

        else:
            ic("kill")
            super().kill()

    def update(self, delta: float) -> None:
        self.update_rect()
        self._update_mask()

    def draw_at(self, position: Vec2, angle: float) -> None:
        debug_surface = self.mask.to_surface()
        renderer.draw_pg_surf(
            (
                self.world_position.x,
                self.world_position.y + self.size.y
            ),
            debug_surface
        )

        renderer.draw_rect(
            self.world_position,
            self.size,
            (1, 0, 0, .2)
        )

    def reset(self) -> None:
        self._uses_left = self._max_uses


class Shield(BaseItem):
    _image_name: tuple[str, str] | str = ("Shield_6", "5")
    _image_size: tuple[int, int] = (45, 80)
    _max_uses: int = 200  # acts as HP for shield

    def __init__(
            self,
            parent: PlayerLike,
            used_callback: tp.Callable[[int], bool],
            parent_position_offset: coord_t
    ) -> None:
        super().__init__(parent, used_callback, parent_position_offset)

        self.add(CollisionDestroyed)

    @property
    def hp(self) -> float:
        return self._uses_left

    def use(self) -> None:
        """
        start using the item
        """

    def stop_use(self) -> None:
        """
        stop using the item
        """

    def hit(self, damage: float, hit_by: BaseEntityLike = ...) -> None:
        self._uses_left -= damage

        if self._uses_left <= 0:
            self.kill(hit_by)

    def draw_at(self, position: Vec2, angle: float) -> None:
        angle = angle % 360
        delta = self._position_offset.copy()
        delta.angle += angle * (m.pi / 180)

        self._current_angle = delta
        self.position = position + delta - self.size / 2

        if 90 < angle < 270:
            renderer.draw_textured_quad(
                self._image_texture_l,
                self.world_position + self._internal_offset,
                self._image_size,
                rotate_angle=angle - 180
            )

        else:
            renderer.draw_textured_quad(
                self._image_texture_r,
                self.world_position + self._internal_offset,
                self._image_size,
                rotate_angle=angle
            )


class HealingPotion(BaseItem):
    _image_name = ("potions", "Icon7")
    _image_size = (32, 32)
    _heal_per_sec = 20
    _max_uses = 80

    def __init__(
            self,
            parent: PlayerLike,
            used_callback: tp.Callable[[int], bool],
            parent_position_offset: coord_t
    ) -> None:
        super().__init__(parent, used_callback, parent_position_offset)
        self._drinking = False

    def use(self) -> None:
        self._drinking = True

    def stop_use(self) -> None:
        self._drinking = False

    def update(self, delta: float) -> None:
        if self._drinking:
            heal = min(
                self._uses_left,
                self._heal_per_sec * delta
            )
            if self.parent.heal(heal):
                self._uses_left -= heal

            if self._uses_left <= 0:
                self.kill()

        super().update(delta)

    def draw_at(self, position: Vec2, angle: float) -> None:
        angle = angle % 360
        self.position = position - self.size / 2

        if 90 < angle < 270:
            renderer.draw_textured_quad(
                self._image_texture_l,
                self.world_position + self._internal_offset - self._position_offset,
                self._image_size,
                # rotate_angle=angle - 180
            )

        else:
            renderer.draw_textured_quad(
                self._image_texture_r,
                self.world_position + self._internal_offset + self._position_offset,
                self._image_size,
                # rotate_angle=angle
            )
