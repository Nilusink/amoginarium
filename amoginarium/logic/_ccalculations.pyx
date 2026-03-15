cimport cython
from libc.math cimport sqrt, atan, cos, sin, pi
from libc.stdint cimport uint16_t
from ._cvectors cimport Vec2


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
    :return: where to aim, tof, predicted position
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
        solutions.clear()

        # calculate possible launch angles
        x = a_pos.x
        y = a_pos.y

        a = (g / 2) * (x / launch_speed) ** 2
        b = a + y

        sd = sqrt(x ** 2 - 4 * a * b)
        if sd > 0 and a > 0:
            z1 = (x + sd) / (2 * a)
            solutions[0] = atan(z1)

            z2 = (x - sd) / (2 * a)
            solutions[1] = atan(z2)

        else:
            raise ValueError("no possible launch angle found")

        # recalculate the probable position of the target using the now
        # calculated angle
        if aim_type == "h" or aim_type == "high":
            angle =  solutions[0] if solutions[0] > solutions[1] else solutions[1]

        else:
            angle = solutions[0] if solutions[0] < solutions[1] else solutions[1]

        v_x = launch_speed * cos(angle)

        a_time = abs(x / v_x)

        a_pos = position_delta.add_vec2(target_velocity.mul_double(a_time))
        a_pos = a_pos.add_vec2(target_acceleration.mul_double(a_time**2 * 1/2))

    if aim_type == "h" or aim_type == "high":
        angle =  solutions[0] if solutions[0] > solutions[1] else solutions[1]

    else:
        angle = solutions[0] if solutions[0] < solutions[1] else solutions[1]

    sol = Vec2().from_polar(angle, 1)
    return sol, a_time, a_pos
