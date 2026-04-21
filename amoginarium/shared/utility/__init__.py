from ._utility_classes import BetterDict, SimpleLock, WDTimer
from ._utility_functions import is_parent, classname, \
    coord_t, lidar_sphere, convert_color, color_t
from ._calculations import calculate_launch_angle_iterative, rk4_update
from ._cvectors import Vec2, normalize_angle
from ._ccolor import Color, fade, c_255_to_1
from ._constants import SQ2, MASK16, MASK32, MASK64
from ._tuplemath import TupleMath

from ._cutility_functions import point_in_triangle, raycast_mask, convert_coord
from ._cutility_functions import is_related, raycast_size, add_tuple, pack_int
from ._cutility_functions import unpack_int
from ._ccalculations import calculate_launch_angle
from ._utility_functions import multi_raycast_mask, get_default
from ._error_types import WtfError


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
