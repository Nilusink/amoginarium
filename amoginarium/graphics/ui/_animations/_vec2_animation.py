"""
amoginarium/ui/_animations/_vec2_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from types import EllipsisType

from amoginarium.shared.utility import Vec2

from ._animation_types import AnimatedVec2Values, anim_vec2_values_t, anim_vec2_t, anim_input_t
from ._multi_animation import MultiAnimation


class Vec2Animation(MultiAnimation):
    """Double float animation for Vec2"""
    __vec2: Vec2
    __delta_vec2: Vec2

    def __init__(self, value: anim_vec2_values_t) -> None:
        """
        Create a Vec2 animation
        :param value: Vec2 animation values
        """
        parsed_value = self.__convert_anim_vec2_values(value)

        super().__init__(
            start_values=self.__convert_up_to_coord(parsed_value.start_vec),
            end_values=self.__convert_up_to_coord(parsed_value.end_vec),
            extend_durations=self.__convert_up_to_coord(parsed_value.extend_duration),
            collapse_durations=self.__convert_up_to_coord(parsed_value.collapse_duration),
            extend_debounce_duration=self.__convert_up_to_coord(parsed_value.extend_debounce_duration),
            collapse_debounce_duration=self.__convert_up_to_coord(parsed_value.collapse_debounce_duration),
            extend_curve=parsed_value.extend_curve,
            collapse_curve=parsed_value.collapse_curve,
            count=2
        )

        self.__vec2 = Vec2()
        self.__delta_vec2 = Vec2()

        # Pull current values from MultiAnimation to initialize the vector
        current = super().current_value
        self.__vec2.xy = current if current else (0.0, 0.0)

    def update(self, delta: float) -> Vec2:
        """
        Update the animations
        :param delta: Time since the last update in seconds
        :return: Value difference between current and last value
        """
        self.__delta_vec2.xy = super().update(delta)
        self.__vec2.xy = super().current_value
        return self.__delta_vec2

    def reset(self) -> None:
        super().reset()
        self.__vec2.xy = super().current_value

    @property
    def current_value(self) -> Vec2:
        """:return: Current values of the animations"""
        return self.__vec2

    @staticmethod
    def __convert_up_to_coord(val: anim_vec2_t | anim_input_t | EllipsisType) -> anim_input_t | EllipsisType:
        """
        Converts a Vec2 or a coordinate tuple to a tuple of floats.
        Passes single scalars, sequences, and Ellipsis (...) through.
        """
        if val is ... or val is None:
            return ...

        if isinstance(val, (int, float)):
            return float(val)

        if isinstance(val, tuple) and len(val) == 2:
            # Check if it's explicitly a numeric coordinate tuple
            if isinstance(val[0], (int, float)) and isinstance(val[1], (int, float)):
                return float(val[0]), float(val[1])

        # Duck-typing check for Vec2
        if hasattr(val, "xy"):
            return float(val.xy[0]), float(val.xy[1])

        # Fallback for other valid sequences that MultiAnimation will pad
        return val

    @staticmethod
    def __is_single_coordinate(val: anim_vec2_values_t) -> bool:
        """Helper to check if a value is a single vector or a scalar."""
        if isinstance(val, (int, float)):
            return True
        if hasattr(val, "xy"):  # catches Vec2
            return True
        # Treat a tuple of two numbers like (10, 20) as a single X,Y coordinate
        if isinstance(val, tuple) and len(val) == 2:
            if isinstance(val[0], (int, float)) and isinstance(val[1], (int, float)):
                return True
        return False

    @classmethod
    def __convert_anim_vec2_values(cls, values: anim_vec2_values_t) -> AnimatedVec2Values:
        """
        Parses union types into the AnimatedVec2Values dataclass.
        Relies on default '...' values handling in down-stream logic.
        """
        if isinstance(values, AnimatedVec2Values):
            return values

        # 1. Handle single coord_t, float, or int
        if cls.__is_single_coordinate(values):
            return AnimatedVec2Values(start_vec=values)

        # 2. Handle tuples representing the parameters sequentially
        if isinstance(values, tuple):
            length = len(values)

            if 2 <= length <= 8:
                return AnimatedVec2Values(
                    start_vec=values[0],
                    end_vec=values[1],
                    extend_duration=values[2] if length > 2 else ...,
                    collapse_duration=values[3] if length > 3 else ...,
                    extend_debounce_duration=values[4] if length > 4 else ...,
                    collapse_debounce_duration=values[5] if length > 5 else ...,
                    extend_curve=values[6] if length > 6 else ...,
                    collapse_curve=values[7] if length > 7 else ...
                )

        raise ValueError(f"Unsupported conversion format: {values}")
