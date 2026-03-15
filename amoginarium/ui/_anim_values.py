"""
amoginarium/ui/_anim_values.py

Project: amoginarium
Created: 15.03.2026
Authors: LukasKrah
"""
import dataclasses
import typing as tp

from ._types import ui_color_t


@dataclasses.dataclass()
class AnimColor():
    start_value: ui_color_t
    end_value: ui_color_t
    extend_duration_seconds: float
    collapse_duration_seconds: float
