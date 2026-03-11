"""
amoginarium/entities/_ui/_ui_component.py

Project: amoginarium
"""

from __future__ import annotations

import typing as tp

from ._entity import UIEntity
from ._types import anchor_t
from ..entities import Cursor

from ..logic import Vec2, coord_t, convert_coord
from ..shared import global_vars

import pygame as pg


##################################################
#                     Code                       #
##################################################

class UIComponent(UIEntity):
    __relative_position: Vec2
    __relative_size: Vec2
    __placement_anchor: anchor_t

    __absolute_position: Vec2
    __absolute_position_updated: bool
    __absolute_size: Vec2
    __absolute_size_updated: bool
    __width: float
    __height: float
    __center: Vec2
    __top_left: Vec2
    __top_right: Vec2
    __bottom_left: Vec2
    __bottom_right: Vec2
    # masks - zwei farben

    # mask get at local

    # hover grob?
    # mask check

    # wenn nix anders - gleiche maske - size/position animations gleich wie davor keine ausrechnen

    __collision_surface: pg.Surface | None = None
    __collision_mask: pg.Mask | None
    __work_with_collision_mask: bool

    __collision_recreation: bool
    __ui_changed: bool

    __last_absolute_position: Vec2 | None
    __last_absolute_size: Vec2 | None

    __last_hover: bool | None
    __is_hovered: bool | None

    __on_enter_callbacks: list[tp.Callable[[], None]] | None
    __on_leave_callbacks: list[tp.Callable[[], None]] | None

    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            *_args: tp.Any,
            parent: UIEntity | None = None,
            placement_anchor: anchor_t = "center",
            _work_with_collision_mask: bool = True
    ) -> None:
        super().__init__(parent=parent)

        self.__relative_position = convert_coord(relative_position, Vec2)
        self.__relative_size = convert_coord(relative_size, Vec2)
        self.__placement_anchor = placement_anchor
        self.__work_with_collision_mask = _work_with_collision_mask

        self.__absolute_size_updated = False
        self.__absolute_position_updated = False

        self.__on_enter_callbacks = None
        self.__on_leave_callbacks = None

        self.__absolute_position = Vec2()
        self.__absolute_size = Vec2()

        self.__is_hovered = None
        self.__ui_changed = True
        self.__collision_recreation = True
        self.__last_absolute_size = None
        self.__last_absolute_position = None
        self.__collision_mask = None

    @property
    def _ui_changed(self) -> bool:
        return self.__ui_changed

    @_ui_changed.setter
    def _ui_changed(self, value: bool) -> None:
        self.__ui_changed = value
        self.__collision_recreation = value

    @staticmethod
    def __relative_to_absolute(
            absolute_value: coord_t
    ) -> Vec2:
        return convert_coord(
            (
                int(absolute_value.x * global_vars.resolution.x),
                int(absolute_value.y * global_vars.resolution.y)
            ),
            Vec2
        )

    @property
    def _work_with_collision_mask(self) -> bool:
        return self.__work_with_collision_mask

    @property
    def _collision_surface(self) -> pg.Surface:
        if not self.__work_with_collision_mask:
            raise NotImplementedError("Collision surface isn't supported")

        # whenever something changed compared to last time - how do i know?
        if self.__collision_recreation:
            self.__collision_recreation = False  #
            self.__collision_mask = None
            self.__collision_surface = pg.Surface(self.__absolute_size.xy, pg.SRCALPHA, 32)
        return self.__collision_surface

    @property
    def _collision_mask(self) -> pg.Mask:
        if not self.__work_with_collision_mask:
            raise NotImplementedError("Collision mask isn't supported")

        if self.__collision_mask is None:
            self.__collision_mask = pg.mask.from_surface(self._collision_surface)
        return self.__collision_mask

    def add_enter_callback(self, callback: tp.Callable[[], None]) -> None:
        if self.__on_enter_callbacks is None:
            self.__on_enter_callbacks = []
        self.__on_enter_callbacks.append(callback)

    def add_leave_callback(self, callback: tp.Callable[[], None]) -> None:
        if self.__on_leave_callbacks is None:
            self.__on_leave_callbacks = []
        self.__on_leave_callbacks.append(callback)

    @property
    def is_hovered(self) -> bool:
        if self.__is_hovered is None:
            self.__is_hovered = False
            cursor: UIComponent
            for cursor in Cursor.sprites():
                if self.__is_hovered_by(cursor._abs_position):
                    self.__is_hovered = True
                    break

        return self.__is_hovered

    def __is_hovered_by(self, coords: Vec2) -> bool:
        if all([
            self.__top_left.x <= coords.x <= self.__bottom_right.x,
            self.__top_left.y <= coords.y <= self.__bottom_right.y
        ]):
            if not self.__work_with_collision_mask:
                return True
            try:
                if self._collision_mask.get_at((coords - self.__top_left).xy):
                    return True
            except IndexError:
                ...
            print("IN BOUNDS, BUT NOT IN MASK GRRRRRR")

        return False

    def _after_draw_update(self) -> None:
        if self.__on_enter_callbacks or self.__on_leave_callbacks:
            # print(self.is_hovered, self.__last_hover)
            if self.is_hovered is None:  # DO NOT CHANGE - this triggers an update
                return

            if self.__last_hover is None:
                return

            if self.__last_hover != self.is_hovered:
                if self.is_hovered:
                    for callback in self.__on_enter_callbacks:
                        callback()
                else:
                    for callback in self.__on_leave_callbacks:
                        callback()

    def _gl_draw(self) -> None:
        """
        Draw function called in loop

        It should always follow this structure in UI:
        - Compare if anything changed, requiring redrawing of the collision surface/mask
        - Call super()._gl_draw()
        - Draw the UI and collision surface
        """
        self.__last_hover = self.__is_hovered
        self.__is_hovered = None

        # Save old values
        if self.__work_with_collision_mask:
            self.__last_absolute_position = self.__absolute_position
            self.__last_absolute_size = self.__absolute_size

        # Calculate new values
        if self.__absolute_position_updated:
            self.__absolute_position_updated = False
        else:
            self.__absolute_position = self.__relative_to_absolute(self.__relative_position)

        if self.__absolute_size_updated:
            self.__absolute_size_updated = False
        else:
            self.__absolute_size = self.__relative_to_absolute(self.__relative_size)

        # Check if values changed
        if self.__work_with_collision_mask and not self._ui_changed:
            if (self.__absolute_position.xy != self.__last_absolute_position.xy
                    or self.__absolute_size.xy != self.__last_absolute_size.xy):
                self._ui_changed = True

        self.__width = self.__absolute_size.x
        self.__height = self.__absolute_size.y

        if self.__placement_anchor == "nw":
            self.__top_left = self.__absolute_position
            self.__top_right = self.__absolute_position + convert_coord((self.__absolute_size.x, 0), Vec2)
            self.__bottom_left = self.__absolute_position + convert_coord((0, self.__absolute_size.y), Vec2)
            self.__bottom_right = self.__absolute_position + self.__absolute_size.y

            self.__center = self.__absolute_position + self.__absolute_size / 2

        elif self.__placement_anchor == "center":
            self.__top_left = self.__absolute_position - self.__absolute_size / 2
            self.__top_right = self.__absolute_position + convert_coord(
                (self.__absolute_size.x / 2, -self.__absolute_size.y / 2),
                Vec2)
            self.__bottom_left = self.__absolute_position + convert_coord(
                (-self.__absolute_size.x / 2, self.__absolute_size.y / 2),
                Vec2)
            self.__bottom_right = self.__absolute_position + self.__absolute_size / 2

            self.__center = self.__absolute_position

    def gl_draw(self) -> None:
        self._ui_changed = False
        self._gl_draw()
        self._after_draw_update()

    @property
    def _abs_position(self) -> Vec2:
        """:return: Absolute position - anchor not factored in"""
        return self.__absolute_position

    @_abs_position.setter
    def _abs_position(self, value: Vec2) -> None:
        """:return: Absolute position - anchor not factored in"""
        self.__absolute_position = value
        self.__absolute_position_updated = True

    @property
    def _abs_size(self) -> Vec2:
        """:return: Absolute size"""
        return self.__absolute_size

    @_abs_size.setter
    def _abs_size(self, value: Vec2) -> None:
        self.__absolute_size = value
        self.__absolute_size_updated = True

    @property
    def _rel_position(self) -> Vec2:
        """:return: Relative position - anchor not factored in"""
        return self.__relative_position

    @property
    def _rel_size(self) -> Vec2:
        """:return: Relative size"""
        return self.__relative_size

    @property
    def _width(self) -> float:
        """:return: Absolute width"""
        return self.__width

    @property
    def _height(self) -> float:
        """:return: Absolute height"""
        return self.__width

    @property
    def _placement_anchor(self) -> anchor_t:
        """:return: Placement anchor"""
        return self.__placement_anchor

    @property
    def _top_left(self) -> Vec2:
        """:return: Absolute top left"""
        return self.__top_left

    @property
    def _top_right(self) -> Vec2:
        """:return: Absolute top right"""
        return self.__top_right

    @property
    def _bottom_left(self) -> Vec2:
        """:return: Absolute bottom left"""
        return self.__bottom_left

    @property
    def _bottom_right(self) -> Vec2:
        """:return: Absolute bottom right"""
        return self.__bottom_right

    @property
    def center(self) -> Vec2:
        """:return: Absolute center"""
        return self.__center
