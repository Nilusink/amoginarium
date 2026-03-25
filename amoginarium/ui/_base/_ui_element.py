"""
amoginarium/ui/_base/_ui_element.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

from dataclasses import dataclass, field
import typing as tp

from amoginarium.logic import Vec2, coord_t, convert_coord, TupleMath
from amoginarium.shared import global_vars

from ._ui_entity import UIEntity

from .._types import Anchor


T = tp.TypeVar('T')


class LazyProp(tp.Generic[T]):
    """
    Descriptor that lazily initializes an attribute upon first access.
    """

    def __init__(self, factory: tp.Callable[[], T], writable: bool = True):
        """
        :param factory: A callable that returns the initial value.
        :param writable: Determines if the property can be reassigned after initialization.
        """
        self.factory = factory
        self.writable = writable

    def __set_name__(self, owner, name):
        """
        :param owner: The class that owns the descriptor.
        :param name: The name of the descriptor assigned in the owner class.
        """
        self.private_name = f"_{name}"

    def __get__(self, instance, owner) -> T:
        """
        :param instance: The instance accessed, or None if accessed via the class.
        :param owner: The owner class.
        :return: The lazily initialized value of type T.
        """
        if instance is None:
            return self

        if not hasattr(instance, self.private_name):
            setattr(instance, self.private_name, self.factory())

        return getattr(instance, self.private_name)

    def __set__(self, instance, value: T):
        """
        :param instance: The instance where the value is being set.
        :param value: The value to assign to the property.
        :raises AttributeError: If the property was initialized with writable=False.
        """
        if not self.writable:
            raise AttributeError(f"Cannot set read-only attribute '{self.private_name.lstrip('_')}'")
        setattr(instance, self.private_name, value)


class LazyVec2(LazyProp[Vec2]):
    """
    Specific descriptor for Vec2 that mutates the existing instance's .xy
    values instead of replacing the object reference.
    """

    def __set__(self, instance, value: coord_t):
        """
        :param instance: The instance where the value is being set.
        :param value: The coordinate value (tuple, list, or Vec2) to apply to .xy.
        :raises AttributeError: If the property was initialized with writable=False.
        """
        current_vec = self.__get__(instance, type(instance))
        current_vec.xy = convert_coord(value)


class UIElementValueFloat:
    """
    Absolute/Relative and global/to parent metrics for a single float value.
    """
    absolute_global: float = LazyProp(float)
    absolute_to_parent: float = LazyProp(float)
    relative_global: float = LazyProp(float)
    relative_to_parent: float = LazyProp(float)

    def copy_from(self, other: 'UIElementValueFloat') -> None:
        """Copies values only if they have been lazily initialized in the source."""
        if '_absolute_global' in other.__dict__:
            self.absolute_global = other.__dict__['_absolute_global']
        if '_absolute_to_parent' in other.__dict__:
            self.absolute_to_parent = other.__dict__['_absolute_to_parent']
        if '_relative_global' in other.__dict__:
            self.relative_global = other.__dict__['_relative_global']
        if '_relative_to_parent' in other.__dict__:
            self.relative_to_parent = other.__dict__['_relative_to_parent']

    def __ne__(self, other: 'UIElementValueFloat') -> bool:
        """Checks for inequality without triggering lazy initialization."""
        if '_absolute_global' in self.__dict__ or '_absolute_global' in other.__dict__:
            if self.absolute_global != other.absolute_global: return True

        if '_absolute_to_parent' in self.__dict__ or '_absolute_to_parent' in other.__dict__:
            if self.absolute_to_parent != other.absolute_to_parent: return True

        if '_relative_global' in self.__dict__ or '_relative_global' in other.__dict__:
            if self.relative_global != other.relative_global: return True

        if '_relative_to_parent' in self.__dict__ or '_relative_to_parent' in other.__dict__:
            if self.relative_to_parent != other.relative_to_parent: return True

        return False

    def __eq__(self, other: 'UIElementValueFloat') -> bool:
        return not self.__ne__(other)


class UIElementValueFloatOneAbsolute:
    """
    Float value representation containing a single absolute value alongside relative metrics.
    """
    absolute: float = LazyProp(float)
    relative_global: float = LazyProp(float)
    relative_to_parent: float = LazyProp(float)

    def copy_from(self, other: 'UIElementValueFloatOneAbsolute') -> None:
        if '_absolute' in other.__dict__:
            self.absolute = other.__dict__['_absolute']
        if '_relative_global' in other.__dict__:
            self.relative_global = other.__dict__['_relative_global']
        if '_relative_to_parent' in other.__dict__:
            self.relative_to_parent = other.__dict__['_relative_to_parent']

    def __ne__(self, other: 'UIElementValueFloatOneAbsolute') -> bool:
        if '_absolute' in self.__dict__ or '_absolute' in other.__dict__:
            if self.absolute != other.absolute: return True

        if '_relative_global' in self.__dict__ or '_relative_global' in other.__dict__:
            if self.relative_global != other.relative_global: return True

        if '_relative_to_parent' in self.__dict__ or '_relative_to_parent' in other.__dict__:
            if self.relative_to_parent != other.relative_to_parent: return True

        return False

    def __eq__(self, other: 'UIElementValueFloatOneAbsolute') -> bool:
        return not self.__ne__(other)


class UIElementValueVec2:
    """
    Absolute/Relative and global/to parent of a Vec2 value crossed.
    Values can be set like coord_t, but get is always Vec2.
    """
    absolute_global: coord_t = LazyVec2(Vec2, writable=False)
    absolute_to_parent: coord_t = LazyVec2(Vec2, writable=False)
    relative_global: coord_t = LazyVec2(Vec2, writable=False)
    relative_to_parent: coord_t = LazyVec2(Vec2, writable=False)

    def copy_from(self, other: 'UIElementValueVec2') -> None:
        # We assign the `.xy` tuple to self so it hits LazyVec2.__set__ and mutates in place
        if '_absolute_global' in other.__dict__:
            self.absolute_global = other.__dict__['_absolute_global'].xy
        if '_absolute_to_parent' in other.__dict__:
            self.absolute_to_parent = other.__dict__['_absolute_to_parent'].xy
        if '_relative_global' in other.__dict__:
            self.relative_global = other.__dict__['_relative_global'].xy
        if '_relative_to_parent' in other.__dict__:
            self.relative_to_parent = other.__dict__['_relative_to_parent'].xy

    def __ne__(self, other: 'UIElementValueVec2') -> bool:
        if '_absolute_global' in self.__dict__ or '_absolute_global' in other.__dict__:
            if self.absolute_global.xy != other.absolute_global.xy: return True

        if '_absolute_to_parent' in self.__dict__ or '_absolute_to_parent' in other.__dict__:
            if self.absolute_to_parent.xy != other.absolute_to_parent.xy: return True

        if '_relative_global' in self.__dict__ or '_relative_global' in other.__dict__:
            if self.relative_global.xy != other.relative_global.xy: return True

        if '_relative_to_parent' in self.__dict__ or '_relative_to_parent' in other.__dict__:
            if self.relative_to_parent.xy != other.relative_to_parent.xy: return True

        return False

    def __eq__(self, other: 'UIElementValueVec2') -> bool:
        return not self.__ne__(other)


class UIElementValueVec2OneAbsolute:
    """
    Vec2 value representation containing a single absolute value alongside relative metrics.
    Values can be set like coord_t, but get is always Vec2.
    """
    absolute: coord_t = LazyVec2(Vec2, writable=False)
    relative_global: coord_t = LazyVec2(Vec2, writable=False)
    relative_to_parent: coord_t = LazyVec2(Vec2, writable=False)

    def copy_from(self, other: 'UIElementValueVec2OneAbsolute') -> None:
        if '_absolute' in other.__dict__:
            self.absolute = other.__dict__['_absolute'].xy
        if '_relative_global' in other.__dict__:
            self.relative_global = other.__dict__['_relative_global'].xy
        if '_relative_to_parent' in other.__dict__:
            self.relative_to_parent = other.__dict__['_relative_to_parent'].xy

    def __ne__(self, other: 'UIElementValueVec2OneAbsolute') -> bool:
        if '_absolute' in self.__dict__ or '_absolute' in other.__dict__:
            if self.absolute.xy != other.absolute.xy: return True

        if '_relative_global' in self.__dict__ or '_relative_global' in other.__dict__:
            if self.relative_global.xy != other.relative_global.xy: return True

        if '_relative_to_parent' in self.__dict__ or '_relative_to_parent' in other.__dict__:
            if self.relative_to_parent.xy != other.relative_to_parent.xy: return True

        return False

    def __eq__(self, other: 'UIElementValueVec2OneAbsolute') -> bool:
        return not self.__ne__(other)



class UIElementData:
    """
    Position data for UIElement that can all influence each other
    Everything with a default value None is only calculated when used
    """
    placement_anchor: Anchor

    position: UIElementValueVec2
    size: UIElementValueVec2OneAbsolute

    width: UIElementValueFloatOneAbsolute
    height: UIElementValueFloatOneAbsolute
    center: UIElementValueVec2
    top_left: UIElementValueVec2
    top_right: UIElementValueVec2
    bottom_left: UIElementValueVec2
    bottom_right: UIElementValueVec2

    position_is_relative_to_parent: bool = True
    size_is_relative_to_parent: bool = True

    reference_ui_element: UIEntity | None

    def __init__(self) -> None:
        self.placement_anchor = Anchor.CENTER
        self.position = UIElementValueVec2()
        self.size = UIElementValueVec2OneAbsolute()

        self.width = UIElementValueFloatOneAbsolute()
        self.height = UIElementValueFloatOneAbsolute()
        self.center = UIElementValueVec2()
        self.top_left = UIElementValueVec2()
        self.top_right = UIElementValueVec2()
        self.bottom_left = UIElementValueVec2()
        self.bottom_right = UIElementValueVec2()

        self.position_is_relative_to_parent = True
        self.size_is_relative_to_parent = True

        self.reference_ui_element = None

    def copy_from(self, other: UIElementData) -> None:
        """Updates this instance with values from another in-place."""
        self.placement_anchor = other.placement_anchor
        self.position_is_relative_to_parent = other.position_is_relative_to_parent
        self.size_is_relative_to_parent = other.size_is_relative_to_parent

        self.position.copy_from(other.position)
        self.size.copy_from(other.size)

        self.width.copy_from(other.width)
        self.height.copy_from(other.height)
        self.center.copy_from(other.center)
        self.top_left.copy_from(other.top_left)
        self.top_right.copy_from(other.top_right)
        self.bottom_left.copy_from(other.bottom_left)
        self.bottom_right.copy_from(other.bottom_right)

    def __ne__(self, other: object) -> bool:
        """Explicitly compares all values to guarantee detection of changes."""
        if not isinstance(other, UIElementData):
            return NotImplemented

        if (
                self.placement_anchor != other.placement_anchor
                or self.position_is_relative_to_parent != other.position_is_relative_to_parent
                or self.size_is_relative_to_parent != other.size_is_relative_to_parent
        ):
            return True

        if (
                self.width != other.width
                or self.height != other.height
                or self.center != other.center
                or self.top_left != other.top_left
                or self.top_right != other.top_right
                or self.bottom_left != other.bottom_left
                or self.bottom_right != other.bottom_right
                or self.position != other.position
                or self.size != other.size
        ):
            return True

        return False

    def __eq__(self, other: object) -> bool:
        return not self.__ne__(other)


class UIElement(UIEntity):
    """Basic UI component with position and size stuff"""
    cursor = False

    __NULL_VEC2: tp.Final[Vec2] = Vec2()
    __ONE_VEC2: tp.Final[Vec2] = Vec2().from_cartesian(1, 1)

    __data: UIElementData
    __last_data: UIElementData

    __changed_since_last_draw: bool

    __absolute_values: bool

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

        self.__absolute_values = absolute_values

        self.__data = UIElementData()
        self.__last_data = UIElementData()

        self.__data.position_is_relative_to_parent = positon_is_relative_to_parent
        self.__data.size_is_relative_to_parent = size_is_relative_to_parent
        self.__data.placement_anchor = placement_anchor

        if absolute_values:
            self.__data.position.relative_to_parent.xy = convert_coord(self.__absolute_to_relative(position))
            self.__data.size.relative_to_parent.xy = convert_coord(self.__absolute_to_relative(size))
        else:
            self.__data.position.relative_to_parent.xy = convert_coord(position)
            self.__data.size.relative_to_parent.xy = convert_coord(size)

        self.__changed_since_last_draw = True
        self.__calc_values()

    # region Methods: parent size/position
    @property
    def __reference_relative_global_size(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.size_is_relative_to_parent:
            return UIElement.__ONE_VEC2
        return self._next_ui_element_parent.relative_size_global

    @property
    def __reference_absolute_global_size(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.size_is_relative_to_parent:
            return global_vars.resolution
        return self._next_ui_element_parent.absolute_size

    @property
    def __reference_absolute_global_position(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.position_is_relative_to_parent:
            return UIElement.__NULL_VEC2
        return self._next_ui_element_parent.top_left

    @property
    def __reference_relative_global_position(self) -> Vec2:
        if self._next_ui_element_parent is None or not self.__data.position_is_relative_to_parent:
            return UIElement.__NULL_VEC2
        return self._next_ui_element_parent.relative_position_global

    def _update_relative_values(self) -> None:
        self.__data.reference_relative_global_position.xy = self.__reference_relative_global_position.xy
        self.__data.reference_relative_global_size.xy = self.__reference_relative_global_size.xy
        self.__data.reference_absolute_global_position.xy = self.__reference_absolute_global_position.xy  # wichtig
        self.__data.reference_absolute_size.xy = self.__reference_absolute_global_size.xy  # sehr wichtig

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
    def __check_modifications(self) -> None:
        """
        Detects external modifications by comparing data to last_data.
        Calculates relative_position_to_parent and relative_size_to_parent from the changed values.
        """
        return
        # Relative size to parent modified
        if self.__data.relative_size_to_parent.xy != self.__last_data.relative_size_to_parent.xy:
            pass  # This is one of the two from which the whole calculation bases from
        # Relative position to parent modified
        elif self.__data.position_relative_to_parent.xy != self.__last_data.position_relative_to_parent.xy:
            pass  # This is one of the two from which the whole calculation bases from
        # Absolute size modified
        elif self.__data.size_absolute.xy != self.__last_data.size_absolute.xy:
            self.__data.relative_size_to_parent.xy = self.__absolute_to_relative(self.__data.size_absolute)
        # Relative global size modified
        elif self.__data.relative_size_global.xy != self.__last_data.relative_size_global.xy:
            self.__data.relative_size_to_parent.xy = TupleMath.div(
                self.__data.relative_size_global.xy,
                self.__data.reference_relative_global_size.xy
            )
        # absolute width or absolute height modified
        elif self.__data.absolute_width != self.__last_data.absolute_width or self.__data.absolute_height != self.__last_data.absolute_height:
            self.__data.relative_size_to_parent.xy = \
                self.__absolute_to_relative((self.__data.absolute_width, self.__data.absolute_height))

        temp_abs_size = convert_coord(self.__relative_to_absolute(self.__data.relative_size_to_parent), Vec2)

        if self.__data.position_absolute_to_parent.xy != self.__last_data.position_absolute_to_parent.xy:
            self.__data.position_relative_to_parent.xy = \
                self.__absolute_to_relative(self.__data.position_absolute_to_parent)
        if self.__data.position_relative_global.xy != self.__last_data.position_relative_global.xy:
            self.__data.position_relative_to_parent.xy = TupleMath.sub(
                self.__data.position_relative_global.xy,
                self.__reference_relative_global_position.xy
            )
        if self.__data.position_absolute_global.xy != self.__last_data.position_absolute_global.xy:
            abs_pos_to_parent = self.__data.position_absolute_global - self.__reference_absolute_global_position
            self.__data.position_relative_to_parent.xy = self.__absolute_to_relative(abs_pos_to_parent)
        else:
            new_abs_global_xy = None
            half_size = TupleMath.div(temp_abs_size.xy, (2, 2))

            if self.__data.absolute_center_global.xy != self.__last_data.absolute_center_global.xy:
                if self.__data.placement_anchor == "center":
                    new_abs_global_xy = self.__data.absolute_center_global.xy
                elif self.__data.placement_anchor == "nw":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_center_global.xy, half_size)

            elif self.__data.absolute_top_left_global.xy != self.__last_data.absolute_top_left_global.xy:
                if self.__data.placement_anchor == "nw":
                    new_abs_global_xy = self.__data.absolute_top_left_global.xy
                elif self.__data.placement_anchor == "center":
                    new_abs_global_xy = TupleMath.add(self.__data.absolute_top_left_global.xy, half_size)

            elif self.__data.absolute_top_right_global.xy != self.__last_data.absolute_top_right_global.xy:
                if self.__data.placement_anchor == "nw":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_top_right_global.xy, (temp_abs_size.x, 0))
                elif self.__data.placement_anchor == "center":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_top_right_global.xy, (temp_abs_size.x / 2, -temp_abs_size.y / 2))

            elif self.__data.absolute_bottom_left_global.xy != self.__last_data.absolute_bottom_left_global.xy:
                if self.__data.placement_anchor == "nw":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_bottom_left_global.xy, (0, temp_abs_size.y))
                elif self.__data.placement_anchor == "center":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_bottom_left_global.xy, (-temp_abs_size.x / 2, temp_abs_size.y / 2))

            elif self.__data.absolute_bottom_right_global.xy != self.__last_data.absolute_bottom_right_global.xy:
                if self.__data.placement_anchor == "nw":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_bottom_right_global.xy, temp_abs_size.xy)
                elif self.__data.placement_anchor == "center":
                    new_abs_global_xy = TupleMath.sub(self.__data.absolute_bottom_right_global.xy, half_size)

            if new_abs_global_xy is not None:
                abs_pos_to_parent_xy = TupleMath.sub(new_abs_global_xy, self.__reference_absolute_global_position.xy)
                # Reconstruct to Vec2 only right before passing to __absolute_to_relative if it strictly expects a vector
                abs_pos_to_parent = convert_coord(abs_pos_to_parent_xy, Vec2)
                self.__data.position_relative_to_parent.xy = self.__absolute_to_relative(abs_pos_to_parent)

    def __calc_values(self) -> None:
        self._update_relative_values()

        if self.__data == self.__last_data:
            return

        return

        self.__check_modifications()

        self.__data.position_absolute_to_parent.xy = self.__relative_to_absolute(
            self.__data.position_relative_to_parent
        )
        self.__data.size_absolute.xy = self.__relative_to_absolute(
            self.__data.relative_size_to_parent
        )

        self.__data.position_absolute_global.xy = TupleMath.add(
            self.__reference_absolute_global_position.xy,
            self.__data.position_absolute_to_parent.xy
        )

        self.__data.position_relative_global.xy = TupleMath.add(
            self.__reference_relative_global_position.xy,
            self.__data.position_relative_to_parent.xy
        )

        self.__data.relative_size_global.xy = TupleMath.mul(
            self.__data.reference_relative_global_size.xy,
            TupleMath.div(self.__data.size_absolute.xy, global_vars.resolution.xy)
        )

        self.__data.absolute_width = self.__data.size_absolute.x
        self.__data.absolute_height = self.__data.size_absolute.y

        if self.__data.placement_anchor == "nw":
            self.__data.absolute_top_left_global.xy = self.__data.position_absolute_global.xy
            self.__data.absolute_top_right_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                (self.__data.size_absolute.x, 0)
            )
            self.__data.absolute_bottom_left_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                (0, self.__data.size_absolute.y)
            )
            self.__data.absolute_bottom_right_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                self.__data.size_absolute.xy
            )
            self.__data.absolute_center_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                TupleMath.div(self.__data.size_absolute.xy, (2, 2))
            )

        elif self.__data.placement_anchor == "center":
            half_size = TupleMath.div(self.__data.size_absolute.xy, (2, 2))

            self.__data.absolute_top_left_global.xy = TupleMath.sub(
                self.__data.position_absolute_global.xy,
                half_size
            )
            self.__data.absolute_top_right_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                (self.__data.size_absolute.x / 2, -self.__data.size_absolute.y / 2)
            )
            self.__data.absolute_bottom_left_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                (-self.__data.size_absolute.x / 2, self.__data.size_absolute.y / 2)
            )
            self.__data.absolute_bottom_right_global.xy = TupleMath.add(
                self.__data.position_absolute_global.xy,
                half_size
            )

            self.__data.absolute_center_global.xy = self.__data.position_absolute_global.xy

        if not self._ui_changed:
            if self.__data != self.__last_data:
                self._ui_changed = True

        self.__last_data.copy_from(self.__data)

    def _gl_draw(self) -> None:
        """
        The draw function called in loop

        It should always follow this structure:
        - Compare if anything changed, requiring redrawing of the collision surface/mask
        - Call super()._gl_draw()
        - Draw the UI and collision surface
        """
        self.__calc_values()

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
    def width(self) -> float:
        """:return: Absolute width"""
        self.__calc_values()
        return self.__data.absolute_width

    @width.setter
    def width(self, value: float) -> None:
        """:param value: Absolute width"""
        self.__calc_values()
        self.__data.absolute_width = float(value)

    def __calc_height_absolute(self) -> None:
        ...

    def __calc_height_relative_global(self) -> None:
        ...

    def __calc_height_relative_to_parent(self) -> None:
        ...

    @property
    def height(self) -> UIElementValueFloatOneAbsolute:
        """:return: Absolute height"""
        self.__calc_values()
        return self.__data.height

    # @height.setter
    # def height(self, value: float) -> None:
    #     """:param value: Absolute height"""
    #     self.__calc_values()
    #     self.__data.absolute_height = float(value)

    @property
    def position(self) -> UIElementValueVec2:
        self.__calc_values()
        return self.__data.position

    @position.setter
    def position(self, value: coord_t) -> None:
        if self.__absolute_values:
            self.__data.position.absolute_to_parent = value
        else:
            self.__data.position.relative_to_parent = value

    # @property
    # def relative_position_to_parent(self) -> Vec2:
    #     """:return: Relative position to parent"""
    #     self.__calc_values()
    #     return self.__data.position_relative_to_parent
    #
    # @relative_position_to_parent.setter
    # def relative_position_to_parent(self, value: coord_t) -> None:
    #     """:param value: Relative position to parent"""
    #     self.__calc_values()
    #     self.__data.position_relative_to_parent.xy = convert_coord(value)
    #
    # @property
    # def absolute_position_to_parent(self) -> Vec2:
    #     """:return: Absolute position to parent"""
    #     self.__calc_values()
    #     return self.__data.position_absolute_to_parent
    #
    # @absolute_position_to_parent.setter
    # def absolute_position_to_parent(self, value: coord_t) -> None:
    #     """:param value: Absolute position to parent"""
    #     self.__calc_values()
    #     self.__data.position_absolute_to_parent.xy = convert_coord(value)

    @property
    def relative_size_to_parent(self) -> Vec2:
        """:return: Relative size to parent"""
        self.__calc_values()
        return self.__data.relative_size_to_parent

    @relative_size_to_parent.setter
    def relative_size_to_parent(self, value: coord_t) -> None:
        """:param value: Relative size to parent"""
        self.__calc_values()
        self.__data.relative_size_to_parent.xy = convert_coord(value)

    # @property
    # def relative_position_global(self) -> Vec2:
    #     """:return: Relative global position"""
    #     self.__calc_values()
    #     return self.__data.position_relative_global
    #
    # @relative_position_global.setter
    # def relative_position_global(self, value: coord_t) -> None:
    #     """:param value: Relative global position"""
    #     self.__calc_values()
    #     self.__data.position_relative_global.xy = convert_coord(value)
    #
    # @property
    # def absolute_position_global(self) -> Vec2:
    #     """:return: Absolute global position"""
    #     self.__calc_values()
    #     return self.__data.position_absolute_global
    #
    # @absolute_position_global.setter
    # def absolute_position_global(self, value: coord_t) -> None:
    #     """:param value: Absolute global position"""
    #     self.__calc_values()
    #     self.__data.position_absolute_global.xy = convert_coord(value)

    @property
    def relative_size_global(self) -> Vec2:
        """:return: Relative global size"""
        self.__calc_values()
        return self.__data.relative_size_global

    @relative_size_global.setter
    def relative_size_global(self, value: coord_t) -> None:
        """:param value: Relative global size"""
        self.__calc_values()
        self.__data.relative_size_global.xy = convert_coord(value)

    @property
    def absolute_size(self) -> Vec2:
        """:return: Absolute size"""
        self.__calc_values()
        return self.__data.size_absolute

    @absolute_size.setter
    def absolute_size(self, value: coord_t) -> None:
        """:param value: Absolute size"""
        self.__calc_values()
        self.__data.size_absolute.xy = convert_coord(value)

    @property
    def center(self) -> Vec2:
        """:return: Absolute center"""
        self.__calc_values()
        return self.__data.absolute_center_global

    @center.setter
    def center(self, value: coord_t) -> None:
        """:param value: Absolute center"""
        self.__calc_values()
        self.__data.absolute_center_global.xy = convert_coord(value)

    @property
    def top_left(self) -> Vec2:
        """:return: Absolute top left"""
        self.__calc_values()
        return self.__data.absolute_top_left_global

    @top_left.setter
    def top_left(self, value: coord_t) -> None:
        """:param value: Absolute top left"""
        self.__calc_values()
        self.__data.absolute_top_left_global.xy = convert_coord(value)

    @property
    def top_right(self) -> Vec2:
        """:return: Absolute top right"""
        self.__calc_values()
        return self.__data.absolute_top_right_global

    @top_right.setter
    def top_right(self, value: coord_t) -> None:
        """:param value: Absolute top right"""
        self.__calc_values()
        self.__data.absolute_top_right_global.xy = convert_coord(value)

    @property
    def bottom_left(self) -> Vec2:
        """:return: Absolute bottom left"""
        self.__calc_values()
        return self.__data.absolute_bottom_left_global

    @bottom_left.setter
    def bottom_left(self, value: coord_t) -> None:
        """:param value: Absolute bottom left"""
        self.__calc_values()
        self.__data.absolute_bottom_left_global.xy = convert_coord(value)

    @property
    def bottom_right(self) -> Vec2:
        """:return: Absolute bottom right"""
        self.__calc_values()
        return self.__data.absolute_bottom_right_global

    @bottom_right.setter
    def bottom_right(self, value: coord_t) -> None:
        """:param value: Absolute bottom right"""
        self.__calc_values()
        self.__data.absolute_bottom_right_global.xy = convert_coord(value)

    # endregion
