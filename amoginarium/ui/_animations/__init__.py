"""
amoginarium/ui/_animations/__init__.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from ._types import AnimationPhase, AnimInput, anim_vec2_t, AnimatedVec2Values, anim_vec2_values_t, \
    anim_float_values_t, anim_float_t, AnimatedFloatValues
from ._timed_animation import TimedAnimation, create_animation, Animation
from ._float_animation import create_float_animation
from ._single_animation import SingleAnimation
from ._multi_animation import MultiAnimation
from ._vec2_animation import Vec2Animation
