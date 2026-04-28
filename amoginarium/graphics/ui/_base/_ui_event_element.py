"""
amoginarium/graphics/ui/_base/_ui_event_element.py

Project: amoginarium
Created: 18.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

# noinspection PyPackageRequirements
import pygame as pg
import typing as tp

from amoginarium.shared.utility import Vec2, coord_t, convert_coord

from ...entities import UIEntities, Cursor
from .._types import Anchor, Positions
from ._ui_element import UIElement

if tp.TYPE_CHECKING:
    from ._ui_entity import UIEntity
    from .._widgets import UICursor


class UIEventElement(UIElement):
    """UI component that handles mouse events, hovering, and collision masks."""
    __collision_surface: pg.Surface | None = None
    __collision_mask: pg.Mask | None
    __collision_buffer: int
    __use_collision_mask: bool

    __collision_recreation: bool

    __is_hovered: bool
    __is_hovered_inner: bool | None
    __is_hovered_inner_last: bool | None
    __is_hovered_outer: bool | None
    __is_hovered_outer_last: bool | None

    __on_enter_callbacks: list[tp.Callable[[], tp.Any]]
    __on_leave_callbacks: list[tp.Callable[[], tp.Any]]
    __on_buffer_callbacks: list[tp.Callable[[], tp.Any]]
    __on_click_callbacks: list[tp.Callable[[], tp.Any]]

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            *,
            parent: UIEntity | None = None,
            placement_anchor: Anchor = Anchor.CENTER,
            absolute_values: bool = False,
            positon_is_relative_to_parent: bool = True,
            size_is_relative_to_parent: bool = True,
            parent_reference_position: Positions = Positions.TOP_LEFT,

            collision_buffer: int = 1,
            use_collision_mask: bool = True,
            on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
    ) -> None:
        """
        Create a new UI component
        :param position: Relative position of the component (absolute if absolute_values is set to True)
        :param size: Relative size of the component (absolute if absolute_values is set to True)
        :param parent: Optional parent UI-Entity
        :param placement_anchor: Placement anchor of the component
        :param absolute_values: Whether the position and size are absolute or relative
        :param positon_is_relative_to_parent: Whether the position is relative to the parent or the screen
        :param size_is_relative_to_parent: Whether the size is relative to the parent or the screen
        :param parent_reference_position: What reference position of the parent component to use
        :param collision_buffer: Buffer for mouse hover in pixels
        :param use_collision_mask: Whether to use a collision mask or just a collision box
        :param on_enter_callbacks: List of callbacks to be called when a cursor enters the component
        :param on_leave_callbacks: List of callbacks to be called when a cursor leaves the component
        :param on_buffer_callbacks: List of callbacks to be called when a cursor buffers the component
        """
        super().__init__(
            position=position,
            size=size,
            parent=parent,
            placement_anchor=placement_anchor,
            absolute_values=absolute_values,
            positon_is_relative_to_parent=positon_is_relative_to_parent,
            size_is_relative_to_parent=size_is_relative_to_parent,
            parent_reference_position=parent_reference_position
        )

        self.__collision_buffer = collision_buffer
        self.__use_collision_mask = use_collision_mask
        self.__on_enter_callbacks = on_enter_callbacks or []
        self.__on_leave_callbacks = on_leave_callbacks or []
        self.__on_buffer_callbacks = on_buffer_callbacks or []
        self.__on_click_callbacks = []

        self.__is_hovered = False
        self.__is_hovered_inner = None
        self.__is_hovered_inner_last = None
        self.__is_hovered_outer = None
        self.__is_hovered_outer_last = None

        self.__collision_recreation = True
        self.__collision_mask = None
        self.__collision_surface = None

        self.add(UIEntities)

    # region TEMP: Click Callbacks
    def check_click(self) -> None:
        """TEMP: check if clicked"""
        if self.is_hovered and self.visible:
            for cb in self.__on_click_callbacks:
                cb()

    def add_click_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor enters the component"""
        self.__on_click_callbacks.append(callback)

    # endregion

    # region Methods: Hovering & Collision
    def add_enter_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor enters the component"""
        self.__on_enter_callbacks.append(callback)

    def add_buffer_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor is right on the edge of the component"""
        self.__on_buffer_callbacks.append(callback)

    def add_leave_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor leaves the component"""
        self.__on_leave_callbacks.append(callback)

    @property
    def use_collision_mask(self) -> bool:
        """:return: Whether a collision mask is used or just a collision box"""
        return self.__use_collision_mask

    @use_collision_mask.setter
    def use_collision_mask(self, value: bool) -> None:
        """:param value: Whether a collision mask is used or just a collision box"""
        if value == self.__use_collision_mask:
            return
        self.__use_collision_mask = value

        self.__collision_mask = None
        self.__collision_surface = None

        if self.__use_collision_mask:
            self.__collision_recreation = True
            self._ui_changed = True

    @property
    def _collision_surface(self) -> pg.Surface:
        """
        :return: Collision surface
        :raises ValueError: If use_collision_mask is set to false
        """
        if not self.__use_collision_mask:
            raise ValueError("use_collision_mask is set to false")

        if self.__collision_recreation or self.__collision_surface is None:
            self.__collision_recreation = False
            self.__collision_mask = None
            self.__collision_surface = pg.Surface(self.size.absolute.xy, pg.SRCALPHA, 32)
        return self.__collision_surface

    @property
    def _collision_mask(self) -> pg.Mask:
        """
        :return: Collision mask
        :raises ValueError: If use_collision_mask is set to false
        """
        if not self.__use_collision_mask:
            raise ValueError("use_collision_mask is set to false")

        if self.__collision_mask is None:
            self.__collision_mask = pg.mask.from_surface(self._collision_surface)
        return self.__collision_mask

    @property
    def is_hovered(self) -> bool:
        """:return: Whether a cursor is hovering over the component"""
        return self.__is_hovered

    def __hovered_inner(self) -> bool:
        """:return: Whether a cursor is hovering over the component"""
        if self.__is_hovered_inner is None:
            self.__is_hovered_inner = False
            cursor: UICursor
            for cursor in Cursor.entities():
                if self.__is_hovered_by(cursor.position.absolute_global, buffer=self.__collision_buffer):
                    self.__is_hovered_inner = True

        return self.__is_hovered_inner

    def __hovered_outer(self) -> bool:
        """:return: Whether a cursor is hovering over the outer buffer of the component"""
        if self.__is_hovered_outer is None:
            self.__is_hovered_outer = False
            cursor: UICursor
            for cursor in Cursor.entities():
                if self.__is_hovered_by(cursor.position.absolute_global, buffer=-self.__collision_buffer):
                    self.__is_hovered_outer = True
                    break

        return self.__is_hovered_outer

    def __is_hovered_by(self, coords: Vec2, buffer: int = 0) -> bool:
        """
        Check if coords are over the component with a buffer
        :param coords: Coordinates to check
        :param buffer: Buffer around the coordinates
        :return: Whether coords are over the component
        """
        if all([
            (self.top_left.absolute_global.x + buffer) <= coords.x <= (self.bottom_right.absolute_global.x - buffer),
            (self.top_left.absolute_global.y + buffer) <= coords.y <= (self.bottom_right.absolute_global.y - buffer)
        ]):
            if not self.__use_collision_mask:
                return True

            rel_coords = (coords - self.top_left.absolute_global)

            rel_coords.x += -buffer if coords.x < self.center.absolute_global.x else buffer
            rel_coords.y += -buffer if coords.y < self.center.absolute_global.y else buffer

            coords_new = convert_coord(rel_coords.xy, Vec2)

            try:
                if self._collision_mask.get_at(coords_new.xy):
                    return True
            except IndexError:
                pass

        return False

    # endregion

    # region Methods: Drawing & Updates
    def _gl_draw(self, delta_cal: float, layer: int = 0):
        """
        The draw function called in loop. Updates hover state trackers and handles
        collision surface recreation flags before calling the parent UIElement draw.
        """
        self.__is_hovered_inner_last = self.__is_hovered_inner
        self.__is_hovered_outer_last = self.__is_hovered_outer
        self.__is_hovered_inner = None
        self.__is_hovered_outer = None

        super()._gl_draw(delta_cal, layer)

        if self.__use_collision_mask and self._ui_changed:
            self.__collision_recreation = True

    def _after_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        super()._after_gl_draw(drawn, layer)
        if drawn:
            if self.__on_enter_callbacks or self.__on_leave_callbacks or self.__on_buffer_callbacks:
                hovered_inner = self.__hovered_inner()
                hovered_outer = self.__hovered_outer()

                if hovered_inner is None or hovered_outer is None:
                    return

                if hovered_inner and not self.__is_hovered_inner_last:
                    self.__is_hovered = True
                    for callback in self.__on_enter_callbacks:
                        callback()
                elif self.__is_hovered_outer_last and not hovered_outer:
                    self.__is_hovered = False
                    for callback in self.__on_leave_callbacks:
                        callback()
                elif (self.__is_hovered_inner_last and not hovered_inner
                      and hovered_outer and self.__is_hovered_outer_last):
                    for callback in self.__on_buffer_callbacks:
                        callback()

    def _reset(self) -> None:
        super()._reset()
        self.__is_hovered = False
        self.__is_hovered_inner = None
        self.__is_hovered_inner_last = None
        self.__is_hovered_outer = None
        self.__is_hovered_outer_last = None
        self.__collision_recreation = True
        self.__collision_mask = None
        self.__collision_surface = None

    # endregion
