"""
_island.py
30.03.2026

visual representation of an island

Author:
Nilusink
"""

from __future__ import annotations

import math as m
import typing as tp
from dataclasses import dataclass

import pygame as pg
from icecream import ic

from amoginarium import pv
from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared import IslandCIDs
from amoginarium.shared.utility import Vec2, WtfError, convert_coord, coord_t

from ..textures import textures
from ._synced_entities import SyncedGraphicsEntity


class _PolyMatcher:
    """Helper class for matching polygon edges."""

    __slots__ = ("top", "bottom", "left", "right")
    top: bool
    bottom: bool
    left: bool
    right: bool

    def __init__(self, top: bool, bottom: bool, left: bool, right: bool) -> None:
        """
        Helper class for matching polygon edges.

        :param top: Whether the top edge is active.
        :param bottom: Whether the bottom edge is active.
        :param left: Whether the left edge is active.
        :param right: Whether the right edge is active.
        """
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def __str__(self) -> str:
        """:return: String formatted as [top, bottom, left, right]."""
        return f"[{self.top}, {self.bottom}, {self.left}, {self.right}]"

    def __repr__(self) -> str:
        """:return: String representation via __str__."""
        return self.__str__()


@dataclass(frozen=True)
class IslandTextures:
    island_single_texture: int
    island_single_right_texture: int
    island_single_left_texture: int
    island_single_top_texture: int
    island_single_bottom_texture: int
    island_left_texture: int
    island_left_inv_texture: int
    island_middle_texture: int
    island_middle_inv_texture: int
    island_top_bottom_texture: int
    island_left_right_texture: int
    island_right_texture: int
    island_right_inv_texture: int
    island_wall_right_texture: int
    island_wall_left_texture: int
    dirt_hole_texture: int
    dirt_texture: int


class _IslandTextureManager:
    __slots__ = ["_textures"]

    def __init__(self) -> None:
        self._textures: tp.MutableMapping[
            type[Island], tp.MutableMapping[int, IslandTextures]
        ] = {}

    @staticmethod
    def _load_from_scope(scope: str, size: tuple[int, int]) -> IslandTextures:
        available = textures.get_raw_from_scope(scope)

        out_tex: tp.MutableMapping[str, int] = {}

        out_tex["island_single_texture"], _ = textures.get_texture(
            "single", size, scope=scope
        )

        out_tex["island_middle_texture"], _ = textures.get_texture(
            "top", size, mirror="x", scope=scope
        )
        out_tex["island_left_texture"], _ = textures.get_texture(
            "top_left", size, mirror="x", scope=scope
        )
        out_tex["island_wall_left_texture"], _ = textures.get_texture(
            "left", size, mirror="", scope=scope
        )
        out_tex["island_left_inv_texture"], _ = textures.get_texture(
            "bottom_left", size, mirror="x", scope=scope
        )
        out_tex["island_middle_inv_texture"], _ = textures.get_texture(
            "bottom", size, mirror="x", scope=scope
        )
        out_tex["island_right_inv_texture"], _ = textures.get_texture(
            "bottom_right", size, mirror="x", scope=scope
        )
        out_tex["island_wall_right_texture"], _ = textures.get_texture(
            "right", size, mirror="", scope=scope
        )
        out_tex["island_right_texture"], _ = textures.get_texture(
            "top_right", size, mirror="x", scope=scope
        )
        out_tex["dirt_texture"], _ = textures.get_texture(
            "center", size, mirror="x", scope=scope
        )

        if "special" in available:
            out_tex["dirt_hole_texture"], _ = textures.get_texture(
                "special", size, mirror="", scope=scope
            )

        else:
            out_tex["dirt_hole_texture"] = out_tex["dirt_texture"]

        out_tex["island_top_bottom_texture"], _ = textures.get_texture(
            "top_bottom", size, mirror="", scope=scope
        )
        out_tex["island_left_right_texture"], _ = textures.get_texture(
            "left_right", size, mirror="", scope=scope
        )

        if "single_right" in available:
            out_tex["island_single_right_texture"], _ = textures.get_texture(
                "single_right", size, mirror="", scope=scope
            )

        else:
            out_tex["island_single_right_texture"] = out_tex["island_single_texture"]

        if "single_left" in available:
            out_tex["island_single_left_texture"], _ = textures.get_texture(
                "single_left", size, mirror="", scope=scope
            )

        else:
            out_tex["island_single_left_texture"] = out_tex["island_single_texture"]

        if "single_top" in available:
            out_tex["island_single_top_texture"], _ = textures.get_texture(
                "single_top", size, mirror="", scope=scope
            )

        else:
            out_tex["island_single_top_texture"] = out_tex["island_single_texture"]

        if "single_bottom" in available:
            out_tex["island_single_bottom_texture"], _ = textures.get_texture(
                "single_bottom", size, mirror="", scope=scope
            )

        else:
            out_tex["island_single_bottom_texture"] = out_tex["island_single_texture"]

        return IslandTextures(**out_tex)

    def get_textures(self, island: type[Island], texture_size: int) -> IslandTextures:
        if island in self._textures:
            if texture_size in self._textures[island]:
                ic("return existing")
                return self._textures[island][texture_size]

        else:
            self._textures[island] = {}

        # load textures
        t: IslandTextures
        try:
            t = self._load_from_scope(island.get_scope(), (texture_size, texture_size))

        except KeyError:
            ic.outputFunction("Failed getting textures from ", island)
            raise RuntimeError

        self._textures[island][texture_size] = t
        return self._textures[island][texture_size]


ISLAND_TEXTURE_MANAGER = _IslandTextureManager()


class Island(SyncedGraphicsEntity):
    _scope: str = ...
    _textures: IslandTextures = ...

    _image_size: tuple[int, int] = (64, 64)
    debug = False

    def __new__(cls, *args, **kwargs):
        # only load texture once
        if cls._textures is ...:
            cls.load_textures()

        return super().__new__(cls)

    @classmethod
    def load_textures(cls) -> None:
        cls._textures = ISLAND_TEXTURE_MANAGER.get_textures(cls, cls._image_size[0])

    @classmethod
    def get_scope(cls) -> str:
        return cls._scope

    def __init__(
        self,
        sync_id: int,
        size: coord_t = ...,
        form: list[list[int]] = ...,
    ) -> None:
        if size is ... and form is ...:
            raise ValueError("either size or form have to be given!")

        self._size = ... if size is ... else convert_coord(size, Vec2)
        self._form = form
        self.mask: pg.Mask = ...

        if form is not ...:
            self._size = Vec2().from_cartesian(
                self._image_size[0] * max(len(r) for r in form),
                self._image_size[1] * len(form),
            )

        super().__init__(sync_id=sync_id)

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        start_pos = self.world_position
        world_position = pv.global_vars.get_world_position()
        resolution = pv.global_vars.resolution_screen

        # check if island is on screen
        if (
            self.pos.x + self.size.x < world_position.x
            or self.pos.x > world_position.x + resolution.x
            or self.pos.y + self.size.y < world_position.y
            or self.pos.y > world_position.y + resolution.y
        ):
            return

        if self._highlight:
            renderer.start_stencil(True)

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
                texture = self._textures.dirt_texture

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
                    right=block_right in (1, 2),
                )

                # empty
                if island_type == 0:
                    continue

                # hole
                if island_type == 2:
                    texture = self._textures.dirt_hole_texture

                else:
                    match poly:
                        # single
                        case _PolyMatcher(
                            top=False, bottom=False, left=False, right=False
                        ):
                            texture = self._textures.island_single_texture

                        # dirt
                        case _PolyMatcher(top=True, bottom=True, left=True, right=True):
                            texture = self._textures.dirt_texture

                        # grass top
                        case _PolyMatcher(
                            top=False, bottom=True, left=True, right=True
                        ):
                            texture = self._textures.island_middle_texture

                        # grass bottom
                        case _PolyMatcher(
                            top=True, bottom=False, left=True, right=True
                        ):
                            texture = self._textures.island_middle_inv_texture

                        # left wall
                        case _PolyMatcher(
                            top=True, bottom=True, left=False, right=True
                        ):
                            texture = self._textures.island_wall_right_texture

                        # right wall
                        case _PolyMatcher(
                            top=True, bottom=True, left=True, right=False
                        ):
                            texture = self._textures.island_wall_left_texture

                        # top and bottom
                        case _PolyMatcher(
                            top=True, bottom=True, left=False, right=False
                        ):
                            texture = self._textures.island_top_bottom_texture

                        # left and right
                        case _PolyMatcher(
                            top=False, bottom=False, left=True, right=True
                        ):
                            texture = self._textures.island_left_right_texture

                        # bottom empty
                        case _PolyMatcher(
                            top=True, bottom=False, left=True, right=True
                        ):
                            texture = self._textures.island_middle_inv_texture

                        # top empty
                        case _PolyMatcher(
                            top=False, bottom=True, left=True, right=True
                        ):
                            texture = self._textures.island_middle_texture

                        # left empty
                        case _PolyMatcher(
                            top=True, bottom=True, left=False, right=True
                        ):
                            texture = self._textures.island_wall_left_texture

                        # right empty
                        case _PolyMatcher(
                            top=True, bottom=True, left=True, right=False
                        ):
                            texture = self._textures.island_wall_right_texture

                        # right top corner
                        case _PolyMatcher(
                            top=False, bottom=True, left=True, right=False
                        ):
                            texture = self._textures.island_right_texture

                        # left top corner
                        case _PolyMatcher(
                            top=False, bottom=True, left=False, right=True
                        ):
                            texture = self._textures.island_left_texture

                        # right bottom corner
                        case _PolyMatcher(
                            top=True, bottom=False, left=True, right=False
                        ):
                            texture = self._textures.island_right_inv_texture

                        # left bottom corner
                        case _PolyMatcher(
                            top=True, bottom=False, left=False, right=True
                        ):
                            texture = self._textures.island_left_inv_texture

                        # top connected
                        case _PolyMatcher(
                            top=True, bottom=False, left=False, right=False
                        ):
                            texture = self._textures.island_single_bottom_texture

                        # bottom connected
                        case _PolyMatcher(
                            top=False, bottom=True, left=False, right=False
                        ):
                            texture = self._textures.island_single_top_texture

                        # left connected
                        case _PolyMatcher(
                            top=False, bottom=False, left=True, right=False
                        ):
                            texture = self._textures.island_single_left_texture

                        # right connected
                        case _PolyMatcher(
                            top=False, bottom=False, left=False, right=True
                        ):
                            texture = self._textures.island_single_right_texture

                        case _:
                            raise WtfError("idek how you got here", poly)

                column_offset = self._image_size[0] * column
                pos = start_pos + Vec2().from_cartesian(column_offset, row_offset)
                size = self._image_size
                renderer.draw_textured_quad(texture, pos, size, layer=layer)

        if self.debug:
            debug_surface = self.mask.to_surface()
            # TODO: mytodo - reimplement other way of debug!
            # renderer.draw_pg_surf((
            #     self.world_position.x,
            #     self.world_position.y + self.size.y
            # ),
            #     debug_surface
            # )

        if self._highlight:
            renderer.enable_stencil(True)

            renderer.draw_rect(
                self.world_position - self.size / 2, self.size * 2, (1, 1, 1, 0.5)
            )

            renderer.disable_stencil()


class GrassIsland(Island):
    _scope = "dirt_islands"
    _CID = IslandCIDs.grass_island


class GrayBrickIsland(Island):
    _scope = "bricks_gray"
    _CID = IslandCIDs.gray_brick_island


class GreenBrickIsland(Island):
    _scope = "bricks_green"
    _CID = IslandCIDs.green_brick_island


__islands: tp.Iterable[type[Island]] = [
    GrassIsland,
    GrayBrickIsland,
    GreenBrickIsland,
]

ISLANDS: tp.Mapping[str, type[Island]] = {c.cid(): c for c in __islands}
