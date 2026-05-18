"""
Defines enumeration types for UI element positioning and anchoring.

Path: amoginarium/graphics/ui/_types.py
Project: amoginarium
Created: 02.03.2026
Authors: LukasKrah
"""

from enum import StrEnum


class Anchor(StrEnum):
    """UI Placement anchor types."""

    NW = "nw"
    NE = "NE"
    SW = "sw"
    SE = "se"
    CENTER = "center"


class Positions(StrEnum):
    """UI Positions of each element."""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
