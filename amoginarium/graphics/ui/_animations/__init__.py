"""
amoginarium/graphics/ui/_animations/__init__.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from ._animation_types import (
    AnimatedColorValues,
    AnimatedFloatValues,
    AnimatedVec2Values,
    AnimationPhase,
    anim_color_t,
    anim_color_values_t,
    anim_float_t,
    anim_float_values_t,
    anim_input_t,
    anim_vec2_t,
    anim_vec2_values_t,
)
from ._color_animation import ColorAnimation
from ._complex_animation import Animation, ComplexAnimation, create_animation
from ._curves import PeakedSCurve, peaked_s_curve
from ._float_animation import FloatAnimation, create_float_animation
from ._multi_animation import MultiAnimation
from ._simple_animation import SimpleAnimation
from ._vec2_animation import Vec2Animation
