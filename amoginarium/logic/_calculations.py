"""
_calculations.py
17. March 2024

defines a functions that perform some kind of calculation

Author:
Nilusink
"""
from ..debugging import timeit
from ._cvectors import Vec2
import typing as tp
from icecream import ic
import math as m


def calculate_launch_angle_iterative(
        position_delta: Vec2,  # vector from turret to target projectile
        target_velocity: Vec2,  # target projectile velocity
        target_acceleration: Vec2,
        # target projectile acceleration (gravity etc.)
        launch_speed: float,  # turret projectile speed
        recalc: int = 10,  # number of iterations
        max_time: float = 10,
        aim_type = ...,
        g: float = 9.81  # gravity affecting turret projectile
) -> tuple[Vec2, float, Vec2]:
    """
    Iteratively computes the launch vector to intercept a moving projectile.

    Returns:
        sol: unit vector to aim turret
        a_time: time-of-flight until intercept
        a_pos: predicted intercept position
    """
    # initial guess: straight-line travel time ignoring gravity
    a_time = position_delta.length / launch_speed if launch_speed > 0 else 0.1

    for _ in range(recalc):
        # predict target position at this time
        a_pos = position_delta + target_velocity * a_time + target_acceleration * 0.5 * a_time ** 2

        # compute required launch angle to reach that position
        x, y = a_pos.xy
        # ensure ratio is within [-1,1] for arcsin
        sin_angle = max(
            min(y / (launch_speed * a_time) + 0.5 * g * a_time / launch_speed,
                1.0), -1.0)
        angle = m.asin(sin_angle)

        # recompute time-of-flight based on horizontal velocity component
        v_x = launch_speed * m.cos(angle)
        if abs(v_x) < 1e-5:
            v_x = 1e-5  # prevent division by zero
        a_time_new = abs(x / v_x)

        # stop if converged
        if abs(a_time_new - a_time) < 1e-5:
            a_time = a_time_new
            break

        a_time = a_time_new
        if a_time > max_time:
            raise ValueError

    # final predicted intercept point
    ic(a_time)
    a_pos = position_delta + target_velocity * a_time + target_acceleration * 0.5 * a_time ** 2

    # launch direction unit vector
    sol = Vec2.from_polar(angle, 1)

    return sol, a_time, a_pos


# @timeit(10)
def rk4_update(
        position: Vec2,
        velocity: Vec2,
        acceleration_func: tp.Callable[[Vec2, Vec2], Vec2],
        dt: float
) -> tuple["Vec2", "Vec2"]:
    """
    Perform a single RK4 integration step for position and velocity.

    :param position: current position vector
    :param velocity: current velocity vector
    :param acceleration_func: function(pos, vel) -> acceleration vector
    :param dt: timestep in seconds
    :return: (new_position, new_velocity)
    """

    # k1
    k1_v = acceleration_func(position, velocity) * dt
    k1_x = velocity * dt

    # k2
    k2_v = acceleration_func(position + k1_x * 0.5, velocity + k1_v * 0.5) * dt
    k2_x = (velocity + k1_v * 0.5) * dt

    # k3
    k3_v = acceleration_func(position + k2_x * 0.5, velocity + k2_v * 0.5) * dt
    k3_x = (velocity + k2_v * 0.5) * dt

    # k4
    k4_v = acceleration_func(position + k3_x, velocity + k3_v) * dt
    k4_x = (velocity + k3_v) * dt

    # combine
    new_position = position + (k1_x + k2_x*2 + k3_x*2 + k4_x) * (1/6)
    new_velocity = velocity + (k1_v + k2_v*2 + k3_v*2 + k4_v) * (1/6)

    return new_position, new_velocity
