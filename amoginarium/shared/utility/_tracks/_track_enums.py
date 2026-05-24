"""
Contains enumerators required by target tracks.

Path: amoginarium/shared/utility/_tracks/_track_enums.py
Project: amoginarium
Created: 23.05.2026
Authors: Nilusink
"""

import typing as tp
from enum import Enum


TRACK_HALF_TIME: tp.Final[float] = 1.0


class TrackState(Enum):
    """Track state."""

    NEW = 0
    TENTATIVE = 1
    CONFIRMED = 2
    DEGRADED = 3
    LOST = 4
    DEAD = -1


class TrackQuality(Enum):
    """Specify target track quality."""

    NONE = -1
    POS_ONLY = 0
    POS_AND_VEL = 1
    POS_VEL_ACC = 2
