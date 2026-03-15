"""
_island.py
26. January 2024

an island in the sky

Author:
Nilusink
"""
from __future__ import annotations
from OpenGL.GL import glBindTexture, glGetTexImage, GL_TEXTURE_2D, GL_RGBA
from OpenGL.GL import GL_UNSIGNED_BYTE
from icecream import ic
import pygame as pg
import typing as tp
import math as m
import random
import time

from ..shared import global_vars
from ..render_bindings import renderer
from ..base._textures import textures
from ._base_entity import VisibleGameEntity
from ..logic import Vec2, coord_t, convert_coord
from ..base import Walls


class _PolyMatcher:
    def __init__(self, top, bottom, left, right) -> None:
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"[{self.top}, {self.bottom}, {self.left}, {self.right}]"

    def __repr__(self) -> str:
        return self.__str__()


class Island(VisibleGameEntity):
    _island_single_texture: int = ...

    _island_single_right_texture: int = ...
    _island_single_left_texture: int = ...
    _island_single_top_texture: int = ...
    _island_single_bottom_texture: int = ...

    _island_left_texture: int = ...
    _island_left_inv_texture: int = ...

    _island_middle_texture: int = ...
    _island_middle_inv_texture: int = ...

    _island_top_bottom_texture: int = ...
    _island_left_right_texture: int = ...

    _island_right_texture: int = ...
    _island_right_inv_texture: int = ...

    _island_wall_right_texture: int = ...
    _island_wall_left_texture: int = ...

    _dirt_hole_texture: int = ...
    _dirt_texture: int = ...

    _image_size: tuple[int, int] = (64, 64)
    debug = False

    def __new__(cls, *args, **kwargs):
        # only load texture once
        if cls._island_single_texture is ...:
            cls.load_textures()

        return super(Island, cls).__new__(cls)

    @classmethod
    def load_textures(cls) -> None:
        raise NotImplementedError

    def __init__(
            self,
            pos: coord_t,
            size: coord_t = ...,
            form: list[list[int]] = ...,
            damage: float = ...,
            bounce: float = ...
    ) -> None:
        if size is ... and form is ...:
            raise ValueError("either size or form have to be given!")

        start = convert_coord(pos, Vec2)
        self._size = ... if size is ... else convert_coord(size, Vec2)
        self._form = form
        self._damage = damage
        self._bounce = bounce
        self.mask: pg.Mask = ...

        if form is not ...:
            self._size = Vec2().from_cartesian(
                self._image_size[0] * max(len(r) for r in form),
                self._image_size[1] * len(form)
            )

        super().__init__(
            size=self._size,
            initial_position=start,
            # initial_velocity=Vec2().from_cartesian(4, 0)
        )

        self.add(Walls)
        self.update_rect()

    @classmethod
    def random_between(
            cls,
            x_start: int,
            x_end: int,
            y_start: int,
            y_end: int,
            x_size_start: int,
            x_size_end: int,
            y_size_start: int,
            y_size_end: int
    ) -> tp.Self:
        x = random.randint(x_start, x_end)
        y = random.randint(y_start, y_end)

        x_size = random.randint(x_size_start, x_size_end)
        y_size = random.randint(y_size_start, y_size_end)

        start = Vec2().from_cartesian(x, y)
        size = Vec2().from_cartesian(x_size, y_size)

        return cls(start, size)

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x,
            self.position.y,
            self.size.x,
            self.size.y
        )

    @classmethod
    def _get_block_mask(cls) -> pg.Mask | tuple[pg.Mask, pg.Mask]:
        return pg.Mask(cls._image_size, fill=True)

    def _generate_collision_mask(self) -> None:
        """
        generate the mask used for collision
        """
        # start = time.perf_counter_ns()
        if self._form is ...:
            return super()._generate_collision_mask()

        # collide sprite and rect
        entity_mask = pg.Mask(self.size.xy)
        block_mask = self._get_block_mask()
        special_mask = None

        if isinstance(block_mask, tuple):
            block_mask, special_mask = block_mask

        n_rows = len(self._form)
        n_columns = max(len(row) for row in self._form)
        for row in range(n_rows):
            row_offset = self._image_size[1] * row

            for column in range(n_columns):
                column_offset = self._image_size[0] * column

                try:
                    island_type = self._form[row][column]

                except IndexError:
                    island_type = -1

                if island_type > 0:
                    mask = block_mask
                    if special_mask is not None and island_type == 2:
                        mask = special_mask

                    entity_mask.draw(
                        mask,
                        (column_offset, row_offset)
                    )

        self.mask = entity_mask
        # end = time.perf_counter_ns()
        # calc_time = (end - start) / 1000
        # classname = self.__class__.__name__
        # ic(classname, calc_time, "µs")

    def collide(self, other) -> tuple[int, int] | None:
        """
        more precise collision for islands
        """
        return pg.sprite.collide_mask(self, other)

    def player_contact(self, player, delta: float) -> None:
        if self._damage is not ...:
            player.hit(self._damage)
            player.velocity.y -= min(
                self._damage * delta * player._movement_acceleration / 35,
                800
            )

        if self._bounce is not ...:
            player.velocity.y -= (
                    self._bounce * delta * player._movement_acceleration / 35
            )

    def get_collided_sides(
            self,
            top_collider: tuple[Vec2, pg.Mask],
            right_collider: tuple[Vec2, pg.Mask],
            bottom_collider: tuple[Vec2, pg.Mask],
            left_collider: tuple[Vec2, pg.Mask],
    ) -> tuple[
        tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]
    ]:
        """
        check which sides of a sprite collide with the wall
        """
        top_offset = top_collider[0] - self.position
        top_collides = (
            self.mask.overlap(top_collider[1], top_offset.xy)
        )

        right_offset = right_collider[0] - self.position
        right_collides = (
            self.mask.overlap(right_collider[1], right_offset.xy)
        )

        bottom_offset = bottom_collider[0] - self.position
        bottom_collides = (
            self.mask.overlap(bottom_collider[1], bottom_offset.xy)
        )

        left_offset = left_collider[0] - self.position
        left_collides = (
            self.mask.overlap(left_collider[1], left_offset.xy)
        )

        return (
            top_collides,
            right_collides,
            bottom_collides,
            left_collides
        )

    def gl_draw(self) -> None:
        start_pos = self.world_position

        # check if island is on screen
        if any([
            self.position.x > global_vars.screen_pixels.x + global_vars.world_position.x,
            self.position.x + self.size.x < global_vars.world_position.x
        ]):
            return

        # fill island with dirt
        if self._form is ...:
            n_rows = m.ceil(self.size.y / self._image_size[1])
            n_columns = m.ceil(self.size.x / self._image_size[0])

        else:
            n_rows = len(self._form)
            n_columns = max(len(row) for row in self._form)

        for row in range(n_rows):
            row_offset = self._image_size[1] * row

            for column in range(n_columns):
                texture = self._dirt_texture

                # check adjacent blocks
                block_top = 0
                block_bottom = 0
                block_left = 0
                block_right = 0

                if self._form is not ...:
                    if row > 0:
                        try:
                            block_top = self._form[row - 1][column]

                        except IndexError:
                            block_top = 0

                    if row < n_rows - 1:
                        try:
                            block_bottom = self._form[row + 1][column]

                        except IndexError:
                            block_left = 0

                    if column > 0:
                        try:
                            block_left = self._form[row][column - 1]

                        except IndexError:
                            block_left = 0

                    if column < n_columns - 1:
                        try:
                            block_right = self._form[row][column + 1]

                        except IndexError:
                            block_right = 0

                else:
                    block_top = row != 0
                    block_bottom = row != n_rows - 1
                    block_left = column != 0
                    block_right = column != n_columns - 1

                island_type = -1
                if self._form is not ...:
                    try:
                        island_type = self._form[row][column]

                    except IndexError:
                        continue

                # corners
                poly = _PolyMatcher(
                    top=block_top in (1, 2),
                    bottom=block_bottom in (1, 2),
                    left=block_left in (1, 2),
                    right=block_right in (1, 2)
                )

                # empty
                if island_type == 0:
                    continue

                # hole
                elif island_type == 2:
                    texture = self._dirt_hole_texture

                else:
                    match poly:
                        # single
                        case _PolyMatcher(
                            top=False,
                            bottom=False,
                            left=False,
                            right=False
                        ):
                            texture = self._island_single_texture

                        # dirt
                        case _PolyMatcher(
                            top=True,
                            bottom=True,
                            left=True,
                            right=True
                        ):
                            texture = self._dirt_texture

                        # grass top
                        case _PolyMatcher(
                            top=False,
                            bottom=True,
                            left=True,
                            right=True
                        ):
                            texture = self._island_middle_texture

                        # grass bottom
                        case _PolyMatcher(
                            top=True,
                            bottom=False,
                            left=True,
                            right=True
                        ):
                            texture = self._island_middle_inv_texture

                        # left wall
                        case _PolyMatcher(
                            top=True,
                            bottom=True,
                            left=False,
                            right=True
                        ):
                            texture = self._island_wall_right_texture

                        # right wall
                        case _PolyMatcher(
                            top=True,
                            bottom=True,
                            left=True,
                            right=False
                        ):
                            texture = self._island_wall_left_texture

                        # top and bottom
                        case _PolyMatcher(
                            top=True,
                            bottom=True,
                            left=False,
                            right=False
                        ):
                            texture = self._island_top_bottom_texture

                        # left and right
                        case _PolyMatcher(
                            top=False,
                            bottom=False,
                            left=True,
                            right=True
                        ):
                            texture = self._island_left_right_texture

                        # bottom empty
                        case _PolyMatcher(
                            top=True,
                            bottom=False,
                            left=True,
                            right=True
                        ):
                            texture = self._island_middle_inv_texture

                        # top empty
                        case _PolyMatcher(
                            top=False,
                            bottom=True,
                            left=True,
                            right=True
                        ):
                            texture = self._island_middle_texture

                        # left empty
                        case _PolyMatcher(
                            top=True,
                            bottom=True,
                            left=False,
                            right=True
                        ):
                            texture = self._island_wall_left_texture

                        # right empty
                        case _PolyMatcher(
                            top=True,
                            bottom=True,
                            left=True,
                            right=False
                        ):
                            texture = self._island_wall_right_texture

                        # right top corner
                        case _PolyMatcher(
                            top=False,
                            bottom=True,
                            left=True,
                            right=False
                        ):
                            texture = self._island_right_texture

                        # left top corner
                        case _PolyMatcher(
                            top=False,
                            bottom=True,
                            left=False,
                            right=True
                        ):
                            texture = self._island_left_texture

                        # right bottom corner
                        case _PolyMatcher(
                            top=True,
                            bottom=False,
                            left=True,
                            right=False
                        ):
                            texture = self._island_right_inv_texture

                        # left bottom corner
                        case _PolyMatcher(
                            top=True,
                            bottom=False,
                            left=False,
                            right=True
                        ):
                            texture = self._island_left_inv_texture

                        # top connected
                        case _PolyMatcher(
                            top=True,
                            bottom=False,
                            left=False,
                            right=False
                        ):
                            texture = self._island_single_bottom_texture

                        # bottom connected
                        case _PolyMatcher(
                            top=False,
                            bottom=True,
                            left=False,
                            right=False
                        ):
                            texture = self._island_single_top_texture

                        # left connected
                        case _PolyMatcher(
                            top=False,
                            bottom=False,
                            left=True,
                            right=False
                        ):
                            texture = self._island_single_left_texture

                        # right connected
                        case _PolyMatcher(
                            top=False,
                            bottom=False,
                            left=False,
                            right=True
                        ):
                            texture = self._island_single_right_texture

                        case _:
                            raise ValueError(
                                "idek how you got here",
                                poly
                            )

                column_offset = self._image_size[0] * column
                pos = start_pos + Vec2().from_cartesian(
                    column_offset,
                    row_offset
                )
                size = self._image_size
                renderer.draw_textured_quad(
                    texture,
                    pos,
                    size
                )

        if self.debug:
            debug_surface = self.mask.to_surface()
            renderer.draw_pg_surf((
                self.world_position.x,
                self.world_position.y + self.size.y
            ),
                debug_surface
            )


class GrassIsland(Island):
    @classmethod
    def load_textures(cls) -> None:
        if cls._island_single_texture is not ...:
            return

        cls._island_single_texture, _ = textures.get_texture(
            "grass_single",
            cls._image_size
        )

        cls._island_single_right_texture, _ = textures.get_texture(
            "grass_single_right",
            cls._image_size
        )
        cls._island_single_left_texture, _ = textures.get_texture(
            "grass_single_left",
            cls._image_size
        )
        cls._island_single_top_texture, _ = textures.get_texture(
            "grass_single_top",
            cls._image_size
        )
        cls._island_single_bottom_texture, _ = textures.get_texture(
            "grass_single_bottom",
            cls._image_size
        )

        cls._island_left_texture, _ = textures.get_texture(
            "grass_left",
            cls._image_size,
            mirror="x"
        )
        cls._island_left_inv_texture, _ = textures.get_texture(
            "grass_left_bottom",
            cls._image_size,
            mirror="x"
        )

        cls._island_middle_texture, _ = textures.get_texture(
            "grass_middle",
            cls._image_size,
            mirror="x"
        )
        cls._island_middle_inv_texture, _ = textures.get_texture(
            "grass_middle_bottom",
            cls._image_size,
            mirror="x"
        )

        cls._island_top_bottom_texture, _ = textures.get_texture(
            "grass_top_bottom",
            cls._image_size,
            mirror="x"
        )
        cls._island_left_right_texture, _ = textures.get_texture(
            "grass_left_right",
            cls._image_size,
            mirror="x"
        )

        cls._island_right_texture, _ = textures.get_texture(
            "grass_right",
            cls._image_size,
            mirror="x"
        )
        cls._island_right_inv_texture, _ = textures.get_texture(
            "grass_right_bottom",
            cls._image_size,
            mirror="x"
        )

        cls._island_wall_right_texture, _ = textures.get_texture(
            "grass_wall_right",
            cls._image_size,
            mirror=""
        )
        cls._island_wall_left_texture, _ = textures.get_texture(
            "grass_wall_right",
            cls._image_size,
            mirror="x"
        )

        cls._dirt_texture, _ = textures.get_texture(
            "dirt",
            cls._image_size,
            mirror="x"
        )
        cls._dirt_hole_texture, _ = textures.get_texture(
            "dirt_hole",
            cls._image_size,
            mirror="x"
        )


class BasicScopedIsland(Island):
    _scope: str

    @classmethod
    def load_textures(cls) -> None:
        if cls._island_single_texture is not ...:
            return

        available = textures.get_raw_from_scope(cls._scope)

        cls._island_single_texture, _ = textures.get_texture(
            "single",
            cls._image_size,
            scope=cls._scope
        )

        cls._island_middle_texture, _ = textures.get_texture(
            "top",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )
        cls._island_left_texture, _ = textures.get_texture(
            "top_left",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )
        cls._island_wall_left_texture, _ = textures.get_texture(
            "left",
            cls._image_size,
            mirror="",
            scope=cls._scope
        )
        cls._island_left_inv_texture, _ = textures.get_texture(
            "bottom_left",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )
        cls._island_middle_inv_texture, _ = textures.get_texture(
            "bottom",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )
        cls._island_right_inv_texture, _ = textures.get_texture(
            "bottom_right",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )
        cls._island_wall_right_texture, _ = textures.get_texture(
            "right",
            cls._image_size,
            mirror="",
            scope=cls._scope
        )
        cls._island_right_texture, _ = textures.get_texture(
            "top_right",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )
        cls._dirt_texture, _ = textures.get_texture(
            "center",
            cls._image_size,
            mirror="x",
            scope=cls._scope
        )

        if "special" in available:
            cls._dirt_hole_texture, _ = textures.get_texture(
                "special",
                cls._image_size,
                mirror="",
                scope=cls._scope
            )

        else:
            cls._dirt_hole_texture = cls._dirt_texture

        cls._island_top_bottom_texture, _ = textures.get_texture(
            "top_bottom",
            cls._image_size,
            mirror="",
            scope=cls._scope
        )
        cls._island_left_right_texture, _ = textures.get_texture(
            "left_right",
            cls._image_size,
            mirror="",
            scope=cls._scope
        )

        if "single_right" in available:
            cls._island_single_right_texture, _ = textures.get_texture(
                "single_right",
                cls._image_size,
                mirror="",
                scope=cls._scope
            )

        else:
            cls._island_single_right_texture = cls._island_single_texture

        if "single_left" in available:
            cls._island_single_left_texture, _ = textures.get_texture(
                "single_left",
                cls._image_size,
                mirror="",
                scope=cls._scope
            )

        else:
            cls._island_single_left_texture = cls._island_single_texture

        if "single_top" in available:
            cls._island_single_top_texture, _ = textures.get_texture(
                "single_top",
                cls._image_size,
                mirror="",
                scope=cls._scope
            )

        else:
            cls._island_single_top_texture = cls._island_single_texture

        if "single_bottom" in available:
            cls._island_single_bottom_texture, _ = textures.get_texture(
                "single_bottom",
                cls._image_size,
                mirror="",
                scope=cls._scope
            )

        else:
            cls._island_single_bottom_texture = cls._island_single_texture


class GrayBrickIsland(BasicScopedIsland):
    _scope = "bricks_gray"
    _image_size = (24*3, 24*3)


class GreenBrickIsland(BasicScopedIsland):
    _scope = "bricks_green"
    _image_size = (24*3, 24*3)


class SingleBlockIsland(Island):
    _texture: tuple[str, str]
    _special_texture: [str, str] = None  # optional

    @classmethod
    def load_textures(cls) -> None:
        if cls._island_single_texture is not ...:
            return

        cls._island_single_texture, _ = textures.get_texture(
            cls._texture[1],
            cls._image_size,
            scope=cls._texture[0]
        )

        cls._island_single_right_texture = cls._island_single_texture
        cls._island_single_left_texture = cls._island_single_texture
        cls._island_single_top_texture = cls._island_single_texture
        cls._island_single_bottom_texture = cls._island_single_texture

        cls._island_left_texture = cls._island_single_texture
        cls._island_left_inv_texture = cls._island_single_texture

        cls._island_middle_texture = cls._island_single_texture
        cls._island_middle_inv_texture = cls._island_single_texture

        cls._island_top_bottom_texture = cls._island_single_texture
        cls._island_left_right_texture = cls._island_single_texture

        cls._island_right_texture = cls._island_single_texture
        cls._island_right_inv_texture = cls._island_single_texture

        cls._island_wall_right_texture = cls._island_single_texture
        cls._island_wall_left_texture = cls._island_single_texture

        cls._dirt_texture = cls._island_single_texture

        if cls._special_texture is not None:
            cls._dirt_hole_texture, _ = textures.get_texture(
                cls._special_texture[1],
                cls._image_size,
                scope=cls._special_texture[0]
            )

        else:
            cls._dirt_hole_texture = cls._island_single_texture

    @classmethod
    def _get_block_mask(cls) -> pg.Mask | tuple[pg.Mask, pg.Mask]:
        # get default mask
        glBindTexture(GL_TEXTURE_2D, cls._island_single_texture)
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        surface = pg.image.frombuffer(data, cls._image_size, "RGBA")
        # surface = pg.transform.flip(surface, False, False)
        normal_mask = pg.mask.from_surface(surface)

        if cls._special_texture is None:
            return normal_mask

        # get special texture
        glBindTexture(GL_TEXTURE_2D, cls._dirt_hole_texture)
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        surface = pg.image.frombuffer(data, cls._image_size, "RGBA")
        # surface = pg.transform.flip(surface, False, False)
        special_mask = pg.mask.from_surface(surface)

        return normal_mask, special_mask


class PillarIsland(SingleBlockIsland):
    _texture = ("columns", "1")
    _special_texture = ("columns", "1_1")
    _image_size = (64*3, 112*3)


class PlatformIsland1(SingleBlockIsland):
    _texture = ("platforms", "1")
    _image_size = (46*3, 13*3)


class PlatformIsland2(SingleBlockIsland):
    _texture = ("platforms", "2")
    _image_size = (44*3, 11*3)
