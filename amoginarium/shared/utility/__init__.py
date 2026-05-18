"""
Exposes core mathematical, geometric, and system utility functions and classes.

Path: amoginarium/shared/utility/__init__.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

from ._calculations import calculate_launch_angle_iterative, rk4_update
from ._ccalculations import calculate_launch_angle
from ._ccolor import c_255_to_1, Color, fade
from ._constants import *
from ._cutility_functions import add_tuple, convert_coord, is_related
from ._cutility_functions import pack_int, point_in_triangle
from ._cutility_functions import raycast_mask, raycast_size, unpack_int
from ._cvectors import clamp_angle, max_angle, min_angle
from ._cvectors import normalize_angle, normalize_angle_neg, Vec2
from ._error_types import WtfError
from ._minrect_algorithm import find_minimum_rectangles, find_minimum_rectangles_dirty
from ._pid_controller import PIDController
from ._tuplemath import TupleMath
from ._utility_classes import BetterDict, SimpleLock, WDTimer
from ._utility_functions import calculate_launch_angle_all_directions, classname
from ._utility_functions import color_t, convert_color, coord_t, get_default
from ._utility_functions import is_parent, lidar_sphere, multi_raycast_mask

# from ._cutility_functions import point_in_triangle as _pit, raycast_mask as _rm, convert_coord as _cc, is_related as _ir
# from ._ccalculations import calculate_launch_angle as _cla
# from ._utility_functions import multi_raycast_mask as _mrm
#
# calculate_launch_angle = cum_timer.time_this(_cla)
# point_in_triangle = cum_timer.time_this(_pit)
# raycast_mask = cum_timer.time_this(_rm)
# multi_raycast_mask = cum_timer.time_this(_mrm)
# convert_coord = cum_timer.time_this(_cc)
# is_related = cum_timer.time_this(_ir)
