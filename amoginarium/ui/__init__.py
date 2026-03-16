"""
amoginarium/ui/__init__.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from ._animations import AnimationPhase, AnimInput, anim_vec2_t, AnimatedVec2Values, anim_vec2_values_t, \
    TimedAnimation, create_animation, Animation, SingleAnimation, MultiAnimation, Vec2Animation
from ._widgets import Rectangle, Button, UICursor
from ._base import UIElement, UIEntity, UIGroup
