"""
Exports UI animation types, curves, and specialized animation controllers.

| ``Path``: amoginarium/graphics/ui/_animations/__init__.py
| ``Project``: amoginarium
| ``Created``: 16.03.2026
| ``Authors``: LukasKrah
"""

from ._animation_types import anim_color_t, anim_color_values_t, anim_float_t
from ._animation_types import anim_float_values_t, anim_input_t, anim_vec2_t
from ._animation_types import anim_vec2_values_t, AnimatedColorValues
from ._animation_types import AnimatedFloatValues, AnimatedVec2Values, AnimationPhase
from ._color_animation import ColorAnimation
from ._complex_animation import Animation, ComplexAnimation, create_animation
from ._curves import peaked_s_curve, PeakedSCurve
from ._float_animation import create_float_animation, FloatAnimation
from ._multi_animation import MultiAnimation
from ._simple_animation import SimpleAnimation
from ._vec2_animation import Vec2Animation
