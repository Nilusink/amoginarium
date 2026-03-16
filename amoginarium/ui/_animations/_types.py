"""
amoginarium/ui/_animations/_types.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from dataclasses import dataclass
from enum import StrEnum
import typing as tp

from ...logic import coord_t


# region Single/MultiAnimation
class AnimationPhase(StrEnum):
    """Enumeration representing the various phases of an animation."""
    AT_START = "AT_START"
    EXTENDING = "EXTENDING"
    STOPPED = "STOPPED"
    COLLAPSING = "COLLAPSING"
    AT_END = "AT_END"


AnimInput = tp.Union[None, float, int, tp.Sequence[tp.Union[float, int]]]

# endregion

# region Vec2Animation
anim_vec2_t = coord_t | float | int


@dataclass  # noqa
class AnimatedVec2Values:
    """Animated color value"""
    start_vec: anim_vec2_t
    end_vec: anim_vec2_t | None = None
    extend_duration_seconds: anim_vec2_t | None = None
    collapse_duration_seconds: anim_vec2_t | None = None


anim_vec2_values_t = tp.Union[
    AnimatedVec2Values,
    tp.Tuple[anim_vec2_t, anim_vec2_t, anim_vec2_t, anim_vec2_t],
    tp.Tuple[anim_vec2_t, anim_vec2_t, anim_vec2_t],
    tp.Tuple[anim_vec2_t, anim_vec2_t],
    anim_vec2_t
]

# endregion

# region FloatAnimation

anim_float_t = tp.Union[float, int]


@dataclass  # noqa
class AnimatedFloatValues:
    """Animated float value"""
    start_value: anim_float_t
    end_value: anim_float_t | None = None
    extend_duration_seconds: anim_float_t | None = None
    collapse_duration_seconds: anim_float_t | None = None


anim_float_values_t = tp.Union[
    AnimatedFloatValues,
    tp.Tuple[anim_float_t, anim_float_t, anim_float_t, anim_float_t],
    tp.Tuple[anim_float_t, anim_float_t, anim_float_t],
    tp.Tuple[anim_float_t, anim_float_t],
    anim_float_t
]

# endregion

# region ColorAnimation

# endregion
