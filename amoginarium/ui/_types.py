"""
amoginarium/entities/_ui/_ui_types.py

Project: amoginarium
Created: 02.03.2026
Authors: LukasKrah
"""

from enum import StrEnum
import typing as tp


class Anchor(StrEnum):
    """UI Placement anchor types"""
    NW = "nw"
    CENTER = "center"


ui_color_t = tp.Union[tuple[int, int, int], tuple[int, int, int, int]]  # Temporary solution
