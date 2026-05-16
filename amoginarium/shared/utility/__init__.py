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
    classname,
    color_t,
    convert_color,
    coord_t,
    get_default,
    is_parent,
    lidar_sphere,
    multi_raycast_mask,
)

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
