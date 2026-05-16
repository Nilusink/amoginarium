"""
amoginarium/logic/entities/_world/_base_island.py

Project: amoginarium
Created: 26.01.2024
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import random
import typing as tp

from amoginarium import pv
from amoginarium.shared import BaseCommandType, CIDType, ProcessCommand
from amoginarium.shared.debugging import CC, print_ic_style
from amoginarium.shared.utility import (
    Vec2,
    convert_coord,
    find_minimum_rectangles_dirty,
)

from .._base import (
    CollisionType,
    DebugRectangleEntity,
    GameCollisions,
    LogicGameEntity,
    Walls,
)

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.utility import coord_t


class Island(LogicGameEntity):
    """
    Base class for island entities in the game world.
    Handles collision generation from bitmaps and logic-to-graphics synchronization.
    """

    __slots__ = ("_size", "_form", "_damage", "_bounce")
    # region ClassVars
    _block_size: tp.ClassVar[tuple[int, int]] = (64, 64)
    _DEFAULT_COLLISION_GROUP: tp.ClassVar[CollisionType.GroupID] = (
        GameCollisions.collision_group_islands
    )
    __DEBUG_DRAW_HITBOXES: tp.ClassVar[bool] = False

    ISLANDS: tp.ClassVar[dict[CIDType, type[Island]]] = {}
    ISLANDS_REVERSE: tp.ClassVar[dict[type[Island], CIDType]] = {}

    # endregion
    # region InstanceVars
    _size: EllipsisType | Vec2
    _form: EllipsisType | list[list[int]]
    _damage: float
    _bounce: float  # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        pos: coord_t,
        size: coord_t | EllipsisType = ...,
        form: list[list[int]] | EllipsisType = ...,
        damage: float | EllipsisType = ...,
        bounce: float | EllipsisType = ...,
    ) -> None:
        """
        Initialize an Island entity.
        :param runtime_buffer: The C-level memory buffer for entity data.
        :param pos: Initial position of the island.
        :param size: Dimensions of the island (used if form is not provided).
        :param form: 2D integer array representing the island's layout.
        :param damage: Damage multiplier for contact.
        :param bounce: Bounciness factor for collisions.
        """
        if size is ... and form is ...:
            raise ValueError("either size or form have to be given!")

        start = convert_coord(pos, Vec2)
        self._size = ... if size is ... else convert_coord(size, Vec2)
        self._form = form
        self._damage = damage
        self._bounce = bounce

        if form is not ...:
            self._size = Vec2().from_cartesian(
                self.__class__._block_size[0] * max(len(r) for r in form),
                self.__class__._block_size[1] * len(form),
            )

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=self._size,
            position=start,
        )

        self.add(Walls)

        self._create_collision_entites()

        # spawn graphics entity
        kwargs: dict[str, tp.Any] = {
            "id": self.id,
            "cid": self.cid(),
        }

        if form is not ...:
            kwargs["form"] = form
        else:
            kwargs["size"] = self._size.xy

        pv.COQ.put(ProcessCommand(type=BaseCommandType.spawn_island, kwargs=kwargs))

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
        y_size_end: int,
    ) -> tp.Self:
        """
        Create an island with randomized position and size.
        :param runtime_buffer: The C-level memory buffer for entity data.
        :param x_start: Minimum X coordinate.
        :param x_end: Maximum X coordinate.
        :param y_start: Minimum Y coordinate.
        :param y_end: Maximum Y coordinate.
        :param x_size_start: Minimum width.
        :param x_size_end: Maximum width.
        :param y_size_start: Minimum height.
        :param y_size_end: Maximum height.
        :return: A new instance of the Island.
        """
        x = random.randint(x_start, x_end)
        y = random.randint(y_start, y_end)

        x_size = random.randint(x_size_start, x_size_end)
        y_size = random.randint(y_size_start, y_size_end)

        start = Vec2().from_cartesian(x, y)
        size = Vec2().from_cartesian(x_size, y_size)

        return cls(runtime_buffer, start, size)

    @property
    def form(self) -> list[list[int]] | None:
        """
        Get a copy of the island's structural form.
        :return: 2D list of integers or None if no form is defined.
        """
        if self._form is ...:
            return None
        return self._form.copy()

    def _create_collision_entites(self) -> None:
        """
        Generates collision rectangles for the island.
        If a form is provided, it uses a greedy algorithm to find the minimum number of
        rectangles covering the solid blocks to optimize collision checks.
        """
        if self._form is ...:
            GameCollisions.collision_manager.register_entity(
                GameCollisions.collision_group_islands, self, self.position, self.size
            )
            if Island.__DEBUG_DRAW_HITBOXES:
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
            rect_x = self.position.x + c1 * self.__class__._block_size[0]
            rect_y = self.position.y + r1 * self.__class__._block_size[1]
            rect_w = width_cells * self.__class__._block_size[0]
            rect_h = height_cells * self.__class__._block_size[1]

            position = convert_coord((rect_x, rect_y), Vec2)
            size = convert_coord((rect_w, rect_h), Vec2)

            GameCollisions.collision_manager.register_entity(
                GameCollisions.collision_group_islands, self, position, size
            )
            if Island.__DEBUG_DRAW_HITBOXES:
                DebugRectangleEntity(self._runtime_buffer, position, size)

    def to_dict(self) -> tp.MutableMapping[str, tp.Any]:
        """
        Convert island state to a dictionary for serialization/saving.
        :return: A dictionary containing the island's configuration and type.
        """
        out: tp.MutableMapping[str, tp.Any] = {"args": {"pos": self.position}}
        if self.form:
            out["args"]["form"] = self.form

        else:
            out["args"]["size"] = self.size

        try:
            out["type"] = Island.ISLANDS_REVERSE[self.__class__]

        except KeyError:
            print_ic_style(
                f"{CC.fg.RED}invalid island type: {self.__class__}{CC.ctrl.ENDC}"
            )

        return out
