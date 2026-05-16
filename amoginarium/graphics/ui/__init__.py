"""
amoginarium/graphics/ui/__init__.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from ._animations import (
    AnimatedColorValues,
    AnimatedVec2Values,
    Animation,
    AnimationPhase,
    ComplexAnimation,
    MultiAnimation,
    SimpleAnimation,
    Vec2Animation,
    anim_input_t,
    anim_vec2_t,
    anim_vec2_values_t,
    create_animation,
)
from ._base import UIElement, UIEntity
from ._types import Anchor, Positions
from ._widgets import UIButton, UICursor, UIDynamicText, UIRectangle, UIStaticText
