"""
Shared enumeration for global debug flags used across the engine.

| Path: amoginarium/shared/_debug_vars.py
| Project: amoginarium
| Created: 20.05.2026
| Authors: LukasKrah
"""

from enum import Enum


class DebugVarsEnum(Enum):
    """
    Enum for debug values shared via global vars.
    """

    DRAW_HITBOXES = 0
