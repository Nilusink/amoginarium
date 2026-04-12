"""
amoginarium/graphics/ui/__init__.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from ._animations import AnimationPhase, anim_input_t, anim_vec2_t, AnimatedVec2Values, anim_vec2_values_t, \
    ComplexAnimation, create_animation, Animation, SimpleAnimation, MultiAnimation, Vec2Animation, AnimatedColorValues
from ._widgets import UIRectangle, UIButton, UICursor, UIEntry, UIStaticText, UIDynamicText
from ._base import UIElement, UIEntity
from ._types import Positions, Anchor
