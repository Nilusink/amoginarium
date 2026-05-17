"""
amoginarium/logic/entities/_sensors/__init__.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from ._base_sensor import BaseSensor
from ._detection_group import DETECTION_GLOBAL_BLUE
from ._detection_group import DETECTION_GLOBAL_NEUTRAL, DETECTION_GLOBAL_RED
from ._detection_group import DETECTION_GROUP_MANAGER, DetectionGroup
from ._magic_sensor import MagicSensor
from ._radar_sensor import RadarSensor
