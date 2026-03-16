"""
amoginarium/ui/_animations/_color_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.logic import Color, convert_color

from ._animation_types import anim_color_t, anim_color__time_t, AnimatedColorValues, anim_color_values_t
from ._multi_animation import MultiAnimation


class ColorAnimation(MultiAnimation[tuple[float, float, float, float]]):
    """RGBA float animation for Color"""
    __color: Color

    def __init__(self, value: anim_color_values_t) -> None:
        """
        Create a Color animation
        :param value: Color animation values
        """
        val = self.__convert_anim_color_values(value)

        super().__init__(
            start_values=self.__convert_color_to_tuple(val.start_value),
            end_values=self.__convert_color_to_tuple(val.end_value),
            extend_durations_in_seconds=self.__convert_time(val.extend_duration_seconds),
            collapse_duration_in_seconds=self.__convert_time(val.collapse_duration_seconds),
            count=4
        )

        # Initialize the stored Color object using the current values calculated by MultiAnimation
        self.__color = convert_color(super().current_value, convert_to=Color)

    def update(self, delta: float) -> Color:
        """
        Update the animations
        :param delta: Time since the last update in seconds
        :return: New values of the animations
        """
        current_rgba = super().update(delta)
        # Update the color object with the new RGBA float tuple (assuming convert_to=Color handles 0.0-1.0 scale floats)
        self.__color = convert_color(current_rgba, convert_to=Color)
        return self.__color

    @property
    def current_value(self) -> Color:
        """:return: Current values of the animations"""
        return self.__color

    @staticmethod
    def __convert_color_to_tuple(color_val: anim_color_t | None) -> tuple[float, float, float, float] | None:
        """
        Converts a Color or a tuple to a tuple of 4 floats (RGBA).
        """
        if color_val is None:
            return None

        # Let the external convert_color function handle scaling to 0.0 - 1.0 format
        converted = tuple(convert_color(color_val, convert_to=tuple))

        # Pad with alpha=1.0 if it's an RGB 3-tuple
        if len(converted) == 3:
            return float(converted[0]), float(converted[1]), float(converted[2]), 1.0

        return float(converted[0]), float(converted[1]), float(converted[2]), float(converted[3])

    @staticmethod
    def __convert_time(time_val: anim_color__time_t | None) -> tuple[float, float, float, float] | float | None:
        """
        Normalizes time inputs. Passes scalars directly to MultiAnimation,
        or converts 4-tuples to floats.
        """
        if time_val is None:
            return None

        if isinstance(time_val, (int, float)):
            return float(time_val)

        if isinstance(time_val, tuple) and len(time_val) == 4:
            return float(time_val[0]), float(time_val[1]), float(time_val[2]), float(time_val[3])

        raise ValueError(f"Unsupported time format for ColorAnimation: {time_val}")

    @staticmethod
    def __is_single_color(val: tp.Any) -> bool:
        """Helper to check if a value is a single color."""
        # Duck-typing for a Color object
        if hasattr(val, "get_rgba1") or type(val).__name__ == "Color":
            return True

        # Treat a tuple of 3 or 4 numbers as a single color (not a tuple of start/end)
        if isinstance(val, tuple) and len(val) in (3, 4):
            if all(isinstance(v, (int, float)) for v in val):
                return True

        return False

    @classmethod
    def __convert_anim_color_values(cls, values: anim_color_values_t) -> AnimatedColorValues:
        """
        Parses union types into the AnimatedColorValues dataclass,
        normalizing all color inputs.
        """
        if isinstance(values, AnimatedColorValues):
            return values

        zero_val = 0.0  # For durations, we can pass a single float scalar directly to MultiAnimation

        # 1. Handle single color
        if cls.__is_single_color(values):
            return AnimatedColorValues(
                start_value=values,
                end_value=values,
                extend_duration_seconds=zero_val,
                collapse_duration_seconds=zero_val
            )

        # 2. Handle tuples representing (start, end, extend_dur, collapse_dur)
        if isinstance(values, tuple):
            length = len(values)

            if length == 2:
                return AnimatedColorValues(
                    start_value=values[0],
                    end_value=values[1],
                    extend_duration_seconds=zero_val,
                    collapse_duration_seconds=zero_val
                )

            elif length == 3:
                return AnimatedColorValues(
                    start_value=values[0],
                    end_value=values[1],
                    extend_duration_seconds=values[2],  # Passes anim_color__time_t
                    collapse_duration_seconds=values[2]
                )

            elif length == 4:
                return AnimatedColorValues(
                    start_value=values[0],
                    end_value=values[1],
                    extend_duration_seconds=values[2],
                    collapse_duration_seconds=values[3]
                )

        raise ValueError(f"Unsupported conversion format: {values}")
