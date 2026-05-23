"""
Provides RGBA color transitions using multichannel animation logic.

| Path: amoginarium/graphics/ui/_animations/_color_animation.py
| Project: amoginarium
| Created: 16.03.2026
| Authors: LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amoginarium.shared.utility import Color, convert_color

from ._animation_types import AnimatedColorValues
from ._multi_animation import MultiAnimation

if TYPE_CHECKING:
    from types import EllipsisType

    from ._animation_types import anim_color_t, anim_color_time_t
    from ._animation_types import anim_color_values_t, anim_input_t


class ColorAnimation(MultiAnimation):
    """RGBA float animation for Color."""

    __color: Color

    def __init__(self, value: anim_color_values_t) -> None:
        """
        Create a Color animation
        :param value: Color animation values.
        """
        parsed_value = self.__convert_anim_color_values(value)

        super().__init__(
            start_values=self.__convert_color_to_tuple(parsed_value.start_value),
            end_values=self.__convert_color_to_tuple(parsed_value.end_value),
            extend_durations=self.__convert_time(parsed_value.extend_duration),
            collapse_durations=self.__convert_time(parsed_value.collapse_duration),
            extend_debounce_duration=self.__convert_time(
                parsed_value.extend_debounce_duration
            ),
            collapse_debounce_duration=self.__convert_time(
                parsed_value.collapse_debounce_duration
            ),
            extend_curve=parsed_value.extend_curve,
            collapse_curve=parsed_value.collapse_curve,
            count=4,
        )

        # Initialize the stored Color object using the current values calculated by MultiAnimation
        current = super().current_value
        self.__color = convert_color(current or (0.0, 0.0, 0.0, 0.0), convert_to=Color)

    def update(self, delta: float) -> Color:
        """
        Update the animations
        :param delta: Time since the last update in seconds
        :return: New color.
        """
        super().update(delta)
        self.__color.rgb1 = super().current_value
        return self.__color

    def reset(self) -> None:
        super().reset()
        self.__color.rgb1 = super().current_value

    @property
    def current_value(self) -> Color:
        """:return: Current values of the animations"""
        return self.__color

    @staticmethod
    def __convert_color_to_tuple(
        color_val: anim_color_t | EllipsisType | None,
    ) -> EllipsisType | tuple[float, float, float, float]:
        """
        Converts a Color or a tuple to a tuple of 4 floats (RGBA).
        Passes Ellipsis (...) through.
        """
        if color_val is ... or color_val is None:
            return ...

        # Let the external convert_color function handle scaling to 0.0 - 1.0 format
        converted = convert_color(color_val, convert_to=float)

        # Pad with alpha=1.0 if it's an RGB 3-tuple
        if len(converted) == 3:
            return float(converted[0]), float(converted[1]), float(converted[2]), 1.0

        return (
            float(converted[0]),
            float(converted[1]),
            float(converted[2]),
            float(converted[3]),
        )

    @staticmethod
    def __convert_time(
        time_val: anim_color_time_t | anim_input_t | EllipsisType | None,
    ) -> anim_color_time_t | anim_input_t | EllipsisType:
        """
        Normalizes time inputs. Passes scalars and Ellipsis (...) directly to MultiAnimation,
        or converts 4-tuples to floats.
        """
        if time_val is ... or time_val is None:
            return ...

        if isinstance(time_val, (int, float)):
            return float(time_val)

        if isinstance(time_val, tuple) and len(time_val) == 4:
            return (
                float(time_val[0]),
                float(time_val[1]),
                float(time_val[2]),
                float(time_val[3]),
            )

        return time_val

    @staticmethod
    def __is_single_color(val: anim_color_values_t) -> bool:
        """Helper to check if a value is a single color."""
        # Duck-typing for a Color object
        if hasattr(val, "get_rgba") or type(val).__name__ == "Color":
            return True

        # Treat a tuple of 3 or 4 numbers as a single color (not a tuple of start/end)
        if isinstance(val, tuple) and len(val) in (3, 4):
            if all(isinstance(v, (int, float)) for v in val):
                return True

        return False

    @classmethod
    def __convert_anim_color_values(
        cls, values: anim_color_values_t
    ) -> AnimatedColorValues:
        """
        Parses union types into the AnimatedColorValues dataclass.
        Relies on default '...' values handling in down-stream logic.
        """
        if isinstance(values, AnimatedColorValues):
            return values

        # 1. Handle single color
        if cls.__is_single_color(values):
            return AnimatedColorValues(start_value=values)

        # 2. Handle tuples representing the parameters sequentially
        if isinstance(values, tuple):
            length = len(values)

            if 2 <= length <= 8:
                return AnimatedColorValues(
                    start_value=values[0],
                    end_value=values[1],
                    extend_duration=values[2] if length > 2 else ...,
                    collapse_duration=values[3] if length > 3 else ...,
                    extend_debounce_duration=values[4] if length > 4 else ...,
                    collapse_debounce_duration=values[5] if length > 5 else ...,
                    extend_curve=values[6] if length > 6 else ...,
                    collapse_curve=values[7] if length > 7 else ...,
                )

        msg = f"Unsupported conversion format: {values}"
        raise ValueError(msg)
