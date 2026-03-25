"""
amoginarium/ui/_base/_ui_element/_ui_element_values.py

Project: amoginarium
Created: 25.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

from enum import Enum
import typing as tp

from amoginarium.logic import Vec2, coord_t, convert_coord

from ..._types import Anchor, Positions


# region ValuesEnums
class UIElementValueNamesEnum(Enum):
    """The different UIElementData values"""
    NONE = 0
    PLACEMENT_ANCHOR = 1
    POSITION = 2
    SIZE = 3
    WIDTH = 4
    HEIGHT = 5
    CENTER = 6
    TOP_LEFT = 7
    TOP_RIGHT = 8
    BOTTOM_LEFT = 9
    BOTTOM_RIGHT = 10
    POSITION_IS_RELATIVE_TO_PARENT = 11
    SIZE_IS_RELATIVE_TO_PARENT = 12
    REFERENCE_POSITION = 13
    REFERENCE_SIZE = 14
    PARENT_REFERENCE_POSITION = 15


class UIElementValueTypesEnum(Enum):
    """The different subtypes of the Float/Vec2 values"""
    NONE = 0
    ABSOLUTE = 1
    ABSOLUTE_GLOBAL = 2
    ABSOLUTE_TO_PARENT = 3
    RELATIVE_GLOBAL = 4
    RELATIVE_TO_PARENT = 5


# endregion

# region FloatValue
class _UIElementValueFloatBase:
    """
    Base class containing the shared relative float metrics.
    """
    _value_name: UIElementValueNamesEnum
    __relative_global: float
    __relative_to_parent: float

    def __init__(self, value_name: UIElementValueNamesEnum) -> None:
        """
        Initializes the base relative float values.
        :param value_name: The identifier for this specific UI value
        """
        self._value_name = value_name
        self.__relative_global = 0.0
        self.__relative_to_parent = 0.0

    @property
    def relative_global(self) -> float:
        """
        :return: Relative global value
        """
        return self.__relative_global

    @relative_global.setter
    def relative_global(self, value: float) -> None:
        """
        :param value: Relative global value
        """
        self.__relative_global = value

    @property
    def relative_to_parent(self) -> float:
        """
        :return: Relative to parent value
        """
        return self.__relative_to_parent

    @relative_to_parent.setter
    def relative_to_parent(self, value: float) -> None:
        """
        :param value: Relative to parent value
        """
        self.__relative_to_parent = value

    def copy_from(self, other: _UIElementValueFloatBase) -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        self.relative_global = other.relative_global
        self.relative_to_parent = other.relative_to_parent

    def not_equal(self, other: _UIElementValueFloatBase
                  ) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        if self.relative_global != other.relative_global:
            return True, self._value_name, UIElementValueTypesEnum.RELATIVE_GLOBAL
        if self.relative_to_parent != other.relative_to_parent:
            return True, self._value_name, UIElementValueTypesEnum.RELATIVE_TO_PARENT
        return False, self._value_name, UIElementValueTypesEnum.NONE

    def __ne__(self, other: '_UIElementValueFloatBase') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        return self.not_equal(other)[0]

    def __eq__(self, other: '_UIElementValueFloatBase') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are equal
        """
        return not self.__ne__(other)


class UIElementValueFloat(_UIElementValueFloatBase):
    """
    Absolute/Relative and global/to parent metrics for a single float value.
    """
    __absolute_global: float
    __absolute_to_parent: float

    def __init__(self, value_name: UIElementValueNamesEnum) -> None:
        """
        Initializes the float values.
        :param value_name: The identifier for this specific UI value
        """
        super().__init__(value_name)
        self.__absolute_global = 0.0
        self.__absolute_to_parent = 0.0

    @property
    def absolute_global(self) -> float:
        """
        :return: Absolute global value
        """
        return self.__absolute_global

    @absolute_global.setter
    def absolute_global(self, value: float) -> None:
        """
        :param value: Absolute global value
        """
        self.__absolute_global = value

    @property
    def absolute_to_parent(self) -> float:
        """
        :return: Absolute to parent value
        """
        return self.__absolute_to_parent

    @absolute_to_parent.setter
    def absolute_to_parent(self, value: float) -> None:
        """
        :param value: Absolute to parent value
        """
        self.__absolute_to_parent = value

    def copy_from(self, other: 'UIElementValueFloat') -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        super().copy_from(other)
        self.absolute_global = other.absolute_global
        self.absolute_to_parent = other.absolute_to_parent

    def not_equal(self, other: UIElementValueFloat) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        is_neq, val_name, val_type = super().not_equal(other)
        if is_neq:
            return True, val_name, val_type

        if self.absolute_global != other.absolute_global:
            return True, self._value_name, UIElementValueTypesEnum.ABSOLUTE_GLOBAL
        if self.absolute_to_parent != other.absolute_to_parent:
            return True, self._value_name, UIElementValueTypesEnum.ABSOLUTE_TO_PARENT

        return False, self._value_name, UIElementValueTypesEnum.NONE

    def __ne__(self, other: UIElementValueFloat) -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        return self.not_equal(other)[0]


class UIElementValueFloatOneAbsolute(_UIElementValueFloatBase):
    """
    Float value representation containing a single absolute value alongside relative metrics.
    """
    __absolute: float

    def __init__(self, value_name: UIElementValueNamesEnum) -> None:
        """
        Initializes the float values.
        :param value_name: The identifier for this specific UI value
        """
        super().__init__(value_name)
        self.__absolute = 0.0

    @property
    def absolute(self) -> float:
        """
        :return: Absolute value
        """
        return self.__absolute

    @absolute.setter
    def absolute(self, value: float) -> None:
        """
        :param value: Absolute value
        """
        self.__absolute = value

    def copy_from(self, other: UIElementValueFloatOneAbsolute) -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        super().copy_from(other)
        self.absolute = other.absolute

    def not_equal(self, other: UIElementValueFloatOneAbsolute
                  ) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        is_neq, val_name, val_type = super().not_equal(other)
        if is_neq:
            return True, val_name, val_type

        if self.absolute != other.absolute:
            return True, self._value_name, UIElementValueTypesEnum.ABSOLUTE

        return False, self._value_name, UIElementValueTypesEnum.NONE

    def __ne__(self, other: 'UIElementValueFloatOneAbsolute') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        return self.not_equal(other)[0]


# endregion

# region Vec2Value
class _UIElementValueVec2Base:
    """
    Base class containing the shared relative Vec2 metrics.
    """
    _value_name: UIElementValueNamesEnum
    __relative_global: Vec2
    __relative_to_parent: Vec2

    def __init__(self, value_name: UIElementValueNamesEnum) -> None:
        """
        Initializes the base relative vector values.
        :param value_name: The identifier for this specific UI value
        """
        self._value_name = value_name
        self.__relative_global = Vec2()
        self.__relative_to_parent = Vec2()

    @property
    def relative_global(self) -> Vec2:
        """
        :return: Relative global vector
        """
        return self.__relative_global

    @relative_global.setter
    def relative_global(self, value: coord_t) -> None:
        """
        :param value: Relative global vector
        """
        self.__relative_global.xy = convert_coord(value)

    @property
    def relative_to_parent(self) -> Vec2:
        """
        :return: Relative to parent vector
        """
        return self.__relative_to_parent

    @relative_to_parent.setter
    def relative_to_parent(self, value: coord_t) -> None:
        """
        :param value: Relative to parent vector
        """
        self.__relative_to_parent.xy = convert_coord(value)

    def copy_from(self, other: '_UIElementValueVec2Base') -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        self.relative_global = other.relative_global.xy
        self.relative_to_parent = other.relative_to_parent.xy

    def not_equal(self, other: '_UIElementValueVec2Base'
                  ) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        if self.relative_global.xy != other.relative_global.xy:
            return True, self._value_name, UIElementValueTypesEnum.RELATIVE_GLOBAL
        if self.relative_to_parent.xy != other.relative_to_parent.xy:
            return True, self._value_name, UIElementValueTypesEnum.RELATIVE_TO_PARENT
        return False, self._value_name, UIElementValueTypesEnum.NONE

    def __ne__(self, other: '_UIElementValueVec2Base') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        return self.not_equal(other)[0]

    def __eq__(self, other: '_UIElementValueVec2Base') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are equal
        """
        return not self.__ne__(other)


class UIElementValueVec2(_UIElementValueVec2Base):
    """
    Absolute/Relative and global/to parent of a Vec2 value crossed.
    """
    __absolute_global: Vec2
    __absolute_to_parent: Vec2

    def __init__(self, value_name: UIElementValueNamesEnum) -> None:
        """
        Initializes the vector values.
        :param value_name: The identifier for this specific UI value
        """
        super().__init__(value_name)
        self.__absolute_global = Vec2()
        self.__absolute_to_parent = Vec2()

    @property
    def absolute_global(self) -> Vec2:
        """
        :return: Absolute global vector
        """
        return self.__absolute_global

    @absolute_global.setter
    def absolute_global(self, value: coord_t) -> None:
        """
        :param value: Absolute global vector
        """
        self.__absolute_global.xy = convert_coord(value)

    @property
    def absolute_to_parent(self) -> Vec2:
        """
        :return: Absolute to parent vector
        """
        return self.__absolute_to_parent

    @absolute_to_parent.setter
    def absolute_to_parent(self, value: coord_t) -> None:
        """
        :param value: Absolute to parent vector
        """
        self.__absolute_to_parent.xy = convert_coord(value)

    def copy_from(self, other: 'UIElementValueVec2') -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        super().copy_from(other)
        self.absolute_global = other.absolute_global.xy
        self.absolute_to_parent = other.absolute_to_parent.xy

    def not_equal(self, other: 'UIElementValueVec2'
                  ) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        is_neq, val_name, val_type = super().not_equal(other)
        if is_neq:
            return True, val_name, val_type

        if self.absolute_global.xy != other.absolute_global.xy:
            return True, self._value_name, UIElementValueTypesEnum.ABSOLUTE_GLOBAL
        if self.absolute_to_parent.xy != other.absolute_to_parent.xy:
            return True, self._value_name, UIElementValueTypesEnum.ABSOLUTE_TO_PARENT

        return False, self._value_name, UIElementValueTypesEnum.NONE

    def __ne__(self, other: 'UIElementValueVec2') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        return self.not_equal(other)[0]


class UIElementValueVec2OneAbsolute(_UIElementValueVec2Base):
    """
    Vec2 value representation containing a single absolute value alongside relative metrics.
    """
    __absolute: Vec2

    def __init__(self, value_name: UIElementValueNamesEnum) -> None:
        """
        Initializes the vector values.
        :param value_name: The identifier for this specific UI value
        """
        super().__init__(value_name)
        self.__absolute = Vec2()

    @property
    def absolute(self) -> Vec2:
        """
        :return: Absolute vector
        """
        return self.__absolute

    @absolute.setter
    def absolute(self, value: coord_t) -> None:
        """
        :param value: Absolute vector
        """
        self.__absolute.xy = convert_coord(value)

    def copy_from(self, other: 'UIElementValueVec2OneAbsolute') -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        super().copy_from(other)
        self.absolute = other.absolute.xy

    def not_equal(self, other: 'UIElementValueVec2OneAbsolute'
                  ) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        is_neq, val_name, val_type = super().not_equal(other)
        if is_neq:
            return True, val_name, val_type

        if self.absolute.xy != other.absolute.xy:
            return True, self._value_name, UIElementValueTypesEnum.ABSOLUTE

        return False, self._value_name, UIElementValueTypesEnum.NONE

    def __ne__(self, other: 'UIElementValueVec2OneAbsolute') -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        return self.not_equal(other)[0]


# endregion

# region UIElementData
# noinspection DuplicatedCode
class UIElementData:
    """
    Position data for UIElement that can all influence each other
    """
    placement_anchor: Anchor

    position: tp.Final[UIElementValueVec2]
    size: tp.Final[UIElementValueVec2OneAbsolute]

    width: tp.Final[UIElementValueFloatOneAbsolute]
    height: tp.Final[UIElementValueFloatOneAbsolute]
    center: tp.Final[UIElementValueVec2]
    top_left: tp.Final[UIElementValueVec2]
    top_right: tp.Final[UIElementValueVec2]
    bottom_left: tp.Final[UIElementValueVec2]
    bottom_right: tp.Final[UIElementValueVec2]

    position_is_relative_to_parent: bool
    size_is_relative_to_parent: bool
    parent_reference_position: Positions

    reference_position: tp.Final[UIElementValueVec2]
    reference_size: tp.Final[UIElementValueVec2OneAbsolute]
    reference_size_for_position: tp.Final[UIElementValueVec2OneAbsolute]

    def __init__(self) -> None:
        """
        Initializes the UIElementData with default values and instantiates all wrappers.
        """
        self.placement_anchor = Anchor.CENTER
        self.parent_reference_position = Positions.TOP_LEFT
        self.position = UIElementValueVec2(UIElementValueNamesEnum.POSITION)
        self.size = UIElementValueVec2OneAbsolute(UIElementValueNamesEnum.SIZE)

        self.width = UIElementValueFloatOneAbsolute(UIElementValueNamesEnum.WIDTH)
        self.height = UIElementValueFloatOneAbsolute(UIElementValueNamesEnum.HEIGHT)
        self.center = UIElementValueVec2(UIElementValueNamesEnum.CENTER)
        self.top_left = UIElementValueVec2(UIElementValueNamesEnum.TOP_LEFT)
        self.top_right = UIElementValueVec2(UIElementValueNamesEnum.TOP_RIGHT)
        self.bottom_left = UIElementValueVec2(UIElementValueNamesEnum.BOTTOM_LEFT)
        self.bottom_right = UIElementValueVec2(UIElementValueNamesEnum.BOTTOM_RIGHT)

        self.position_is_relative_to_parent = True
        self.size_is_relative_to_parent = True

        self.reference_position = UIElementValueVec2(UIElementValueNamesEnum.REFERENCE_POSITION)
        self.reference_size = UIElementValueVec2OneAbsolute(UIElementValueNamesEnum.REFERENCE_SIZE)
        self.reference_size_for_position = UIElementValueVec2OneAbsolute(UIElementValueNamesEnum.REFERENCE_SIZE)

    def copy_from(self, other: UIElementData) -> None:
        """
        Updates this instance with values from another in-place.
        :param other: The instance to copy values from
        """
        self.placement_anchor = other.placement_anchor
        self.position_is_relative_to_parent = other.position_is_relative_to_parent
        self.size_is_relative_to_parent = other.size_is_relative_to_parent
        self.parent_reference_position = other.parent_reference_position

        self.reference_position.copy_from(other.reference_position)
        self.reference_size.copy_from(other.reference_size)
        self.reference_size_for_position.copy_from(other.reference_size_for_position)

        self.position.copy_from(other.position)
        self.size.copy_from(other.size)

        self.width.copy_from(other.width)
        self.height.copy_from(other.height)
        self.center.copy_from(other.center)
        self.top_left.copy_from(other.top_left)
        self.top_right.copy_from(other.top_right)
        self.bottom_left.copy_from(other.bottom_left)
        self.bottom_right.copy_from(other.bottom_right)

    def not_equal(self, other: object) -> tp.Tuple[bool, UIElementValueNamesEnum, UIElementValueTypesEnum]:
        """
        Checks for inequality and identifies which specific attribute differs.
        :param other: The instance to compare against
        :return: Tuple containing a boolean if not equal, the value name, and the specific value type
        """
        if not isinstance(other, UIElementData):
            return True, UIElementValueNamesEnum.NONE, UIElementValueTypesEnum.NONE

        if self.placement_anchor != other.placement_anchor:
            return True, UIElementValueNamesEnum.PLACEMENT_ANCHOR, UIElementValueTypesEnum.NONE

        if self.position_is_relative_to_parent != other.position_is_relative_to_parent:
            return True, UIElementValueNamesEnum.POSITION_IS_RELATIVE_TO_PARENT, UIElementValueTypesEnum.NONE

        if self.size_is_relative_to_parent != other.size_is_relative_to_parent:
            return True, UIElementValueNamesEnum.SIZE_IS_RELATIVE_TO_PARENT, UIElementValueTypesEnum.NONE

        if self.parent_reference_position != other.parent_reference_position:
            return True, UIElementValueNamesEnum.PARENT_REFERENCE_POSITION, UIElementValueTypesEnum.NONE

        is_neq, val_name, val_type = self.position.not_equal(other.position)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.size.not_equal(other.size)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.width.not_equal(other.width)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.height.not_equal(other.height)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.center.not_equal(other.center)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.top_left.not_equal(other.top_left)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.top_right.not_equal(other.top_right)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.bottom_left.not_equal(other.bottom_left)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.bottom_right.not_equal(other.bottom_right)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.reference_position.not_equal(other.reference_position)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.reference_size.not_equal(other.reference_size)
        if is_neq:
            return True, val_name, val_type

        is_neq, val_name, val_type = self.reference_size_for_position.not_equal(other.reference_size_for_position)
        if is_neq:
            return True, val_name, val_type

        return False, UIElementValueNamesEnum.NONE, UIElementValueTypesEnum.NONE

    def __ne__(self, other: object) -> bool:
        """
        Explicitly compares all values to guarantee detection of changes.
        :param other: The instance to compare against
        :return: Whether the instances are not equal
        """
        if not isinstance(other, UIElementData):
            return NotImplemented

        return self.not_equal(other)[0]

    def __eq__(self, other: object) -> bool:
        """
        :param other: The instance to compare against
        :return: Whether the instances are equal
        """
        result = self.__ne__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

# endregion
