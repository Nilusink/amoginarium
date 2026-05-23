"""
Vec2 class and calculate_launch_angle.

Path: amoginarium/shared/utility/_ccalculations.pyx
Project: amoginarium
Created: 11.03.2026
Authors: Nilusink
"""

cimport cython
from libc.math cimport cos, fabs, sqrt, atan2
from libc.stdint cimport uint16_t

from ._tracks cimport BaseTrack
from ._cvectors cimport Vec2


cdef inline double get_solution(
    double solutions[2],
    double speed,
    double g,
    Vec2 position_delta,
    str aim_type="low",
):
    cdef:
        double x
        double y
        double v2
        double discriminant
        double root

        double z1
        double z2

        double angle
        double vx

    x = position_delta.x
    y = position_delta.y

    v2 = speed * speed

    discriminant = v2 * v2 - g * (g * x * x + 2.0 * y * v2)

    if discriminant < 0.0:
        raise ValueError("no possible launch angle found")

    root = sqrt(discriminant)

    z1 = atan2(v2 + root, g * x)
    z2 = atan2(v2 - root, g * x)

    solutions[0] = z1
    solutions[1] = z2

    if aim_type == "h" or aim_type == "high":
        angle = z1 if z1 > z2 else z2
    else:
        angle = z1 if z1 < z2 else z2

    vx = speed * cos(angle)

    if fabs(vx) < 1e-9:
        raise ValueError("invalid horizontal velocity")

    # Preserve sign consistency
    if (x > 0 > vx) or (x < 0 < vx):
        raise ValueError("solution points away from target")

    return x / vx


cpdef tuple calculate_launch_angle(
    Vec2 position_delta,
    Vec2 target_velocity,
    Vec2 target_acceleration,
    float launch_speed,
    uint16_t recalculate = 10,
    str aim_type = "low",
    double g = 9.81
):
    """
    :param position_delta: the position delta between cannon and target
    :param target_velocity: the current velocity of the target, pass empty Vec2 if no velocity is known
    :param target_acceleration: the current acceleration of the target, pass empty Vec2 if no velocity is known
    :param launch_speed: the projectile muzzle speed
    :param recalculate: how often the position is being recalculated, basically a precision parameter
    :param aim_type: either "high" - "h" or "low" - "l". Defines if the lower or higher curve should be aimed for
    :param g: gravitation inflicted on target
    :return: ``target_angle@launch_velocity``, ``tof``, ``predicted_position``
    """
    if recalculate < 0:
        recalculate = 0

    # approximate where the target will be (this is not an exact method!!!)
    cdef double a_time = abs(position_delta.get_length() / launch_speed)
    cdef Vec2 a_pos = position_delta.add_vec2(target_velocity.mul_double(a_time))
    a_pos = a_pos.add_vec2(target_acceleration.mul_double(a_time**2 * 1/2))

    # mirror = False
    cdef double angle, v_x
    cdef double solutions[2]
    for _ in range(recalculate + 1):
        a_time = get_solution(
            solutions,
            launch_speed,
            g,
            a_pos,
            aim_type=aim_type
        )
        a_pos = position_delta.add_vec2(target_velocity.mul_double(a_time))
        a_pos = a_pos.add_vec2(target_acceleration.mul_double(a_time**2 * 1/2))

    if aim_type == "h" or aim_type == "high":
        angle =  solutions[0] if solutions[0] > solutions[1] else solutions[1]

    else:
        angle = solutions[0] if solutions[0] < solutions[1] else solutions[1]

    sol = Vec2().from_polar(angle, launch_speed)
    return sol, a_time, a_pos


cpdef tuple calculate_launch_solution_from_track(
    Vec2 launch_position,
    BaseTrack track,
    double launch_speed,
    uint16_t recalculate = 10,
    str aim_type = "low",
    double g = 9.81
):
    """
    Calculate the launch angle of a projectile.
    
    :param launch_position: position of weapon
    :param track: target track to calculate solution from
    :param launch_speed: the projectile muzzle speed
    :param recalculate: how often the position is being recalculated, basically a precision parameter
    :param aim_type: either "high" - "h" or "low" - "l". Defines if the lower or higher curve should be aimed for
    :param g: gravitation inflicted on target
    :return: ``target_angle@launch_velocity``, ``tof``, ``predicted_position``
    """
    # approximate where the target will be (this is not an exact method!!!)
    cdef Vec2 position_delta = track.get_position().sub_vec2(launch_position)
    cdef double a_time = abs(position_delta.get_length() / launch_speed)
    cdef Vec2 a_pos = track.predict_future_position(a_time)

    if recalculate < 0:
        recalculate = 0

    # mirror = False
    cdef double angle, v_x
    cdef double solutions[2]
    for _ in range(recalculate + 1):
        a_time = get_solution(
            solutions,
            launch_speed,
            g,
            a_pos,
            aim_type=aim_type
        )
        a_pos = track.predict_future_position(a_time).sub_vec2(launch_position)

    if aim_type == "h" or aim_type == "high":
        angle =  solutions[0] if solutions[0] > solutions[1] else solutions[1]

    else:
        angle = solutions[0] if solutions[0] < solutions[1] else solutions[1]

    sol = Vec2().from_polar(angle, launch_speed)
    return sol, a_time, a_pos
