"""
Converts input types into configured float-based UI animation instances.

| Path: amoginarium/graphics/ui/_animations/_float_animation.py
| Project: amoginarium
| Created: 16.03.2026
| Authors: LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._animation_types import AnimatedFloatValues
from ._complex_animation import Animation, create_animation

if TYPE_CHECKING:
    from ._animation_types import anim_float_values_t


class _FloatAnimationHelper:
    """Helper class for float animation conversions."""

    @staticmethod
    def convert(values: anim_float_values_t) -> AnimatedFloatValues:
        """
        Parses union types into the AnimatedFloatValues dataclass,
        relying on `...` for value defaults.
        """
        if isinstance(values, AnimatedFloatValues):
            return values

        # 1. Handle single float or int
        if isinstance(values, (int, float)):
            return AnimatedFloatValues(start_value=float(values))

        # 2. Handle tuples representing the parameters sequentially
        if isinstance(values, tuple):
            length = len(values)

            if 2 <= length <= 8:
                return AnimatedFloatValues(
                    start_value=float(values[0]),
                    end_value=float(values[1]),
                    extend_duration=float(values[2]) if length > 2 else ...,
                    collapse_duration=float(values[3]) if length > 3 else ...,
                    extend_debounce_duration=float(values[4]) if length > 4 else ...,
                    collapse_debounce_duration=float(values[5]) if length > 5 else ...,
                    extend_curve=values[6] if length > 6 else ...,
                    collapse_curve=values[7] if length > 7 else ...,
                )

        msg = f"Unsupported conversion format: {values}"
        raise ValueError(msg)


FloatAnimation = Animation


def create_float_animation(value: anim_float_values_t) -> Animation:
    """
    Creates either a SimpleAnimation or a ComplexAnimation based on the input values.

    :param value: Float animation values (single value, tuple, or AnimatedFloatValues)
    :return: The configured SimpleAnimation or ComplexAnimation instance.
    """
    val = _FloatAnimationHelper.convert(value)

    return create_animation(
        start_value=val.start_value,
        end_value=val.end_value,
        extend_duration=val.extend_duration,
        collapse_duration=val.collapse_duration,
        extend_debounce_duration=val.extend_debounce_duration,
        collapse_debounce_duration=val.collapse_debounce_duration,
        extend_curve=val.extend_curve,
        collapse_curve=val.collapse_curve,
    )
