"""
amoginarium/graphics/ui/_animations/_animation_types.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from dataclasses import dataclass
from enum import StrEnum
import typing as tp

from amoginarium.shared.utility import coord_t, color_t


# region Single/MultiAnimation
class AnimationPhase(StrEnum):
    """Enumeration representing the various phases of an animation."""
    AT_START = "AT_START"
    EXTENDING = "EXTENDING"
    STOPPED = "STOPPED"
    COLLAPSING = "COLLAPSING"
    AT_END = "AT_END"


type anim_input_t = tp.Union[None, float, int, tp.Sequence[tp.Union[float, int]]]

type anim_curve_t = tp.Callable[[float], float]
type anim_curve_input_t = tp.Union[None, anim_curve_t, tp.Sequence[anim_curve_t]]

# endregion

# region Vec2Animation
# noinspection DuplicatedCode
type anim_vec2_t = coord_t | float | int


@dataclass  # noqa
class AnimatedVec2Values:
    """Animated color value"""
    start_vec: anim_vec2_t
    end_vec: anim_vec2_t = ...
    extend_duration: anim_vec2_t = ...
    collapse_duration: anim_vec2_t = ...
    extend_debounce_duration: anim_input_t = ...
    collapse_debounce_duration: anim_input_t = ...
    extend_curve: anim_curve_t = ...
    collapse_curve: anim_curve_t = ...


type anim_vec2_values_t = tp.Union[
    AnimatedVec2Values, anim_vec2_t
]

# endregion

# region FloatAnimation
type anim_float_t = tp.Union[float, int]


@dataclass  # noqa
class AnimatedFloatValues:
    """Animated float value"""
    start_value: anim_float_t
    end_value: anim_float_t = ...
    extend_duration: anim_float_t = ...
    collapse_duration: anim_float_t = ...
    extend_debounce_duration: anim_input_t = ...
    collapse_debounce_duration: anim_input_t = ...
    extend_curve: anim_curve_t = ...
    collapse_curve: anim_curve_t = ...


# noinspection DuplicatedCode
type anim_float_values_t = tp.Union[
    AnimatedFloatValues, anim_float_t
]

# endregion

# region ColorAnimation
type anim_color_t = color_t
# noinspection DuplicatedCode
type anim_color_time_t = tp.Tuple[float, float, float, float] | tp.Tuple[int, int, int, int] | float | int


@dataclass  # noqa
class AnimatedColorValues:
    """Animated float value"""
    start_value: anim_color_t
    end_value: anim_color_t = ...
    extend_duration: anim_color_time_t = ...
    collapse_duration: anim_color_time_t = ...
    extend_debounce_duration: anim_input_t = ...
    collapse_debounce_duration: anim_input_t = ...
    extend_curve: anim_curve_t = ...
    collapse_curve: anim_curve_t = ...


# noinspection DuplicatedCode
type anim_color_values_t = tp.Union[
    AnimatedColorValues, anim_color_t
]

# endregion
