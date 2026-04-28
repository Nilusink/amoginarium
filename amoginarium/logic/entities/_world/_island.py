"""
_island.py
26. January 2024

an island in the sky

Author:
Nilusink
"""
from __future__ import annotations
from ctypes import Array
from icecream import ic
import pygame as pg
import typing as tp
import random

from amoginarium.shared.utility import Vec2, coord_t, convert_coord, find_minimum_rectangles_dirty
from amoginarium.shared.debugging import print_ic_style, CC, cum_timer
from amoginarium.shared import base_entity_t, IslandCIDs, ProcessCommand
from amoginarium.shared import BaseCommandType
from amoginarium import pv

from .._base_entities import LogicGameEntity
from .._groups import Walls, Updated
from .._collision import collision_manager
from .._collision.collision_groups import collision_group_islands
from .._debug import DebugRectangleEntity

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


class Island(LogicGameEntity):
    _block_size: tuple[int, int] = (64, 64)
    debug = False

    _DEFAULT_COLLISION_GROUP = collision_group_islands

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
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
                self._block_size[0] * max(len(r) for r in form),
                self._block_size[1] * len(form)
            )

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=self._size,
            position=start,
        )

        self.add(Walls)
        self.update_rect()

        self._generate_collision_mask()

        # for group in GridSystem.get_cells_by_pos(self.rect.topleft[0], self.rect.topright[0]):
        #     self.add(group.walls)

        # spawn graphics entity
        args: tp.MutableMapping[str, tp.Any] = {
            "id": self.id,
            "cid": self.cid(),
        }

        if form is not ...:
            args["form"] = form

        else:
            args["size"] = self._size.xy

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_island,
            kwargs=args
        ))

    @classmethod
    def random_between(
            cls,
            runtime_buffer: Array[base_entity_t],
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

        return cls(runtime_buffer, start, size)

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x,
            self.position.y,
            self.size.x,
            self.size.y
        )

    @classmethod
    def _get_block_mask(cls) -> pg.Mask | tuple[pg.Mask, pg.Mask]:
        return pg.Mask(cls._block_size, fill=True)

    @property
    def form(self) -> list[list[int]] | None:
        if self._form is ...:
            return None

        return self._form.copy()

    def _generate_collision_mask(self) -> None:
        """
        generate the mask used for collision
        """
        # start = time.perf_counter_ns()
        self.collision_rects: list[pg.Rect] = []

        if self._form is ...:
            self.collision_rects.append(
                pg.Rect(self.position.x, self.position.y, self.size.x, self.size.y)
            )
            collision_manager.register_entity(collision_group_islands, self,
                                              self.position, self.size)
            DebugRectangleEntity(self._runtime_buffer, self.position, self.size)
            return

        # Collision rects
        n_rows = len(self._form)
        n_columns = max(len(row) for row in self._form)

        bitmap = [[0] * n_columns for _ in range(n_rows)]
        for r in range(n_rows):
            for c in range(n_columns):
                try:
                    # island_type > 0 means it's a solid block
                    if self._form[r][c] > 0:
                        bitmap[r][c] = 1
                except IndexError:
                    # Jagged edge, leave as 0
                    pass

        raw_rects = find_minimum_rectangles_dirty(bitmap)

        for r1, c1, r2, c2 in raw_rects:
            # Calculate cell dimensions
            width_cells = c2 - c1 + 1
            height_cells = r2 - r1 + 1

            # Translate to Pygame world coordinates
            rect_x = self.position.x + c1 * self._block_size[0]
            rect_y = self.position.y + r1 * self._block_size[1]
            rect_w = width_cells * self._block_size[0]
            rect_h = height_cells * self._block_size[1]

            position = convert_coord((rect_x, rect_y), Vec2)
            size = convert_coord((rect_w, rect_h), Vec2)

            self.collision_rects.append(pg.Rect(rect_x, rect_y, rect_w, rect_h))
            collision_manager.register_entity(collision_group_islands, self,
                                              position, size)
            DebugRectangleEntity(self._runtime_buffer, position, size)
        # collide entity and rect
        entity_mask = pg.Mask(self.size.xy)
        block_mask = self._get_block_mask()
        special_mask = None

        if isinstance(block_mask, tuple):
            block_mask, special_mask = block_mask

        for row in range(n_rows):
            row_offset = self._block_size[1] * row

            for column in range(n_columns):
                column_offset = self._block_size[0] * column

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

    @cum_timer.time_this
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

    def to_dict(self) -> tp.MutableMapping[str, tp.Any]:
        """
        convert island to dict for saving
        """
        out: tp.MutableMapping[str, tp.Any] = {
            "args": {
                "pos": self.position
            }
        }
        if self.form:
            out["args"]["form"] = self.form

        else:
            out["args"]["size"] = self.size

        try:
            out["type"] = _islands_reverse[self.__class__]

        except KeyError:
            print_ic_style(
                f"{CC.fg.RED}invalid island type: "
                f"{self.__class__}{CC.ctrl.ENDC}"
            )

        return out

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
        check which sides of a entity collide with the wall
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


class GrassIsland(Island):
    _block_size = (64, 64)
    _CID = IslandCIDs.grass_island


class GrayBrickIsland(Island):
    _block_size = (24 * 3, 24 * 3)
    _CID = IslandCIDs.gray_brick_island


class GreenBrickIsland(Island):
    _block_size = (24 * 3, 24 * 3)
    _CID = IslandCIDs.green_brick_island


# class PillarIsland(Island):
#     _block_size = (64 * 3, 112 * 3)
#
#
# class PlatformIsland1(Island):
#     _block_size = (46 * 3, 13 * 3)
#
#
# class PlatformIsland2(Island):
#     _block_size = (44 * 3, 11 * 3)


__islands: tp.Iterable[tp.Type[Island]] = [
    GrassIsland,
    GrayBrickIsland,
    GreenBrickIsland
]

ISLANDS: tp.Mapping[str, tp.Type[Island]] = {
    c.cid(): c for c in __islands
}
_islands_reverse = {v: k for k, v in ISLANDS.items()}
