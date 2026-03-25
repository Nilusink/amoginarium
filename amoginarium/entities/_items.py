"""
_items.py
12.03.2026

various items that are not weapons

Author:
Nilusink
"""
from typing import Tuple

from OpenGL.GL import glBindTexture, glGetTexImage, GL_TEXTURE_2D, GL_RGBA
from OpenGL.GL import GL_UNSIGNED_BYTE
from icecream import ic
import typing as tp
import pygame as pg
import math as m

from ..shared import PlayerLike, BaseEntityLike, ItemLike, WeaponLike, \
    ItemSlot
from ..logic import coord_t, convert_coord, Vec2
from ..entities import CollisionDestroyed, Updated, GravityAffected, WallCollider, Drawn
from ._base_entity import PositionedEntity, VisibleGameEntity
from ..base._textures import textures
from ..render_bindings import renderer
from ._animation import Animation


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
            # used_callback: tp.Callable[[int], bool],
            parent_position_offset: coord_t
    ) -> None:
        self._position_offset = convert_coord(parent_position_offset, Vec2)
        self._uses_left = self._max_uses
        self._used_callback = None

        square_size = max(self._image_size)
        self._internal_offset = Vec2().from_cartesian(
            (square_size - self._image_size[0]) / 2,
            (square_size - self._image_size[1]) / 2
        )

        super().__init__(
            parent.position + self._position_offset,
            Vec2().from_cartesian(square_size, square_size),
            parent
        )

        self._current_angle = Vec2().from_cartesian(1, 0)

        self.load_textures()
        self._generate_collision_mask()
        self.update_rect()

    # noinspection PyTypeChecker
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

    def get_icon(self) -> tuple[int, tuple[int, int]]:
        """
        return the items texture and size
        """
        return self._image_texture_r, self._image_size

    def add_used_callback(self, callback: tp.Callable[[int], bool]) -> None:
        self._used_callback = callback

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

        self._mask_right_surf = pg.transform.flip(
            self._mask_left_surf,
            True,
            False
        )
        self._update_mask()

    def _update_mask(self) -> None:
        angle = self._current_angle.angle * 180 / m.pi
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
        if self._used_callback and self._used_callback(1):
            self._uses_left = self._max_uses

        else:
            super().kill()

    def update(self, delta: float) -> None:
        self.update_rect()
        self._update_mask()

    def draw_at(
            self,
            position: Vec2,
            angle: float,
            size_fac: float = 1,
            convert_global: bool = True
    ) -> None:
        debug_surface = self.mask.to_surface()
        renderer.draw_pg_surf(
            (
                self.world_position.x,
                self.world_position.y + self.size.y
            ),
            debug_surface,
            convert_global=convert_global
        )

        renderer.draw_rect(
            self.world_position,
            self.size,
            (1, 0, 0, .2),
            convert_global=convert_global
        )

    def reset(self) -> None:
        self._uses_left = self._max_uses


class Shield(BaseItem):
    _image_name: tuple[str, str] | str = ("Shield_6", "4")
    _image_size: tuple[int, int] = (45, 80)
    _max_uses: int = 200  # acts as HP for shield

    def __init__(
            self,
            parent: PlayerLike,
            # used_callback: tp.Callable[[int], bool],
            parent_position_offset: coord_t
    ) -> None:
        super().__init__(parent, parent_position_offset)

        self._in_use = False
        # self.add(CollisionDestroyed)

    @property
    def hp(self) -> float:
        return self._uses_left

    def use(self) -> None:
        """
        start using the item
        """
        if not self._in_use:
            self._in_use = True
            self.add(CollisionDestroyed)

    def stop_use(self) -> None:
        """
        stop using the item
        """
        if self._in_use:
            self._in_use = False
            self.remove(CollisionDestroyed)

    def hit(self, damage: float, hit_by: BaseEntityLike = ...) -> None:
        self._uses_left -= damage

        if self._uses_left <= 0:
            self.kill(hit_by)

    def draw_at(
            self,
            position: Vec2,
            angle: float,
            size_fac: float = 1,
            convert_global: bool = True
    ) -> None:
        angle = angle % 360
        delta = self._position_offset.copy() * size_fac
        delta.angle += angle * (m.pi / 180)

        size = self.size * size_fac

        self._current_angle = delta

        if self._in_use:
            self.position = position + delta - size / 2
            own_pos = self.world_position if convert_global else self.position
            if 90 < angle < 270:
                renderer.draw_textured_quad(
                    self._image_texture_l,
                    own_pos + self._internal_offset,
                    (
                        self._image_size[0] * size_fac,
                        self._image_size[1] * size_fac
                    ),
                    rotate_angle=angle - 180,
                    convert_global=convert_global
                )

            else:
                renderer.draw_textured_quad(
                    self._image_texture_r,
                    own_pos + self._internal_offset,
                    (
                        self._image_size[0] * size_fac,
                        self._image_size[1] * size_fac
                    ),
                    rotate_angle=angle,
                    convert_global=convert_global
                )

        else:
            size = Vec2().from_cartesian(*self._image_size) * size_fac
            self.position = position - size / 4
            own_pos = self.world_position if convert_global else self.position
            if 90 < angle < 270:
                renderer.draw_textured_quad(
                    self._image_texture_l,
                    own_pos,
                    size / 2,
                    rotate_angle=angle - 180,
                    convert_global=convert_global
                )

            else:
                renderer.draw_textured_quad(
                    self._image_texture_r,
                    own_pos,
                    size / 2,
                    rotate_angle=angle,
                    convert_global=convert_global
                )


class HealingPotion(BaseItem):
    _image_name = ("potions", "empty")
    _empty_mask = ("potions", "empty_mask")
    _image_size = (32, 32)
    _heal_per_sec = 20
    _max_uses = 80

    @classmethod
    def load_textures(cls) -> None:
        if cls._image_texture_r is not ...:
            return

        cls._mask_texture, _ = textures.get_texture(
            cls._empty_mask[1],
            cls._image_size,
            scope=cls._empty_mask[0]
        )

        super().load_textures()

    def __init__(
            self,
            parent: PlayerLike,
            parent_position_offset: coord_t
    ) -> None:
        super().__init__(parent, parent_position_offset)
        self._drinking = False

        self._target_rotation = 0
        self._f_velocity = 0
        self._f_tilt = 0

    def use(self) -> None:
        self._drinking = True

    def stop_use(self) -> None:
        self._drinking = False

    def update(self, delta: float) -> None:
        if self._drinking:
            # noinspection PyTypeChecker
            heal = min(
                self._uses_left,
                self._heal_per_sec * delta
            )
            if self.parent.heal(heal):
                self._uses_left -= heal

            if self._uses_left <= 0:
                self.kill()

        stiffness = .2
        damping = .9

        # target = -self._target_rotation
        # acceleration = (target - self._f_tilt) * stiffness
        # self._f_velocity += acceleration #+ self.parent.acceleration.x * -.05
        # self._f_velocity *= damping
        # self._f_tilt += self._f_velocity

        target = -self._target_rotation
        acceleration = (target - self._f_tilt) * stiffness

        # acceleration influence
        acc_mag, acc_angle = self.parent.acceleration.polar
        acc_angle *= 180 / m.pi

        acceleration += m.sin(m.radians(acc_angle)) * acc_mag \
                        * self.parent.acceleration.length / 500

        self._f_velocity += acceleration
        self._f_velocity *= damping
        self._f_tilt += self._f_velocity

        super().update(delta)

    def draw_at(
            self,
            position: Vec2,
            angle: float,
            size_fac: float = 1,
            convert_global: bool = False
    ) -> None:
        self._target_rotation = angle
        angle = angle % 360
        self.position = position - self.size / 2

        pos = self.world_position + self._internal_offset
        pos += self._position_offset

        offset = self._position_offset
        own_pos = self.world_position if convert_global else self.position

        # noinspection PyTypeChecker
        renderer.apply_stencil(
            renderer.draw_textured_quad,
            False,
            self._mask_texture,
            own_pos + self._internal_offset + offset,
            self._image_size,
            rotate_angle=angle - (180 if 90 < angle < 270 else 0),
            convert_global=convert_global
        )

        fill_line = 5 + (self.size.y - 10) \
                    * (1 - self._uses_left / self._max_uses)
        renderer.draw_polygon(
            [
                own_pos + offset + Vec2().from_cartesian(
                    -self.size.x,
                    self.size.y
                ),
                own_pos + offset + Vec2().from_cartesian(
                    2 * self.size.x,
                    self.size.y
                ),
                own_pos + offset + Vec2().from_cartesian(
                    self.size.x / 2, fill_line
                ) + Vec2().from_polar(
                    (self._target_rotation + self._f_tilt) * m.pi / 180,
                    self.size.x) + Vec2().from_cartesian(
                    0, 5
                ),
                own_pos + offset + Vec2().from_cartesian(
                    self.size.x / 2, fill_line
                ) - Vec2().from_polar(
                    (self._target_rotation + self._f_tilt) * m.pi / 180,
                    self.size.x) + Vec2().from_cartesian(
                    0, 5
                ),
            ],
            (0, .8, 0),
            convert_global=convert_global
        )

        renderer.disable_stencil()

        if 90 < angle < 270:
            renderer.draw_textured_quad(
                self._image_texture_l,
                own_pos + self._internal_offset + self._position_offset,
                self._image_size,
                rotate_angle=angle - 180,
                convert_global=convert_global
            )

        else:
            renderer.draw_textured_quad(
                self._image_texture_r,
                own_pos + self._internal_offset + self._position_offset,
                self._image_size,
                rotate_angle=angle,
                convert_global=convert_global
            )


class JetBag(BaseItem):
    _image_name: tuple[str, str] | str = ("missiles", "Missile02F")
    _image_size: tuple[int, int] = (32, 64)
    _animation_scope: str = "flame"
    _animation_size: tuple[int, int] = (32, 32)
    _animation_textures: list[int] = ...
    _max_uses: int = 5
    _reload_per_second: float = .2
    _recoil_factor = 1

    @classmethod
    def load_textures(cls) -> None:
        if cls._animation_textures is not ...:
            return

        cls._animation_textures = [
            t[0] for t in
            textures.get_all_from_scope(
                cls._animation_scope,
                cls._animation_size
            )
        ]

        super().load_textures()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._in_use = False
        self._facing = True
        self._size_fac = 1

        self._animation = Animation(
            self._animation_textures,
            self._animation_size,
            .05,
            position_reference=self._flame_position,
            loop=True
        )

    def _flame_position(self) -> Vec2:
        return self.position + Vec2().from_cartesian(
            self.size.x / 2 + self._position_offset.x
            * (1 if self._facing else -1),
            self.size.y / 2 + self._position_offset.y + 36
        )

    def use(self) -> None:
        self._in_use = True
        if self._uses_left > 0:
            self._animation.play()

    def stop_use(self) -> None:
        self._in_use = False
        self._animation.stop()

    def kill(self, killed_by=...) -> None:
        self._animation.stop()
        super().kill(killed_by)

    def update(self, delta: float) -> None:
        if self._in_use:
            if self._uses_left > 0:
                self._uses_left -= delta

                if hasattr(self.parent, "_movement_acceleration"):
                    # noinspection PyProtectedMember
                    recoil = Vec2().from_cartesian(
                        0,
                        -self.parent._movement_acceleration
                    )
                    recoil *= self._recoil_factor
                    self.parent.add_acceleration(recoil)

            else:
                if self._animation.playing:
                    self._animation.stop()

        elif self.parent.on_ground:
            if self._uses_left < self._max_uses:
                self._uses_left = min(
                    self._uses_left + self._reload_per_second * delta,
                    self._max_uses
                )

    def draw_at(
            self,
            position: Vec2,
            angle: float,
            size_fac: float = 1,
            convert_global: bool = True
    ) -> None:
        angle = angle % 360

        size = self.size * size_fac
        self._size_fac = size_fac

        self.position = position - size / 2

        own_pos = self.world_position if convert_global else self.position

        if 90 < angle < 270:
            pos = own_pos + self._internal_offset * size_fac
            pos -= self._position_offset * size_fac
            renderer.draw_textured_quad(
                self._image_texture_l,
                pos,
                (
                    self._image_size[0] * size_fac,
                    self._image_size[1] * size_fac
                ),
                convert_global=convert_global
            )
            self._facing = False

        else:
            pos = own_pos + self._internal_offset * size_fac
            pos += self._position_offset * size_fac
            renderer.draw_textured_quad(
                self._image_texture_r,
                pos,
                (
                    self._image_size[0] * size_fac,
                    self._image_size[1] * size_fac
                ),
                convert_global=convert_global
            )
            self._facing = True


class VisibleItem(VisibleGameEntity):
    _parent: ItemSlot
    _drop_timeout = 1

    def __init__(
            self,
            item: ItemLike | WeaponLike
    ) -> None:
        self._item = item
        self._visible = False
        self.size = item._size.copy()
        self._current_timeout = 0
        super().__init__()
        self.remove(GravityAffected, Drawn, CollisionDestroyed, Updated)

    @property
    def parent(self) -> ItemSlot | None:
        if self._parent is ...:
            return None

        return self._parent

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def item(self) -> ItemLike | WeaponLike:
        return self._item

    def hide(self) -> None:
        self._visible = False
        if not self.parent:
            self.remove(Drawn)

    def show(self) -> None:
        self._visible = True
        self.add(Drawn)

    def hit(self, damage: float, hit_by=...) -> None:
        if self._current_timeout > 0:
            return

        if hasattr(hit_by, "pickup_item"):
            hit_by.pickup_item(self)
            self._current_timeout = self._drop_timeout

    def set_parent(self, parent: ItemSlot) -> None:
        self._parent = parent
        self.remove(GravityAffected, Drawn, CollisionDestroyed, Updated)

    def remove_parent(self, at_pos: Vec2, velocity: Vec2 = ...) -> None:
        self._parent = ...
        self.acceleration *= 0
        self.velocity *= 0
        self.position = at_pos.copy()
        self._current_timeout = self._drop_timeout

        ic(at_pos, velocity)

        if velocity is not ...:
            self.velocity.x = velocity.x
            self.velocity.y = velocity.y

        self.add(GravityAffected, Drawn, CollisionDestroyed, Updated)

    def get_icon(self) -> tuple[int, tuple[int, int]]:
        return self._item.get_icon()

    def draw_at(
            self,
            position: Vec2,
            angle: float,
            size_fac: float = 1,
            convert_global: bool = True
    ) -> None:
        ic(position)
        self._item.draw_at(position, angle, size_fac, convert_global)

    def update(self, delta: float) -> None:
        if self.parent:
            return

        self._current_timeout -= delta

        # wall stuff
        if self._current_timeout <= self._drop_timeout - .1:
            res = WallCollider.collides_with(self)
            if res:
                # wall, pos = res
                self.acceleration *= 0
                self.velocity *= 0

        super().update(delta)

    def gl_draw(self) -> None:
        if self.parent and not self.visible:
            return

        self._item.draw_at(
            self.position + Vec2().from_cartesian(
                0,
                -20 - m.sin(self._current_t*2) * 10
            ),
            0
        )
