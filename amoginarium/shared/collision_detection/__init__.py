"""
amoginarium/logic/collision_detection/__init__.py

Project: amoginarium
Created: 01.04.2026
Authors: LukasKrah
"""

from ._minrect_algorithm import find_minimum_rectangles_dirty, find_minimum_rectangles
from ._collision_detection import collision_detection_aabb_aabb_minkowski_raycast
