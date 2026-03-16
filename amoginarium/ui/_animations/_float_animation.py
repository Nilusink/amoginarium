"""
amoginarium/ui/_animations/_float_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

from ._types import anim_float_values_t, AnimatedFloatValues
from ._single_animation import SingleAnimation
from ._timed_animation import create_animation


class _FloatAnimationHelper:
    """Helper class for float animation conversions."""

    @staticmethod
    def convert(values: anim_float_values_t) -> AnimatedFloatValues:
        """
        Parses union types into the AnimatedFloatValues dataclass,
        normalizing all inputs to floats.
        """
        if isinstance(values, AnimatedFloatValues):
            return values

        # 1. Handle single float or int
        if isinstance(values, (int, float)):
            norm_val = float(values)
            return AnimatedFloatValues(
                start_value=norm_val,
                end_value=norm_val,
                extend_duration_seconds=0.0,
                collapse_duration_seconds=0.0
            )

        # 2. Handle tuples representing (start, end, extend_dur, collapse_dur)
        if isinstance(values, tuple):
            length = len(values)

            if length == 2:
                return AnimatedFloatValues(
                    start_value=float(values[0]),
                    end_value=float(values[1]),
                    extend_duration_seconds=0.0,
                    collapse_duration_seconds=0.0
                )

            elif length == 3:
                return AnimatedFloatValues(
                    start_value=float(values[0]),
                    end_value=float(values[1]),
                    extend_duration_seconds=float(values[2]),
                    collapse_duration_seconds=float(values[2])
                )

            elif length == 4:
                return AnimatedFloatValues(
                    start_value=float(values[0]),
                    end_value=float(values[1]),
                    extend_duration_seconds=float(values[2]),
                    collapse_duration_seconds=float(values[3])
                )

        raise ValueError(f"Unsupported conversion format: {values}")


def create_float_animation(value: anim_float_values_t) -> SingleAnimation:
    """
    Creates either a SingleAnimation or a TimedAnimation based on the input values.

    :param value: Float animation values (single value, tuple, or AnimatedFloatValues)
    :return: The configured SingleAnimation or TimedAnimation instance.
    """
    val = _FloatAnimationHelper.convert(value)

    return create_animation(
        start_value=val.start_value,
        end_value=val.end_value,
        extend_duration_seconds=val.extend_duration_seconds,
        collapse_duration_seconds=val.collapse_duration_seconds
    )
