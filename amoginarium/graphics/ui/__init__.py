"""
amoginarium/graphics/ui/__init__.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from ._animations import anim_input_t, anim_vec2_t, anim_vec2_values_t
from ._animations import AnimatedColorValues, AnimatedVec2Values, Animation
from ._animations import AnimationPhase, ComplexAnimation, create_animation
from ._animations import MultiAnimation, SimpleAnimation, Vec2Animation
from ._base import UIElement, UIEntity
from ._types import Anchor, Positions
from ._widgets import UIButton, UICursor, UIDynamicText, UIRectangle, UIStaticText
