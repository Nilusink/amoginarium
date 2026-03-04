"""
_calculations.py
17. March 2024

defines a functions that perform some kind of calculation

Author:
Nilusink
"""
from ..debugging import print_ic_style
from contextlib import suppress
from ._vectors import Vec2
import math as m


def calculate_launch_angle(
    position_delta: Vec2,
    target_velocity: Vec2,
    target_acceleration: Vec2,
    launch_speed: float,
    recalculate: int = 10,
    aim_type: str = "low",
    g: float = 9.81
) -> tuple[Vec2, float, Vec2]:
    """
    :param position_delta: the position delta between cannon and target
    :param target_velocity: the current velocity of the target, pass empty Vec3 if no velocity is known
    :param launch_speed: the projectile muzzle speed
    :param recalculate: how often the position is being recalculated, basically a precision parameter
    :param aim_type: either "high" - "h" or "low" - "l". Defines if the lower or higher curve should be aimed for
    :return: where to aim, tof, predicted position
    """
    if recalculate < 0:
        recalculate = 0

    aim_type = max if aim_type.lower() in ("high", "h") else min

    # approximate where the target will be (this is not an exact method!!!)
    a_time = abs(position_delta.length / launch_speed)
    # prev_time = a_time
    # a_pos = position_delta + target_velocity * a_time
    a_pos = position_delta + target_velocity * a_time
    a_pos += target_acceleration * a_time**2 * 1/2

    # mirror = False
    solutions: list[float] = []
    # print_ic_style(a_pos.xy, a_time, position_delta.xy, target_velocity.xy, launch_speed)
    for _ in range(recalculate + 1):
        solutions.clear()

        # calculate possible launch angles
        x, y = a_pos.xy

        a = (g / 2) * (x / launch_speed) ** 2
        b = a + y

        with suppress(ValueError):
            z1 = (x + m.sqrt(x ** 2 - 4 * a * b)) / (2 * a)
            solutions.append(m.atan(z1))

        with suppress(ValueError):
            z2 = (x - m.sqrt(x ** 2 - 4 * a * b)) / (2 * a)
            solutions.append(m.atan(z2))

        if not solutions:
            # if not mirror:
            #     print_ic_style("mirror")
            #     mirror = True

            #     position_delta.x *= -1
            #     target_velocity.x *= -1
            #     target_acceleration.x *= -1

            #     print_ic_style(a_pos.xy, a_time, position_delta.xy, target_velocity.xy, launch_speed)
            #     a_time = prev_time
            #     a_pos = position_delta + target_velocity * a_time
            #     a_pos += target_acceleration * a_time**2 * 1/2
            #     print_ic_style(a_pos.xy, a_time)
            #     continue

            # print_ic_style("impossible: ", a_pos.xy, a_time)
            raise ValueError("no possible launch angle found")

        # recalculate the probable position of the target using the now
        # calculated angle
        angle = aim_type(solutions)
        v_x = launch_speed * m.cos(angle)

        # prev_time = a_time
        a_time = abs(x / v_x) * 1.1

        a_pos = position_delta + target_velocity * a_time
        a_pos += target_acceleration * a_time**2 * 1/2
        # print_ic_style(a_pos.xy, a_time, position_delta.xy, target_velocity.xy, launch_speed)

    sol = Vec2.from_polar(aim_type(solutions), 1)
    return sol, a_time / 1.0, a_pos
