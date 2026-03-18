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
from dataclasses import dataclass

from amoginarium.logic import Vec2, coord_t, convert_coord
from amoginarium.shared import global_vars
from amoginarium.entities import Cursor, UIEntities

from ._ui_entity import UIEntity

if tp.TYPE_CHECKING:
    from .._widgets import UICursor
from .._types import Anchor

@dataclass
class UIElementData:
    """Position data for UIElement that can all influence each other"""
    placement_anchor: Anchor = Anchor.CENTER

    relative_position_global: Vec2 = Vec2()
    absolute_position_global: Vec2 = Vec2()
    relative_size_global: Vec2 = Vec2()
    absolute_size: Vec2 = Vec2()

    relative_position_to_parent: Vec2 = Vec2()
    absolute_position_to_parent: Vec2 = Vec2()
    relative_size_to_parent: Vec2 = Vec2()

    width: float = 0.0
    height: float = 0.0
    center: Vec2 = Vec2()
    top_left: Vec2 = Vec2()
    top_right: Vec2 = Vec2()
    bottom_left: Vec2 = Vec2()
    bottom_right: Vec2 = Vec2()

    position_is_relative_to_parent: bool = True
    size_is_relative_to_parent: bool = True

    reference_relative_global_size: Vec2 = Vec2()
    reference_absolute_size: Vec2 = Vec2()
    reference_absolute_global_position: Vec2 = Vec2()
    reference_relative_global_position: Vec2 = Vec2()

    def copy_from(self, other: UIElementData) -> None:
        """Updates this instance with values from another in-place."""
        self.placement_anchor = other.placement_anchor
        self.width = other.width
        self.height = other.height
        self.position_is_relative_to_parent = other.position_is_relative_to_parent
        self.size_is_relative_to_parent = other.size_is_relative_to_parent

        # Vec2 instances (Mutate in-place to avoid new memory allocations)
        # noinspection DuplicatedCode
        self.relative_position_global.xy = other.relative_position_global.xy
        self.absolute_position_global.xy = other.absolute_position_global.xy
        self.relative_size_global.xy = other.relative_size_global.xy
        self.absolute_size.xy = other.absolute_size.xy

        self.relative_position_to_parent.xy = other.relative_position_to_parent.xy
        self.absolute_position_to_parent.xy = other.absolute_position_to_parent.xy
        # noinspection DuplicatedCode
        self.relative_size_to_parent.xy = other.relative_size_to_parent.xy

        self.center.xy = other.center.xy
        self.top_left.xy = other.top_left.xy
        self.top_right.xy = other.top_right.xy
        self.bottom_left.xy = other.bottom_left.xy
        self.bottom_right.xy = other.bottom_right.xy


class UIElement(UIEntity):
    """Basic UI component with position and size stuff"""

    __NULL_VEC2: Vec2 = Vec2()
    __ONE_VEC2: Vec2 = Vec2().from_cartesian(1, 1)

    __data: UIElementData
    __last_data: UIElementData

    __changed_since_last_draw: bool

    def __init__(
            self,
            position: coord_t,
            size: coord_t,
            *_args: tp.Any,
            parent: UIEntity | None = None,
            placement_anchor: Anchor = Anchor.CENTER,
            absolute_values: bool = False,
            positon_is_relative_to_parent: bool = True,
            size_is_relative_to_parent: bool = True
    ) -> None:
        """
        Create a new UI component
        :param position: Relative position of the component (absolute if absolute_values is set to True)
        :param size: Relative size of the component (absolute if absolute_values is set to True)
        :param _args: Not used
        :param parent: Optional parent UI-Entity
        :param placement_anchor: Placement anchor of the component
        :param absolute_values: Whether the position and size are absolute or relative
        :param positon_is_relative_to_parent: Whether the position is relative to the parent or the screen
        :param size_is_relative_to_parent: Whether the size is relative to the parent or the screen
        """
        super().__init__(parent=parent, _is_ui_element=True)

        self.__data = UIElementData()
        self.__last_data = UIElementData()

        self.__data.position_is_relative_to_parent = positon_is_relative_to_parent
        self.__data.size_is_relative_to_parent = size_is_relative_to_parent
        self.__data.placement_anchor = placement_anchor

        if absolute_values:
            self.__data.absolute_position_to_parent.xy = convert_coord(position)
            self.__data.relative_position_to_parent.xy = convert_coord(
                self.__absolute_to_relative(self.__data.absolute_position_to_parent))
        else:
            self.__data.relative_position_to_parent.xy = convert_coord(position)
            self.__data.absolute_position_to_parent.xy = convert_coord(
                self.__relative_to_absolute(self.__data.relative_position_to_parent))

        if absolute_values:
            self.__data.absolute_size.xy = convert_coord(size)
            self.__data.relative_size_to_parent.xy = convert_coord(
                self.__absolute_to_relative(self.__data.absolute_size))
        else:
            self.__data.relative_size_to_parent.xy = convert_coord(size)
            self.__data.absolute_size.xy = convert_coord(
                self.__relative_to_absolute(self.__data.relative_size_to_parent))

        self._update_relative_values()

        self.__data.absolute_position_global.xy = (self.__data.reference_absolute_global_position
                                                   + self.__data.absolute_position_to_parent).xy
        self.__data.relative_position_global.xy = (self.__data.reference_relative_global_position
                                                   + self.__data.relative_position_to_parent).xy
        self.__data.relative_size_global.xy = (self.__data.reference_absolute_size
                                               * (self.__data.absolute_size / global_vars.resolution)).xy

        self.__changed_since_last_draw = True

    # region Methods: parent size/position
    @property
    def __reference_relative_size(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.size_is_relative_to_parent:
            return UIElement.__ONE_VEC2
        return self._next_ui_element_parent.relative_size_global

    @property
    def __reference_absolute_size(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.size_is_relative_to_parent:
            return global_vars.resolution
        return self._next_ui_element_parent.absolute_size_global

    @property
    def __reference_absolute_global_position(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.position_is_relative_to_parent:
            return UIElement.__NULL_VEC2
        return self._next_ui_element_parent.absolute_position_global

    @property
    def __reference_relative_global_position(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.position_is_relative_to_parent:
            return UIElement.__NULL_VEC2
        return self._next_ui_element_parent.relative_position_global

    def _update_relative_values(self) -> None:
        self.__data.relative_position_global.xy = self.__reference_relative_global_position.xy
        self.__data.relative_size_global.xy = self.__reference_relative_size.xy
        self.__data.absolute_position_global.xy = self.__reference_absolute_global_position.xy
        self.__data.absolute_size.xy = self.__reference_absolute_size.xy

    # endregion

    # region Methods: absolute/relative convert
    def __relative_to_absolute(
            self,
            relative_value: coord_t,
            reference: coord_t | None = None
    ) -> tuple[float, float]:
        """
        Converts relative coords to absolute coords according to the current resolution
        :param relative_value: Relative value to convert
        :param reference: Absolute reference value to convert relative coords to
        :return: Absolute value
        """
        abs_x, abs_y = convert_coord(relative_value)
        ref_x, ref_y = convert_coord(reference if reference else self.__data.reference_absolute_size)
        return abs_x * ref_x, abs_y * ref_y

    def __absolute_to_relative(
            self,
            absolute_value: coord_t,
            reference: coord_t | None = None
    ) -> tuple[float, float]:
        """
        Converts relative coords to absolute coords according to the current resolution
        :param absolute_value: Absolute value to convert
        :param reference: Absolute reference value to convert relative coords to
        :return: Relative value
        """
        rel_x, rel_y = convert_coord(absolute_value)
        ref_x, ref_y = convert_coord(reference if reference else self.__data.reference_absolute_size)
        return rel_x / ref_x, rel_y / ref_y

    # endregion

    # region Methods: drawing
    def __calc_values(self) -> None:
        # Dont change this. This is for scaling
        self._update_relative_values()

        # todo: ADD MODIFIED CHECKER CALL HERE
        self.__data.absolute_position_global.xy = self.__relative_to_absolute(self.__data.relative_position_global)
        self.__data.absolute_size.xy = self.__relative_to_absolute(self.__data.relative_size_global)

        self.__data.width = self.__data.absolute_size.x
        self.__data.height = self.__data.absolute_size.y

        if self.__data.placement_anchor == "nw":
            self.__data.top_left.xy = self.__data.absolute_position_global.xy
            self.__data.top_right.xy = (self.__data.absolute_position_global
                                        + convert_coord((self.__data.absolute_size.x, 0), Vec2)).xy
            self.__data.bottom_left.xy = (self.__data.absolute_position_global
                                          + convert_coord((0, self.__data.absolute_size.y), Vec2)).xy
            self.__data.bottom_right.xy = (self.__data.absolute_position_global + self.__data.absolute_size.y).xy

            self.__data.center.xy = (self.__data.absolute_position_global + self.__data.absolute_size / 2).xy

        elif self.placement_anchor == "center":
            self.__data.top_left.xy = (self.__data.absolute_position_global - self.__data.absolute_size / 2).xy
            self.__data.top_right.xy = (self.__data.absolute_position_global + convert_coord(
                (self.__data.absolute_size.x / 2, -self.__data.absolute_size.y / 2),
                Vec2)).xy
            self.__data.bottom_left.xy = (self.__data.absolute_position_global + convert_coord(
                (-self.__data.absolute_size.x / 2, self.__data.absolute_size.y / 2),
                Vec2)).xy
            self.__data.bottom_right.xy = (self.__data.absolute_position_global + self.__data.absolute_size / 2).xy

            self.__data.center.xy = self.__data.absolute_position_global.xy

    def _gl_draw(self) -> None:
        """
        The draw function called in loop

        It should always follow this structure:
        - Compare if anything changed, requiring redrawing of the collision surface/mask
        - Call super()._gl_draw()
        - Draw the UI and collision surface
        """
        self.__calc_values()

        if not self._ui_changed:
            if self.__data != self.__last_data:
                self._ui_changed = True

        self.__last_data.copy_from(self.__data)

        super()._gl_draw()

    def gl_draw(self, recursive: bool = True, force_draw: bool = False) -> None:
        super().gl_draw(recursive=recursive, force_draw=force_draw)
        self._ui_changed = False

    # endregion

    # region Methods: reset
    def _reset(self) -> None:
        super()._reset()
        self._ui_changed = True

    # endregion

    # region Methods: properties
    @property
    def _ui_changed(self) -> bool:
        """:return: Whether the UI has changed since the last draw"""
        return self.__changed_since_last_draw

    @_ui_changed.setter
    def _ui_changed(self, value: bool) -> None:
        """:param value: Set whether the UI has changed since the last draw"""
        self.__changed_since_last_draw = value
        self.__collision_recreation = value

    @property
    def absolute_position_global(self) -> Vec2:
        """:return: Absolute position - anchor not factored in"""
        if self.__last_relative_position.xy != self.__relative_position_global.xy:
            self.__absolute_position_global.xy = self.__relative_to_absolute(self.__relative_position_global)
            self.__last_relative_position.xy = self.__relative_position_global.xy
        return self.__absolute_position_global

    @absolute_position_global.setter
    def absolute_position_global(self, value: coord_t) -> None:
        """:param value: Absolute position"""
        self.__absolute_position_global.xy = convert_coord(value)
        self.__relative_position_global.xy = self.__absolute_to_relative(self.__absolute_position_global)

    @property
    def absolute_size_global(self) -> Vec2:
        """:return: Absolute size"""
        if self.__last_relative_size.xy != self.__relative_size_global.xy:
            self.__absolute_size.xy = self.__relative_to_absolute(self.__relative_size_global)
            self.__last_relative_size.xy = self.__relative_size_global.xy
        return self.__absolute_size

    @absolute_size_global.setter
    def absolute_size_global(self, value: coord_t) -> None:
        """:param value: Absolute size"""
        self.__absolute_size.xy = convert_coord(value)
        self.__relative_size_global.xy = self.__absolute_to_relative(self.__absolute_size)

    @property
    def relative_position_global(self) -> Vec2:
        """:return: Relative position - anchor not factored in"""
        if self.__absolute_position_global.xy != self.__last_absolute_position.xy:
            self.__relative_position_global.xy = self.__absolute_to_relative(self.__absolute_position_global)
            self.__last_absolute_position.xy = self.__absolute_position_global.xy
        return self.__relative_position_global

    @relative_position_global.setter
    def relative_position_global(self, value: coord_t) -> None:
        """:param value: Relative position"""
        self.__relative_position_global.xy = convert_coord(value)
        self.__absolute_position_global.xy = self.__relative_to_absolute(self.__relative_position_global)

    @property
    def relative_size_global(self) -> Vec2:
        """:return: Relative size"""
        if self.__absolute_size.xy != self.__last_absolute_size.xy:
            self.__relative_size_global.xy = self.__absolute_to_relative(self.__absolute_size)
            self.__last_absolute_size.xy = self.__absolute_size.xy
        return self.__relative_size_global

    @relative_size_global.setter
    def relative_size_global(self, value: coord_t) -> None:
        """:param value: Relative size"""
        self.__relative_size_global.xy = convert_coord(value)
        self.__absolute_size.xy = self.__relative_to_absolute(self.__relative_size_global)

    # todo: refactor properties after here
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
