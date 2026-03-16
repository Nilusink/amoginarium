"""
amoginarium/ui/__init__.py

Project: amoginarium
Created: 26.03.2024
Authors: Nilusink, LukasKrah
"""

from ._animations import AnimationPhase, AnimInput, up_to_coord_t, AnimatedVec2Values, anim_vec2_values_t, \
    TimedAnimation, create_animation, Animation, SingleAnimation, MultiAnimation, Vec2Animation
from ._component import UIComponent
from ._rectangle import Rectangle
from ._entity import UIEntity
from ._button import Button
from ._cursor import UICursor
