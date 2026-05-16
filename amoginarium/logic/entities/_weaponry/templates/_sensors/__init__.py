"""
amoginarium/logic/entities/_sensors/__init__.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from ._detection_group import (
    DetectionGroup,
    DETECTION_GROUP_MANAGER,
    DETECTION_GLOBAL_RED,
    DETECTION_GLOBAL_BLUE,
    DETECTION_GLOBAL_NEUTRAL,
)
from ._base_sensor import BaseSensor
from ._magic_sensor import MagicSensor
from ._radar_sensor import RadarSensor

