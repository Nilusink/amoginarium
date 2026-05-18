"""
Exposes core mathematical, geometric, and system utility functions and classes.

Path: amoginarium/shared/utility/__init__.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

from ._calculations import calculate_launch_angle_iterative, rk4_update
from ._ccalculations import calculate_launch_angle
from ._ccolor import Color, c_255_to_1, fade
from ._constants import *
from ._cutility_functions import (
    add_tuple,
    convert_coord,
    is_related,
    pack_int,
    point_in_triangle,
    raycast_mask,
    raycast_size,
    unpack_int,
)
from ._cvectors import (
    Vec2,
    clamp_angle,
    max_angle,
    min_angle,
    normalize_angle,
    normalize_angle_neg,
)
from ._error_types import WtfError
from ._minrect_algorithm import find_minimum_rectangles, find_minimum_rectangles_dirty
from ._pid_controller import PIDController
from ._tuplemath import TupleMath
from ._utility_classes import BetterDict, SimpleLock, WDTimer
from ._utility_functions import (
    calculate_launch_angle_all_directions,
    clamp,
    classname,
    color_t,
    convert_color,
    coord_t,
    get_default,
    is_parent,
    lidar_sphere,
    multi_raycast_mask,
)
