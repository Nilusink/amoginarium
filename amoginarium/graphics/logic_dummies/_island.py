"""
Visual representation of an Island.

| Path: amoginarium/graphics/logic_dummies/_island.py
| Project: amoginarium
| Created: 30.03.2026
| Authors: Nilusink
"""

from __future__ import annotations

import math as m
import typing as tp
from dataclasses import dataclass
from types import EllipsisType

from icecream import ic

from amoginarium import pv
from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared import IslandCIDs
from amoginarium.shared.utility import clamp, convert_coord, Vec2

from ..textures import textures
from ._synced_entities import SyncedGraphicsEntity

if tp.TYPE_CHECKING:
    import pygame as pg

    from amoginarium.shared.utility import coord_t


# island types
_ISLAND_TYPE_AIR: int = 0
_ISLAND_TYPE_FILLED: int
_ISLAND_TYPE_HOLE: int = 2


def _l_get[A, B](
    lst: tp.Sequence[A],
    index: int,
    default: B = None,
    *,
    default_on_neg: bool = False,
) -> A | B:
    """
    Get list index with default.

    :param lst: list to get from
    :param index: list index
    :param default: default value
    :param default_on_neg: return default on negative values
    :returns: value if index is valid, else default
    """
    if default_on_neg and index < 0:
        return default

    try:
        return lst[index]

    except IndexError:
        return default


@dataclass(frozen=True)
class IslandTextures:
    """Island texture dataclass."""

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
        """Get textures for specified island."""
        if island in self._textures:
            if texture_size in self._textures[island]:
                return self._textures[island][texture_size]

        else:
            self._textures[island] = {}

        # load textures
        t: IslandTextures
        try:
            t = self._load_from_scope(island.get_scope(), (texture_size, texture_size))

        except KeyError as e:
            ic.outputFunction("Failed getting textures from ", island)
            raise RuntimeError from e

        self._textures[island][texture_size] = t
        return self._textures[island][texture_size]


ISLAND_TEXTURE_MANAGER = _IslandTextureManager()


class Island(SyncedGraphicsEntity):
    _scope: str = ...
    _textures: IslandTextures = ...

    _image_size: tuple[int, int] = (64, 64)

    def __new__(cls, *_args: tp.Any, **_kwargs: tp.Any) -> tp.Self:
        # only load texture once
        if cls._textures is ...:
            cls.load_textures()

        return super().__new__(cls)  # type: ignore noqa: PGH003

    @classmethod
    def load_textures(cls) -> None:
        """Load island textures."""
        cls._textures = ISLAND_TEXTURE_MANAGER.get_textures(cls, cls._image_size[0])

    @classmethod
    def get_scope(cls) -> str:
        """Island texture scope."""
        return cls._scope

    def __init__(
        self,
        sync_id: int,
        size: coord_t | EllipsisType = ...,
        form: list[list[int]] | EllipsisType = ...,
    ) -> None:
        if size is ... and form is ...:
            msg = "size or form have to be given!"
            raise ValueError(msg)

        self._size = (
            ... if isinstance(size, EllipsisType) else convert_coord(size, Vec2)
        )
        self._form = form
        self.mask: pg.Mask | EllipsisType = ...

        if not isinstance(form, EllipsisType):
            self._size = Vec2().from_cartesian(
                self._image_size[0] * max(len(r) for r in form),
                self._image_size[1] * len(form),
            )

        super().__init__(sync_id=sync_id)

        self.load_textures()
        self.__parsed_island: list[list[int]] = []
        self.__parse_island()

    def __parse_island(self) -> None:
        """pre-parse the island textures."""
        # fill island with dirt
        if isinstance(self._form, EllipsisType):
            n_rows = m.ceil(self._size.y / self._image_size[1])
            n_columns = m.ceil(self._size.x / self._image_size[0])

        else:
            n_rows = len(self._form)
            n_columns = max(len(row) for row in self._form)

        # create texture map
        texture_map = {
            # single
            (False, False, False, False): self._textures.island_single_texture,
            # dirt
            (True, True, True, True): self._textures.dirt_texture,
            # grass top
            (False, True, True, True): self._textures.island_middle_texture,
            # grass bottom
            (True, False, True, True): self._textures.island_middle_inv_texture,
            # left wall
            (True, True, False, True): self._textures.island_wall_right_texture,
            # right wall
            (True, True, True, False): self._textures.island_wall_left_texture,
            # top and bottom
            (True, True, False, False): self._textures.island_top_bottom_texture,
            # left and right
            (False, False, True, True): self._textures.island_left_right_texture,
            # right top corner
            (False, True, True, False): self._textures.island_right_texture,
            # left top corner
            (False, True, False, True): self._textures.island_left_texture,
            # right bottom corner
            (True, False, True, False): self._textures.island_right_inv_texture,
            # left bottom corner
            (True, False, False, True): self._textures.island_left_inv_texture,
            # top connected
            (True, False, False, False): self._textures.island_single_bottom_texture,
            # bottom connected
            (False, True, False, False): self._textures.island_single_top_texture,
            # left connected
            (False, False, True, False): self._textures.island_single_left_texture,
            # right connected
            (False, False, False, True): self._textures.island_single_right_texture,
        }

        self.__parsed_island = [[0] * n_columns for _ in range(n_rows)]

        # parse island
        for row in range(n_rows):
            for column in range(n_columns):
                island_type = -1

                if not isinstance(self._form, EllipsisType):
                    try:
                        island_type = self._form[row][column]

                    except IndexError:
                        continue

                    # empty
                    if island_type == _ISLAND_TYPE_AIR:
                        continue

                    # try to get adjacent blocks, else treat as air
                    block_top = _l_get(
                        _l_get(self._form, row - 1, [], default_on_neg=True),
                        column,
                        0,
                        default_on_neg=True,
                    )
                    block_bottom = _l_get(
                        _l_get(self._form, row + 1, [], default_on_neg=True),
                        column,
                        0,
                        default_on_neg=True,
                    )
                    block_left = _l_get(
                        _l_get(self._form, row, [], default_on_neg=True),
                        column - 1,
                        0,
                        default_on_neg=True,
                    )
                    block_right = _l_get(
                        _l_get(self._form, row, [], default_on_neg=True),
                        column + 1,
                        0,
                        default_on_neg=True,
                    )

                else:
                    block_top = row != 0
                    block_bottom = row != n_rows - 1
                    block_left = column != 0
                    block_right = column != n_columns - 1

                # hole
                if island_type == _ISLAND_TYPE_HOLE:
                    texture = self._textures.dirt_hole_texture

                else:
                    poly = (
                        block_top in (1, 2),
                        block_bottom in (1, 2),
                        block_left in (1, 2),
                        block_right in (1, 2),
                    )
                    texture = texture_map[poly]

                self.__parsed_island[row][column] = texture

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:  # noqa: ARG002
        world_position = pv.global_vars.get_world_position()
        resolution = pv.global_vars.resolution_screen
        start_pos = self.world_position

        world_end = world_position + resolution

        # check if island is on screen
        # if (
        #     self.pos.x + self.size.x < world_position.x
        #     or self.pos.x > world_position.x + resolution.x
        #     or self.pos.y + self.size.y < world_position.y
        #     or self.pos.y > world_position.y + resolution.y
        # ):
        #     return

        if self._highlight:
            renderer.start_stencil(True)  # noqa: FBT003

        # for texture_id, (column_offset, row_offset) in self.__parsed_island:
        n_rows = len(self.__parsed_island)
        n_cols = len(self.__parsed_island[0])

        vis_row_start = int(
            clamp((world_position.y - self.pos.y) // self._image_size[1], 0, n_rows)
        )
        vis_row_end = int(
            clamp((world_end.y - self.pos.y) // self._image_size[1] + 1, 0, n_rows)
        )

        vis_col_start = int(
            clamp((world_position.x - self.pos.x) // self._image_size[0], 0, n_cols)
        )
        vis_col_end = int(
            clamp((world_end.x - self.pos.x) // self._image_size[1] + 1, 0, n_cols)
        )

        # only iterate columns and rows that are on screen
        for row in range(max(vis_row_start, 0), min(vis_row_end, n_rows)):
            for col in range(max(vis_col_start, 0), min(vis_col_end, n_cols)):
                # check if air
                if (texture_id := self.__parsed_island[row][col]) > 0:
                    pos = (
                        start_pos.x + col * self._image_size[0],
                        start_pos.y + row * self._image_size[1],
                    )
                    size = self._image_size

                    renderer.draw_textured_quad(
                        texture_id,
                        pos,
                        size,
                        layer=layer,
                        offscreen_check=False,
                    )

        if self._highlight:
            renderer.enable_stencil(True)  # noqa: FBT003

            renderer.draw_rect(
                self.world_position - self.size / 2,
                self.size * 2,
                (1, 1, 1, 0.5),
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
