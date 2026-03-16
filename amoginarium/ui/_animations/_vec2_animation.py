"""
amoginarium/ui/_animations/_vec2_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.logic import Vec2

from ._animation_types import anim_vec2_t, AnimatedVec2Values, anim_vec2_values_t
from ._multi_animation import MultiAnimation


class Vec2Animation(MultiAnimation[tuple[float, float]]):
    """Double float animation for Vec2"""
    __vec2: Vec2

    def __init__(self, value: anim_vec2_values_t) -> None:
        """
        Create a Vec2 animation
        :param value: Vec2 animation values
        """
        value = self.__convert_anim_vec2_values(value)

        super().__init__(
            start_values=self.__convert_up_to_coord(value.start_vec),
            end_values=self.__convert_up_to_coord(value.end_vec),
            extend_durations_in_seconds=self.__convert_up_to_coord(value.extend_duration_seconds),
            collapse_duration_in_seconds=self.__convert_up_to_coord(value.collapse_duration_seconds),
            count=2
        )

        self.__vec2 = Vec2()
        self.__vec2.xy = super().current_value

    def update(self, delta: float) -> Vec2:
        """
        Update the animations
        :param delta: Time since the last update in seconds
        :return: New values of the animations
        """
        self.__vec2.xy = super().update(delta)
        return self.__vec2

    @property
    def current_value(self) -> Vec2:
        """:return: Current values of the animations"""
        return self.__vec2

    @staticmethod
    def __convert_up_to_coord(coord: anim_vec2_t) -> tuple[float, float] | float:
        """
        Converts a Vec2 or a coordinate tuple to a tuple of floats.
        Passes single int or float values through as-is.
        """
        if isinstance(coord, (int, float)):
            return coord

        if isinstance(coord, tuple) and len(coord) == 2:
            return float(coord[0]), float(coord[1])

        # Duck-typing check for Vec2
        if hasattr(coord, "xy"):
            return float(coord.xy[0]), float(coord.xy[1])

        raise ValueError(f"Unsupported coordinate format: {coord}")

    @staticmethod
    def __is_single_coordinate(val: tp.Any) -> bool:
        """Helper to check if a value is a single vector or a scalar."""
        if isinstance(val, (int, float)):
            return True
        if hasattr(val, "xy"):  # catches Vec2
            return True
        # Treat a tuple of two numbers like (10, 20) as a single X,Y coordinate,
        # NOT as start=10, end=20.
        if isinstance(val, tuple) and len(val) == 2:
            if isinstance(val[0], (int, float)) and isinstance(val[1], (int, float)):
                return True
        return False

    @classmethod
    def __convert_anim_vec2_values(cls, values: anim_vec2_values_t) -> AnimatedVec2Values:
        """
        Parses union types into the AnimatedVec2Values dataclass,
        normalizing all vector inputs to tuples of floats or single numeric values.
        """
        if isinstance(values, AnimatedVec2Values):
            return values

        zero_val = (0.0, 0.0)

        # 1. Handle single coord_t, float, or int
        if cls.__is_single_coordinate(values):
            norm_val = cls.__convert_up_to_coord(values)
            return AnimatedVec2Values(
                start_vec=norm_val,
                end_vec=norm_val,
                extend_duration_seconds=zero_val,
                collapse_duration_seconds=zero_val
            )

        # 2. Handle tuples representing (start, end, extend_dur, collapse_dur)
        if isinstance(values, tuple):
            length = len(values)

            if length == 2:
                return AnimatedVec2Values(
                    start_vec=cls.__convert_up_to_coord(values[0]),
                    end_vec=cls.__convert_up_to_coord(values[1]),
                    extend_duration_seconds=zero_val,
                    collapse_duration_seconds=zero_val
                )

            elif length == 3:
                return AnimatedVec2Values(
                    start_vec=cls.__convert_up_to_coord(values[0]),
                    end_vec=cls.__convert_up_to_coord(values[1]),
                    extend_duration_seconds=cls.__convert_up_to_coord(values[2]),
                    collapse_duration_seconds=cls.__convert_up_to_coord(values[2])
                )

            elif length == 4:
                return AnimatedVec2Values(
                    start_vec=cls.__convert_up_to_coord(values[0]),
                    end_vec=cls.__convert_up_to_coord(values[1]),
                    extend_duration_seconds=cls.__convert_up_to_coord(values[2]),
                    collapse_duration_seconds=cls.__convert_up_to_coord(values[3])
                )

        raise ValueError(f"Unsupported conversion format: {values}")
