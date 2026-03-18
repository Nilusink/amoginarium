"""
amoginarium/ui/_base/_ui_element.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

# noinspection PyPackageRequirements
import pygame as pg
import typing as tp

from amoginarium.logic import Vec2, coord_t, convert_coord
from amoginarium.shared import global_vars
from amoginarium.entities import Cursor, UIEntities

from ._ui_entity import UIEntity

if tp.TYPE_CHECKING:
    from .._widgets import UICursor
from .._types import Anchor


class UIElement(UIEntity):
    """Basic UI component with position, size, and hovering"""

    # region Attributes: position and size
    __placement_anchor: Anchor

    __relative_position: Vec2
    __last_relative_position: Vec2
    __absolute_position: Vec2
    __last_absolute_position: Vec2

    __relative_size: Vec2
    __last_relative_size: Vec2
    __absolute_size: Vec2
    __last_absolute_size: Vec2

    # Purely calculated values, therefore, these can't be set externally
    __width: float
    __height: float
    __center: Vec2
    __top_left: Vec2
    __top_right: Vec2
    __bottom_left: Vec2
    __bottom_right: Vec2
    # endregion

    # region Attributes: hovering
    __collision_surface: pg.Surface | None = None
    __collision_mask: pg.Mask | None
    __collision_buffer: int  # Note: Buffer can't be set after creation. Until needed it's better this way
    __use_collision_mask: bool

    __collision_recreation: bool  # Internal variable indicating the collision surface/mask needs to be recreated
    __ui_changed: bool  # Variable indicating if the UI has changed since the last draw. Can be set by outer layers

    __is_hovered: bool
    __is_hovered_inner: bool | None
    __is_hovered_inner_last: bool | None
    __is_hovered_outer: bool | None
    __is_hovered_outer_last: bool | None

    __on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None
    __on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None
    __on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None

    __on_click_callbacks: list[tp.Callable[[], tp.Any]]

    # endregion

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            *_args: tp.Any,
            parent: UIEntity | None = None,
            placement_anchor: Anchor = Anchor.CENTER,
            collision_buffer: int = 1,
            on_enter_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_leave_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            on_buffer_callbacks: list[tp.Callable[[], tp.Any]] | None = None,
            absolute_values: bool = False,
            _positon_relative_to_parent: bool = True,
            _size_relative_to_parent: bool = True,
            _scaling: bool = True,
            _use_collision_mask: bool = True,
    ) -> None:
        """
        Create a new UI component
        :param position: Relative position of the component (absolute if absolute_values is set to True)
        :param size: Relative size of the component (absolute if absolute_values is set to True)
        :param _args: Not used
        :param parent: Optional parent UI-Entity
        :param placement_anchor: Placement anchor of the component
        :param collision_buffer: Mouse hovering buffer for edge cases
        :param on_enter_callbacks: Callbacks to be called when a cursor enters the component
        :param on_leave_callbacks: Callbacks to be called when a cursor leaves the component
        :param on_buffer_callbacks: Callbacks to be called when a cursor is right on the edge of the component,
        :param absolute_values: Whether the position and size are absolute or relative
        :param _positon_relative_to_parent: Whether the position is relative to the parent or the screen
        :param _size_relative_to_parent: Whether the size is relative to the parent or the screen
        :param _scaling: Whether the position and size should be scaled if the resolution is changed
        :param _use_collision_mask: Whether a collision mask should be used or just a collision box
        """
        super().__init__(parent=parent)

        if absolute_values:
            self.__absolute_position = convert_coord(position, Vec2)
            self.__absolute_size = convert_coord(size, Vec2)
            self.__relative_position = convert_coord(self.__absolute_to_relative(self.__absolute_position), Vec2)
            self.__relative_size = convert_coord(self.__absolute_to_relative(self.__absolute_size), Vec2)
        else:
            self.__relative_position = convert_coord(position, Vec2)
            self.__relative_size = convert_coord(size, Vec2)
            self.__absolute_position = convert_coord(self.__relative_to_absolute(self.__relative_position), Vec2)
            self.__absolute_size = convert_coord(self.__relative_to_absolute(self.__relative_size), Vec2)

        self.__placement_anchor = placement_anchor
        self.__collision_buffer = collision_buffer
        self.__use_collision_mask = _use_collision_mask
        self.__on_enter_callbacks = on_enter_callbacks
        self.__on_leave_callbacks = on_leave_callbacks
        self.__on_buffer_callbacks = on_buffer_callbacks
        self.__on_click_callbacks = []

        self.__is_hovered = False
        self.__is_hovered_inner = None
        self.__is_hovered_inner_last = None
        self.__is_hovered_outer = None
        self.__is_hovered_outer_last = None
        self.__ui_changed = True
        self.__last_absolute_size = Vec2()
        self.__last_relative_size = Vec2()
        self.__last_absolute_position = Vec2()
        self.__last_relative_position = Vec2()
        self.__collision_recreation = True
        self.__collision_mask = None
        self.__collision_surface = None

        self.add(UIEntities)

    # region temp - will be fixed with controller rework
    def check_click(self):
        """TEMP: check if clicked"""
        if self.is_hovered and self.visible:
            for cb in self.__on_click_callbacks:
                cb()

    def add_click_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor enters the component"""
        self.__on_click_callbacks.append(callback)

    # endregion

    # region Methods: static absolute/relative convert
    @staticmethod
    def __relative_to_absolute(relative_value: coord_t) -> tuple[float, float]:
        """
        Converts relative coords to absolute coords according to the current resolution
        :param relative_value: Relative value to convert
        :return: Absolute value
        """
        abs_x, abs_y = convert_coord(relative_value)
        return abs_x * global_vars.resolution.x, abs_y * global_vars.resolution.y

    @staticmethod
    def __absolute_to_relative(absolute_value: coord_t) -> tuple[float, float]:
        """
        Converts relative coords to absolute coords according to the current resolution
        :param absolute_value: Absolute value to convert
        :return: Relative value
        """
        rel_x, rel_y = convert_coord(absolute_value)
        return rel_x / global_vars.resolution.x, rel_y / global_vars.resolution.y

    # endregion

    # region Methods: hovering (including related properties)
    def add_enter_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor enters the component"""
        if self.__on_enter_callbacks is None:
            self.__on_enter_callbacks = []
        self.__on_enter_callbacks.append(callback)

    def add_buffer_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor is right on the edge of the component"""
        if self.__on_buffer_callbacks is None:
            self.__on_buffer_callbacks = []
        self.__on_buffer_callbacks.append(callback)

    def add_leave_callback(self, callback: tp.Callable[[], None]) -> None:
        """:param callback: Callback to be called when a cursor leaves the component"""
        if self.__on_leave_callbacks is None:
            self.__on_leave_callbacks = []
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
            self.__ui_changed = True

    @property
    def _collision_surface(self) -> pg.Surface:
        """
        :return: Collision surface
        :raises ValueError: If use_collision_mask is set to false
        """
        if not self.__use_collision_mask:
            raise ValueError("use_collision_mask is set to false")

        if self.__collision_recreation or self.__collision_surface is None:
            self.__collision_recreation = False  #
            self.__collision_mask = None
            self.__collision_surface = pg.Surface(self.absolute_size.xy, pg.SRCALPHA, 32)
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
            for cursor in Cursor.sprites():
                if self.__is_hovered_by(cursor.absolute_position, buffer=self.__collision_buffer):
                    self.__is_hovered_inner = True

        return self.__is_hovered_inner

    def __hovered_outer(self) -> bool:
        """:return: Whether a cursor is hovering over the outer buffer of the component"""
        if self.__is_hovered_outer is None:
            self.__is_hovered_outer = False
            cursor: UICursor
            for cursor in Cursor.sprites():
                if self.__is_hovered_by(cursor.absolute_position, buffer=-self.__collision_buffer):
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
            (self.__top_left.x + buffer) <= coords.x <= (self.__bottom_right.x - buffer),
            (self.__top_left.y + buffer) <= coords.y <= (self.__bottom_right.y - buffer)
        ]):
            if not self.__use_collision_mask:
                return True

            rel_coords = (coords - self.__top_left)

            rel_coords.x += -buffer if coords.x < self.__center.x else buffer
            rel_coords.y += -buffer if coords.y < self.__center.y else buffer

            coords_new = convert_coord(rel_coords.xy, Vec2)

            try:
                if self._collision_mask.get_at(coords_new.xy):
                    return True
            except IndexError:
                pass

        return False

    # endregion

    # region Methods: drawing
    def _after_draw_update(self) -> None:
        if self.__on_enter_callbacks or self.__on_leave_callbacks or self.__on_buffer_callbacks:
            # Don't change directly into an if. This way the hovered_inner/outer variables are always both updated
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

    def _gl_draw(self) -> None:
        """
        The draw function called in loop

        It should always follow this structure:
        - Compare if anything changed, requiring redrawing of the collision surface/mask
        - Call super()._gl_draw()
        - Draw the UI and collision surface
        """
        super()._gl_draw()

        self.__is_hovered_inner_last = self.__is_hovered_inner
        self.__is_hovered_outer_last = self.__is_hovered_outer
        self.__is_hovered_inner = None
        self.__is_hovered_outer = None

        # Dont change this. This way it checks if the values have been changed externally
        new_abs_pos = self.__relative_to_absolute(self.relative_position)
        new_abs_size = self.__relative_to_absolute(self.relative_size)

        self.__last_relative_position.xy = self.relative_position.xy
        self.__last_relative_size.xy = self.relative_size.xy
        self.__last_absolute_position.xy = self.absolute_position.xy
        self.__last_absolute_size.xy = self.absolute_size.xy

        self.absolute_position.xy = new_abs_pos
        self.absolute_size.xy = new_abs_size

        # Check if values changed
        if self.__use_collision_mask:
            if not self._ui_changed:
                if (self.absolute_position.xy != self.__last_absolute_position.xy
                        or self.absolute_size.xy != self.__last_absolute_size.xy):
                    self._ui_changed = True

        self.__width = self.absolute_size.x
        self.__height = self.absolute_size.y

        if self.__placement_anchor == "nw":
            self.__top_left = self.absolute_position
            self.__top_right = self.absolute_position + convert_coord((self.absolute_size.x, 0), Vec2)
            self.__bottom_left = self.absolute_position + convert_coord((0, self.absolute_size.y), Vec2)
            self.__bottom_right = self.absolute_position + self.absolute_size.y

            self.__center = self.absolute_position + self.absolute_size / 2

        elif self.__placement_anchor == "center":
            self.__top_left = self.absolute_position - self.absolute_size / 2
            self.__top_right = self.absolute_position + convert_coord(
                (self.absolute_size.x / 2, -self.absolute_size.y / 2),
                Vec2)
            self.__bottom_left = self.absolute_position + convert_coord(
                (-self.absolute_size.x / 2, self.absolute_size.y / 2),
                Vec2)
            self.__bottom_right = self.absolute_position + self.absolute_size / 2

            self.__center = self.absolute_position

    def gl_draw(self, recursive: bool = True, force_draw: bool = False) -> None:
        super().gl_draw(recursive=recursive, force_draw=force_draw)
        if force_draw or self.visible:
            self._after_draw_update()
        self._ui_changed = False

    def reset(self) -> None:
        super().reset()
        self.__is_hovered = False
        self.__is_hovered_inner = None
        self.__is_hovered_inner_last = None
        self.__is_hovered_outer = None
        self.__is_hovered_outer_last = None
        self.__ui_changed = True
        self.__collision_recreation = True
        self.__collision_mask = None
        self.__collision_surface = None

    # endregion

    # region Methods: properties
    @property
    def _ui_changed(self) -> bool:
        """:return: Whether the UI has changed since the last draw"""
        return self.__ui_changed

    @_ui_changed.setter
    def _ui_changed(self, value: bool) -> None:
        """:param value: Set whether the UI has changed since the last draw"""
        self.__ui_changed = value
        self.__collision_recreation = value

    @property
    def absolute_position(self) -> Vec2:
        """:return: Absolute position - anchor not factored in"""
        if self.__last_relative_position.xy != self.__relative_position.xy:
            self.__absolute_position.xy = self.__relative_to_absolute(self.__relative_position)
            self.__last_relative_position.xy = self.__relative_position.xy
        return self.__absolute_position

    @absolute_position.setter
    def absolute_position(self, value: coord_t) -> None:
        """:param value: Absolute position"""
        self.__absolute_position.xy = convert_coord(value)
        self.__relative_position.xy = self.__absolute_to_relative(self.__absolute_position)

    @property
    def absolute_size(self) -> Vec2:
        """:return: Absolute size"""
        if self.__last_relative_size.xy != self.__relative_size.xy:
            self.__absolute_size.xy = self.__relative_to_absolute(self.__relative_size)
            self.__last_relative_size.xy = self.__relative_size.xy
        return self.__absolute_size

    @absolute_size.setter
    def absolute_size(self, value: coord_t) -> None:
        """:param value: Absolute size"""
        self.__absolute_size.xy = convert_coord(value)
        self.__relative_size.xy = self.__absolute_to_relative(self.__absolute_size)

    @property
    def relative_position(self) -> Vec2:
        """:return: Relative position - anchor not factored in"""
        if self.__absolute_position.xy != self.__last_absolute_position.xy:
            self.__relative_position.xy = self.__absolute_to_relative(self.__absolute_position)
            self.__last_absolute_position.xy = self.__absolute_position.xy
        return self.__relative_position

    @relative_position.setter
    def relative_position(self, value: coord_t) -> None:
        """:param value: Relative position"""
        self.__relative_position.xy = convert_coord(value)
        self.__absolute_position.xy = self.__relative_to_absolute(self.__relative_position)

    @property
    def relative_size(self) -> Vec2:
        """:return: Relative size"""
        if self.__absolute_size.xy != self.__last_absolute_size.xy:
            self.__relative_size.xy = self.__absolute_to_relative(self.__absolute_size)
            self.__last_absolute_size.xy = self.__absolute_size.xy
        return self.__relative_size

    @relative_size.setter
    def relative_size(self, value: coord_t) -> None:
        """:param value: Relative size"""
        self.__relative_size.xy = convert_coord(value)
        self.__absolute_size.xy = self.__relative_to_absolute(self.__relative_size)

    @property
    def width(self) -> float:
        """:return: Absolute width"""
        return self.__width

    @property
    def height(self) -> float:
        """:return: Absolute height"""
        return self.__width

    @property
    def placement_anchor(self) -> Anchor:
        """:return: Placement anchor"""
        return self.__placement_anchor

    @placement_anchor.setter
    def placement_anchor(self, value: Anchor) -> None:
        """:param value: Placement anchor, values recalculated next frame"""
        self.__placement_anchor = value

    @property
    def top_left(self) -> Vec2:
        """:return: Absolute top left"""
        return self.__top_left

    @property
    def top_right(self) -> Vec2:
        """:return: Absolute top right"""
        return self.__top_right

    @property
    def bottom_left(self) -> Vec2:
        """:return: Absolute bottom left"""
        return self.__bottom_left

    @property
    def bottom_right(self) -> Vec2:
        """:return: Absolute bottom right"""
        return self.__bottom_right

    @property
    def center(self) -> Vec2:
        """:return: Absolute center"""
        return self.__center

    # endregion
