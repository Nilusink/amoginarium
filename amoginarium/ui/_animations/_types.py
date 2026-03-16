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
up_to_coord_t = coord_t | float | int


@dataclass
class AnimatedVec2Values:
    """Animated color value"""
    start_vec: up_to_coord_t
    end_vec: up_to_coord_t | None = None
    extend_duration_seconds: up_to_coord_t | None = None
    collapse_duration_seconds: up_to_coord_t | None = None


anim_vec2_values_t = tp.Union[
    AnimatedVec2Values,
    tp.Tuple[up_to_coord_t, up_to_coord_t, up_to_coord_t, up_to_coord_t],
    tp.Tuple[up_to_coord_t, up_to_coord_t, up_to_coord_t],
    tp.Tuple[up_to_coord_t, up_to_coord_t],
    up_to_coord_t
]

# endregion
