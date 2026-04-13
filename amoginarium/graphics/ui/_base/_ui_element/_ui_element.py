"""
amoginarium/graphics/ui/_base/_ui_element/_ui_element.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.utility import Vec2, coord_t, convert_coord, TupleMath
from amoginarium import pv

from ..._types import Anchor, Positions
from .._ui_entity import UIEntity
from ._ui_element_values import UIElementValueVec2, UIElementValueFloatOneAbsolute, UIElementValueVec2OneAbsolute
from ._ui_element_values import UIElementData, UIElementValueNamesEnum, UIElementValueTypesEnum


class UIElement(UIEntity):
    """Basic UI component with position and size stuff"""
    __NULL_VEC2: tp.ClassVar[Vec2] = Vec2()
    __ONE_VEC2: tp.ClassVar[Vec2] = Vec2().from_cartesian(1, 1)

    __data: UIElementData
    __last_data: UIElementData

    __changed_since_last_draw: bool

    __absolute_values: bool

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
    ) -> None:
        """
        Create a new UI component
        :param position: Relative position of the component (absolute if absolute_values is set to True)
        :param size: Relative size of the component (absolute if absolute_values is set to True)
        :param parent: Optional parent UI-Entity
        :param placement_anchor: Placement anchor of the component
        :param absolute_values: Whether the position and size are absolute or relative
        :param positon_is_relative_to_parent: WWhether the position is relative to the parent or the screen
        :param size_is_relative_to_parent: Whether the size is relative to the parent or the screen
        :param parent_reference_position: What reference position of the parent component to use
        """
        super().__init__(parent=parent)

        self.__absolute_values = absolute_values

        self.__data = UIElementData()
        self.__last_data = UIElementData()

        self.__data.position_is_relative_to_parent = positon_is_relative_to_parent
        self.__data.size_is_relative_to_parent = size_is_relative_to_parent
        self.__data.placement_anchor = placement_anchor
        self.__data.parent_reference_position = parent_reference_position

        self._update_relative_values()
        if absolute_values:
            self.__data.position.relative_to_parent = self.__absolute_to_relative(position, calc_for="position")
            self.__data.size.relative_to_parent = self.__absolute_to_relative(size)
        else:
            self.__data.position.relative_to_parent = position
            self.__data.size.relative_to_parent = size

        self.__changed_since_last_draw = True
        self.__calc_values(pass_check=True)

    # region Methods: absolute/relative convert
    def _update_relative_values(self) -> None:
        """Update reference position and size"""
        if self.__data.position_is_relative_to_parent and self._next_ui_element_parent is not None:
            match self.__data.parent_reference_position:
                case Positions.TOP_LEFT:
                    self.__data.reference_position.copy_from(self._next_ui_element_parent._top_left)
                case Positions.TOP_RIGHT:
                    self.__data.reference_position.copy_from(self._next_ui_element_parent._top_right)
                case Positions.BOTTOM_LEFT:
                    self.__data.reference_position.copy_from(self._next_ui_element_parent._bottom_left)
                case Positions.BOTTOM_RIGHT:
                    self.__data.reference_position.copy_from(self._next_ui_element_parent._bottom_right)
                case Positions.CENTER:
                    self.__data.reference_position.copy_from(self._next_ui_element_parent._center)
                case _:
                    raise ValueError(f"Invalid anchor: {self.__data.parent_reference_position}.")
        else:
            self.__data.reference_position.absolute_global = self.__NULL_VEC2
            self.__data.reference_position.absolute_to_parent = self.__NULL_VEC2
            self.__data.reference_position.relative_global = self.__NULL_VEC2
            self.__data.reference_position.relative_to_parent = self.__NULL_VEC2

        if self.__data.size_is_relative_to_parent and self._next_ui_element_parent is not None:
            self.__data.reference_size.copy_from(self._next_ui_element_parent._size)
        else:
            self.__data.reference_size.absolute = pv.global_vars.get_resolution()
            self.__data.reference_size.relative_global = self.__ONE_VEC2
            self.__data.reference_size.relative_to_parent = self.__ONE_VEC2

        if self._next_ui_element_parent is not None:
            self.__data.reference_size_for_position.copy_from(self._next_ui_element_parent._size)
        else:
            self.__data.reference_size_for_position.absolute = pv.global_vars.get_resolution()
            self.__data.reference_size_for_position.relative_global = self.__ONE_VEC2
            self.__data.reference_size_for_position.relative_to_parent = self.__ONE_VEC2

    def __relative_to_absolute(
            self,
            relative_value: coord_t,
            reference: coord_t | None = None,
            calc_for: tp.Literal["position", "size"] = "size"
    ) -> tuple[float, float]:
        """
        Converts relative coords to absolute coords according to the current resolution
        :param relative_value: Relative value to convert
        :param reference: Absolute reference value to convert relative coords to
        :param calc_for: Whether the transformation is for size or position
        :return: Absolute value
        """
        return TupleMath.mul(
            convert_coord(relative_value),
            convert_coord(
                reference if reference else (
                    self.__data.reference_size.absolute if (
                            calc_for == "size" and self.__data.size_is_relative_to_parent
                    ) else (
                        self.__data.reference_size_for_position.absolute if (
                                calc_for == "position" and self.__data.position_is_relative_to_parent
                        ) else pv.global_vars.get_resolution())
                ))
        )

    def __absolute_to_relative(
            self,
            absolute_value: coord_t,
            reference: coord_t | None = None,
            calc_for: tp.Literal["position", "size"] = "size"
    ) -> tuple[float, float]:
        """
        Converts relative coords to absolute coords according to the current resolution
        :param absolute_value: Absolute value to convert
        :param reference: Absolute reference value to convert relative coords to
        :param calc_for: Whether the transformation is for size or position
        :return: Relative value
        """
        return TupleMath.div(
            convert_coord(absolute_value),
            convert_coord(
                reference if reference else (
                    self.__data.reference_size.absolute if (
                            calc_for == "size" and self.__data.size_is_relative_to_parent
                    ) else (
                        self.__data.reference_size_for_position.absolute if (
                                calc_for == "position" and self.__data.position_is_relative_to_parent
                        ) else pv.global_vars.get_resolution())
                ))
        )

    # endregion

    # region Methods: drawing
    # noinspection DuplicatedCode
    def __check_modifications(self) -> bool:
        """
        Detects external modifications by comparing data to last_data.
        Calculates relative_position_to_parent and relative_size_to_parent from the changed values.
        """
        is_neq, value_name, value_type = self.__data.not_equal(self.__last_data)

        if is_neq:
            match value_name:
                case UIElementValueNamesEnum.WIDTH:
                    value_name = UIElementValueNamesEnum.SIZE
                    match value_type:
                        case UIElementValueTypesEnum.ABSOLUTE:
                            self.__data.size.absolute.x = self.__data.width.absolute
                        case UIElementValueTypesEnum.RELATIVE_GLOBAL:
                            self.__data.size.relative_global.x = self.__data.width.relative_global
                        case UIElementValueTypesEnum.RELATIVE_TO_PARENT:
                            self.__data.size.relative_to_parent.x = self.__data.width.relative_to_parent
                        case _:
                            raise ValueError(f"Invalid value type: {value_type}.")
                case UIElementValueNamesEnum.HEIGHT:
                    value_name = UIElementValueNamesEnum.SIZE
                    match value_type:
                        case UIElementValueTypesEnum.ABSOLUTE:
                            self.__data.size.absolute.y = self.__data.height.absolute
                        case UIElementValueTypesEnum.RELATIVE_GLOBAL:
                            self.__data.size.relative_global.y = self.__data.height.relative_global
                        case UIElementValueTypesEnum.RELATIVE_TO_PARENT:
                            self.__data.size.relative_to_parent.y = self.__data.height.relative_to_parent
                        case _:
                            raise ValueError(f"Invalid value type: {value_type}.")
                case (
                UIElementValueNamesEnum.CENTER
                | UIElementValueNamesEnum.TOP_LEFT
                | UIElementValueNamesEnum.TOP_RIGHT
                | UIElementValueNamesEnum.BOTTOM_LEFT
                | UIElementValueNamesEnum.BOTTOM_RIGHT):
                    modified_obj = getattr(self.__data, value_name.name.lower())

                    if value_type in (UIElementValueTypesEnum.ABSOLUTE_GLOBAL,
                                      UIElementValueTypesEnum.ABSOLUTE_TO_PARENT):
                        size_xy = self.__data.size.absolute.xy
                    elif value_type == UIElementValueTypesEnum.RELATIVE_GLOBAL:
                        size_xy = self.__data.size.relative_global.xy
                    elif value_type == UIElementValueTypesEnum.RELATIVE_TO_PARENT:
                        size_xy = self.__data.size.relative_to_parent.xy
                    else:
                        raise ValueError(f"Invalid value type: {value_type}.")

                    half_size_xy = TupleMath.div(size_xy, (2, 2))

                    match value_name:
                        case UIElementValueNamesEnum.TOP_LEFT:
                            mod_coord = (0.0, 0.0)
                        case UIElementValueNamesEnum.TOP_RIGHT:
                            mod_coord = (size_xy[0], 0.0)
                        case UIElementValueNamesEnum.BOTTOM_LEFT:
                            mod_coord = (0.0, size_xy[1])
                        case UIElementValueNamesEnum.BOTTOM_RIGHT:
                            mod_coord = size_xy
                        case UIElementValueNamesEnum.CENTER:
                            mod_coord = half_size_xy

                    match self.__data.placement_anchor:
                        case Anchor.NW:
                            anchor_coord = (0.0, 0.0)
                        case Anchor.NE:
                            anchor_coord = (size_xy[0], 0.0)
                        case Anchor.SW:
                            anchor_coord = (0.0, size_xy[1])
                        case Anchor.SE:
                            anchor_coord = size_xy
                        case Anchor.CENTER:
                            anchor_coord = half_size_xy

                    offset_xy = (mod_coord[0] - anchor_coord[0], mod_coord[1] - anchor_coord[1])

                    match value_type:
                        case UIElementValueTypesEnum.ABSOLUTE_GLOBAL:
                            self.__data.position.absolute_global = TupleMath.sub(
                                modified_obj.absolute_global.xy, offset_xy)
                        case UIElementValueTypesEnum.ABSOLUTE_TO_PARENT:
                            self.__data.position.absolute_to_parent = TupleMath.sub(
                                modified_obj.absolute_to_parent.xy, offset_xy)
                        case UIElementValueTypesEnum.RELATIVE_GLOBAL:
                            self.__data.position.relative_global = TupleMath.sub(
                                modified_obj.relative_global.xy, offset_xy)
                        case UIElementValueTypesEnum.RELATIVE_TO_PARENT:
                            self.__data.position.relative_to_parent = TupleMath.sub(
                                modified_obj.relative_to_parent.xy, offset_xy)

                    value_name = UIElementValueNamesEnum.POSITION
                case _:
                    ...

            match value_name:
                case UIElementValueNamesEnum.POSITION:
                    match value_type:
                        case UIElementValueTypesEnum.ABSOLUTE_GLOBAL:
                            self.__data.position.relative_to_parent = self.__absolute_to_relative(
                                TupleMath.sub(
                                    self.__data.position.absolute_global.xy,
                                    self.__data.reference_position.absolute_global.xy
                                ),
                                calc_for="position"
                            )
                        case UIElementValueTypesEnum.ABSOLUTE_TO_PARENT:
                            self.__data.position.relative_to_parent = self.__absolute_to_relative(
                                self.__data.position.absolute_to_parent, calc_for="position"
                            )
                        case UIElementValueTypesEnum.RELATIVE_GLOBAL:
                            self.__data.position.relative_to_parent = TupleMath.div(
                                TupleMath.sub(
                                    self.__data.position.relative_global.xy,
                                    self.__data.reference_position.relative_global.xy),
                                self.__data.reference_size_for_position.relative_global.xy
                            )
                        case UIElementValueTypesEnum.RELATIVE_TO_PARENT:
                            ...  # Calculations bases from here, no action needed
                        case _:
                            raise ValueError(f"Invalid value type: {value_type}.")
                case UIElementValueNamesEnum.SIZE:
                    match value_type:
                        case UIElementValueTypesEnum.ABSOLUTE:
                            self.__data.size.relative_to_parent = self.__absolute_to_relative(
                                self.__data.size.absolute
                            )
                        case UIElementValueTypesEnum.RELATIVE_GLOBAL:
                            self.__data.size.relative_to_parent = TupleMath.div(
                                self.__data.size.relative_global.xy,
                                self.__data.reference_size.relative_global.xy
                            )
                        case UIElementValueTypesEnum.RELATIVE_TO_PARENT:
                            ...  # Calculations bases from here, no action needed
                        case _:
                            raise ValueError(f"Invalid value type: {value_type}.")
                case UIElementValueNamesEnum.POSITION_IS_RELATIVE_TO_PARENT:
                    ...
                case UIElementValueNamesEnum.SIZE_IS_RELATIVE_TO_PARENT:
                    ...
                case (
                UIElementValueNamesEnum.PLACEMENT_ANCHOR
                | UIElementValueNamesEnum.REFERENCE_POSITION
                | UIElementValueNamesEnum.REFERENCE_SIZE
                | UIElementValueNamesEnum.PARENT_REFERENCE_POSITION):
                    ...  # No change to relative position to parent or relative size to parent
                case _:
                    raise ValueError(f"Invalid value name: {value_name}. IDK HOW THIS HAPPENS. CONTACT DEVELOPERS.")

        return is_neq

    # noinspection DuplicatedCode
    def __calc_values(self, pass_check: bool = False) -> None:
        self._update_relative_values()

        if not pass_check:
            if not self.__check_modifications():
                return

        # position relative to parent and size relative to parent are always true already

        # region Position
        self.__data.position.absolute_to_parent = self.__relative_to_absolute(
            self.__data.position.relative_to_parent, calc_for="position")
        self.__data.position.absolute_global = TupleMath.add(
            self.__data.reference_position.absolute_global.xy,
            self.__data.position.absolute_to_parent.xy
        )
        self.__data.position.relative_global = TupleMath.add(
            self.__data.reference_position.relative_global.xy,
            self.__data.position.relative_to_parent.xy
        )
        # endregion

        # region Size
        self.__data.size.absolute = self.__relative_to_absolute(self.__data.size.relative_to_parent)
        self.__data.size.relative_global = TupleMath.mul(
            self.__data.size.relative_to_parent.xy,
            self.__data.reference_size.relative_global.xy
        )
        # endregion

        # region Width
        self.__data.width.absolute = self.__data.size.absolute.x
        self.__data.width.relative_global = self.__data.size.relative_global.x
        self.__data.width.relative_to_parent = self.__data.size.relative_to_parent.x
        # endregion

        # region Height
        self.__data.height.absolute = self.__data.size.absolute.y
        self.__data.height.relative_global = self.__data.size.relative_global.y
        self.__data.height.relative_to_parent = self.__data.size.relative_to_parent.y
        # endregion

        # region Positions
        match self.__data.placement_anchor:
            case Anchor.NW:
                ax, ay = 0.0, 0.0
            case Anchor.NE:
                ax, ay = 1.0, 0.0
            case Anchor.SW:
                ax, ay = 0.0, 1.0
            case Anchor.SE:
                ax, ay = 1.0, 1.0
            case Anchor.CENTER:
                ax, ay = 0.5, 0.5
            case _:
                raise ValueError(f"Invalid anchor: {self.__data.placement_anchor}")

        pos = self.__data.position
        sz_abs = self.__data.size.absolute.xy
        sz_rg = self.__data.size.relative_global.xy
        sz_rtp = self.__data.size.relative_to_parent.xy

        targets = [
            (self.__data.top_left, 0.0, 0.0),
            (self.__data.top_right, 1.0, 0.0),
            (self.__data.bottom_left, 0.0, 1.0),
            (self.__data.bottom_right, 1.0, 1.0),
            (self.__data.center, 0.5, 0.5),
        ]

        for target_obj, px, py in targets:
            if px == ax and py == ay:
                target_obj.copy_from(pos)
                continue

            dx, dy = px - ax, py - ay

            off_abs = (sz_abs[0] * dx, sz_abs[1] * dy)
            off_rg = (sz_rg[0] * dx, sz_rg[1] * dy)
            off_rtp = (sz_rtp[0] * dx, sz_rtp[1] * dy)

            target_obj.absolute_global = TupleMath.add(pos.absolute_global.xy, off_abs)
            target_obj.absolute_to_parent = TupleMath.add(pos.absolute_to_parent.xy, off_abs)
            target_obj.relative_global = TupleMath.add(pos.relative_global.xy, off_rg)
            target_obj.relative_to_parent = TupleMath.add(pos.relative_to_parent.xy, off_rtp)

        # endregion

        self._ui_changed = True
        self.__last_data.copy_from(self.__data)

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        """
        The draw function called in loop

        It should always follow this structure:
        - Compare if anything changed, requiring redrawing of the collision surface/mask
        - Call super()._gl_draw()
        - Draw the UI and collision surface
        """
        self.__calc_values()

        super()._gl_draw(delta_cal, layer)

    def _after_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        super()._after_gl_draw(drawn, layer)
        self._ui_changed = False

    # endregion

    # region Methods: reset
    def _reset(self) -> None:
        super()._reset()
        self._ui_changed = True

    # endregion

    # region Methods: properties
    def _next_ui_element_parent_recursion(self) -> UIElement:
        return self

    @property
    def _ui_changed(self) -> bool:
        """:return: Whether the UI has changed since the last draw"""
        return self.__changed_since_last_draw

    @_ui_changed.setter
    def _ui_changed(self, value: bool) -> None:
        """:param value: Set whether the UI has changed since the last draw"""
        self.__changed_since_last_draw = value

    @property
    def _placement_anchor(self) -> Anchor:
        """:return: Placement anchor without triggering a calculation"""
        return self.__data.placement_anchor

    @property
    def placement_anchor(self) -> Anchor:
        """:return: Placement anchor"""
        self.__calc_values()
        return self.__data.placement_anchor

    @placement_anchor.setter
    def placement_anchor(self, value: Anchor) -> None:
        """:param value: Placement anchor"""
        self.__calc_values()
        self.__data.placement_anchor = value

    @property
    def _position_is_relative_to_parent(self) -> bool:
        """:return: Whether position is relative to parent without triggering a calculation"""
        return self.__data.position_is_relative_to_parent

    @property
    def position_is_relative_to_parent(self) -> bool:
        """:return: Whether position is relative to parent"""
        self.__calc_values()
        return self.__data.position_is_relative_to_parent

    @position_is_relative_to_parent.setter
    def position_is_relative_to_parent(self, value: bool) -> None:
        """:param value: Set position relativity"""
        self.__calc_values()
        self.__data.position_is_relative_to_parent = bool(value)

    @property
    def _size_is_relative_to_parent(self) -> bool:
        """:return: Whether size is relative to parent without triggering a calculation"""
        return self.__data.size_is_relative_to_parent

    @property
    def size_is_relative_to_parent(self) -> bool:
        """:return: Whether size is relative to parent"""
        self.__calc_values()
        return self.__data.size_is_relative_to_parent

    @size_is_relative_to_parent.setter
    def size_is_relative_to_parent(self, value: bool) -> None:
        """:param value: Set size relativity"""
        self.__calc_values()
        self.__data.size_is_relative_to_parent = bool(value)

    @property
    def _position(self) -> UIElementValueVec2:
        """:return: Position of the UI element without triggering a calculation"""
        return self.__data.position

    @property
    def position(self) -> UIElementValueVec2:
        """:return: Position of the UI element"""
        self.__calc_values()
        return self.__data.position

    @position.setter
    def position(self, value: coord_t) -> None:
        """:param value: Absolute/relative (same as initialized) Position to parent of the UI element."""
        self.__calc_values()
        if self.__absolute_values:
            self.__data.position.absolute_to_parent = value
        else:
            self.__data.position.relative_to_parent = value

    @property
    def _size(self) -> UIElementValueVec2OneAbsolute:
        """:return: Size of the UI element without triggering a calculation"""
        return self.__data.size

    @property
    def size(self) -> UIElementValueVec2OneAbsolute:
        """:return: Size of the UI element"""
        self.__calc_values()
        return self.__data.size

    @size.setter
    def size(self, value: coord_t) -> None:
        """:param value: Absolute/relative (same as initialized) size to parent."""
        self.__calc_values()
        if self.__absolute_values:
            self.__data.size.absolute = value
        else:
            self.__data.size.relative_to_parent = value

    @property
    def _width(self) -> UIElementValueFloatOneAbsolute:
        """:return: Width of the UI element without triggering a calculation"""
        return self.__data.width

    @property
    def width(self) -> UIElementValueFloatOneAbsolute:
        """:return: Width of the UI element"""
        self.__calc_values()
        return self.__data.width

    @width.setter
    def width(self, value: float) -> None:
        """:param value: Absolute/relative (same as initialized) width to parent."""
        self.__calc_values()
        if self.__absolute_values:
            self.__data.width.absolute = value
        else:
            self.__data.width.relative_to_parent = value

    @property
    def _height(self) -> UIElementValueFloatOneAbsolute:
        """:return: Height of the UI element without triggering a calculation"""
        return self.__data.height

    @property
    def height(self) -> UIElementValueFloatOneAbsolute:
        """:return: Height of the UI element"""
        self.__calc_values()
        return self.__data.height

    @height.setter
    def height(self, value: float) -> None:
        """:param value: Absolute/relative (same as initialized) height to parent."""
        self.__calc_values()
        if self.__absolute_values:
            self.__data.height.absolute = value
        else:
            self.__data.height.relative_to_parent = value

    @property
    def _center(self) -> UIElementValueVec2:
        """:return: Center of the UI element without triggering a calculation"""
        return self.__data.center

    @property
    def center(self) -> UIElementValueVec2:
        """:return: Center of the UI element"""
        self.__calc_values()
        return self.__data.center

    @center.setter
    def center(self, value: coord_t) -> None:
        """:param value: Absolute global position of the center of the UI element."""
        self.__calc_values()
        self.__data.center.absolute_global = value

    @property
    def _top_left(self) -> UIElementValueVec2:
        """:return: Top left position of the UI element without triggering a calculation"""
        return self.__data.top_left

    @property
    def top_left(self) -> UIElementValueVec2:
        """:return: Top left position of the UI element"""
        self.__calc_values()
        return self.__data.top_left

    @top_left.setter
    def top_left(self, value: coord_t) -> None:
        """:param value: Absolute global position of the top left corner of the UI element."""
        self.__calc_values()
        self.__data.top_left.absolute_global = value

    @property
    def _top_right(self) -> UIElementValueVec2:
        """:return: Top right position of the UI element without triggering a calculation"""
        return self.__data.top_right

    @property
    def top_right(self) -> UIElementValueVec2:
        """:return: Top right position of the UI element"""
        self.__calc_values()
        return self.__data.top_right

    @top_right.setter
    def top_right(self, value: coord_t) -> None:
        """:param value: Absolute global position of the top right corner of the UI element."""
        self.__calc_values()
        self.__data.top_right.absolute_global = value

    @property
    def _bottom_left(self) -> UIElementValueVec2:
        """:return: Bottom left position of the UI element without triggering a calculation"""
        return self.__data.bottom_left

    @property
    def bottom_left(self) -> UIElementValueVec2:
        """:return: Bottom left position of the UI element"""
        self.__calc_values()
        return self.__data.bottom_left

    @bottom_left.setter
    def bottom_left(self, value: coord_t) -> None:
        """:param value: Absolute global position of the bottom left corner of the UI element."""
        self.__calc_values()
        self.__data.bottom_left.absolute_global = value

    @property
    def _bottom_right(self) -> UIElementValueVec2:
        """:return: Bottom right position of the UI element without triggering a calculation"""
        return self.__data.bottom_right

    @property
    def bottom_right(self) -> UIElementValueVec2:
        """:return: Bottom right position of the UI element"""
        self.__calc_values()
        return self.__data.bottom_right

    @bottom_right.setter
    def bottom_right(self, value: coord_t) -> None:
        """:param value: Absolute global position of the bottom right corner of the UI element."""
        self.__calc_values()
        self.__data.bottom_right.absolute_global = value

    @property
    def _parent_reference_position(self) -> UIElementValueVec2:
        """:return: Reference position of the parent without triggering a calculation"""
        return self.__data.reference_position

    @property
    def parent_reference_position(self) -> UIElementValueVec2:
        """:return: Reference position of the parent"""
        self.__calc_values()
        return self.__data.reference_position

    @parent_reference_position.setter
    def parent_reference_position(self, value: Positions) -> None:
        """:param value: Reference position of the parent"""
        self.__calc_values()
        self.__data.parent_reference_position = value

    # endregion
