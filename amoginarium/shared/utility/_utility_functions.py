"""
_utility_functions.py
19. March 2024

a few useful functions

Author:
Nilusink
"""

import typing as tp
from types import EllipsisType

import numpy as np
import pygame as pg
from icecream import ic

from ._ccalculations import calculate_launch_angle
from ._ccolor import Color
from ._cutility_functions import raycast_mask, raycast_size
from ._cvectors import Vec2

type coord_t = tuple[int, int] | tuple[float, float] | Vec2
type color_t = tuple[float, float, float] | tuple[float, float, float, float] | Color


# from ._cutility_functions import raycast_mask as rm, infinite_lines_intersect as ili, raycast_size as rs
# from ..debugging import timeit, cum_timer
# infinite_lines_intersect = cum_timer.time_this(ili)
# raycast_size = cum_timer.time_this(rs)
# raycast_mask = cum_timer.time_this(rm)


class EntityLike(tp.Protocol):
    """really basic entity abstraction"""

    position: Vec2
    size: Vec2
    mask: pg.Mask
    rect: pg.Rect
    damage: float
    hp: float

    def hit(self, damage: float, hit_by: tp.Any) -> None: ...


def classname(c: object) -> str:
    """
    get the name of an obect class
    """
    return c.__class__.__name__


def is_parent(parent: object, child: object) -> bool:
    """
    check parent is the parent of child
    """
    if not hasattr(child, "parent"):
        return False

    return parent == child.parent


def convert_color[A: Color | int | float](
    color: color_t, convert_to: type[A] = tuple
) -> A | tuple[A, A, A, A]:
    if convert_to is Color:
        if isinstance(color, Color):
            return color.copy()

        if max(color) > 1:
            return Color().from_255(*color)

        return Color().from_1(*color)

    elif convert_to is int:
        if isinstance(color, Color):
            return color.get_rgba255()

        else:
            # noinspection PyTypeChecker
            return (*(round(c * 255) for c in color),)

    else:
        if isinstance(color, Color):
            return color.get_rgba1()
        # noinspection PyTypeChecker
        return (*(c / 255 for c in color),)


# @timeit(1)
def multi_raycast_mask(
    parent: EntityLike,
    sprites: tp.Collection[EntityLike],
    start: Vec2,
    end: Vec2,
    sample_rate: int = 10,
) -> list[tuple[EntityLike, Vec2]]:
    out = []

    for sprite in sprites:
        if sprite.parent == parent:
            continue

        if hasattr(sprite, "last_pos"):
            res = raycast_size(start, end, sprite.position, sprite.size)

            if not res:
                continue

        elif hasattr(sprite, "form"):  # check if island
            if raycast_size(start, end, sprite.position + sprite.size / 2, sprite.size):
                res = raycast_mask(sprite, start, end, sample_rate)

            else:
                continue

        elif hasattr(sprite, "is_bullet"):  # check if game entity
            res = raycast_size(start, end, sprite.position, sprite.size)

            if not res:
                continue

        else:
            continue

        if res.length > 0:
            out.append((sprite, res))

    return out


def lidar_sphere(
    position: Vec2,
    radius: float,
    segments: int,
    entity_sample: tp.Iterable[EntityLike],
    sample_rate: int = 1,
) -> list[Vec2]:
    """
    cast an array of spheres around a certain point
    and check if it hits any entity

    :returns: list of vectors to hit
    """
    angle_step = (np.pi * 2) / segments

    out = []
    for i in range(segments):
        curr_angle = i * angle_step
        delta = Vec2().from_polar(curr_angle, radius)

        hits = []
        for entity in entity_sample:
            res = raycast_mask(entity, position, position + delta, sample_rate)

            if res is not None:
                if res.length > 0:
                    hits.append(res)

        if hits:
            hits = sorted(hits, key=lambda x: x.length)

            out.append(hits[0] - position)
            continue

        out.append(delta)

    return out


def get_default[T](param: T | EllipsisType, default: T) -> T:
    """return param if not Ellipsis else default"""
    return default if isinstance(param, EllipsisType) else param


def calculate_launch_angle_all_directions(
    position_delta: Vec2,
    target_velocity: Vec2,
    target_acceleration: Vec2,
    launch_speed: float,
    recalculate: int = 10,
    aim_type: str = "low",
    g: float = 9.81,
) -> tuple[Vec2, float, Vec2]:
    """
    removes calculate_launch_angles directional restrictions

    :param position_delta: the position delta between cannon and target
    :param target_velocity: the current velocity of the target, pass empty Vec2 if no velocity is known
    :param target_acceleration: the current acceleration of the target, pass empty Vec2 if no velocity is known
    :param launch_speed: the projectile muzzle speed
    :param recalculate: how often the position is being recalculated, basically a precision parameter
    :param aim_type: either "high" - "h" or "low" - "l". Defines if the lower or higher curve should be aimed for
    :param g: gravitation inflicted on target
    :return: where to aim, tof, predicted position
    """
    # mirror y because of pygame
    position_delta.y *= -1
    target_velocity.y *= -1
    target_acceleration.y *= -1

    # mirror x if negative
    mirror = False
    if position_delta.x < 0:
        mirror = True
        position_delta.x *= -1
        target_velocity.x *= -1
        target_acceleration.x *= -1

    aiming_angle, tof, predict = calculate_launch_angle(
        position_delta,
        target_velocity,
        target_acceleration,
        launch_speed,
        recalculate,
        aim_type,
        g,
    )

    # un-mirror everything
    aiming_angle.y *= -1
    predict.y *= -1

    if mirror:
        aiming_angle.x *= -1
        predict.x *= -1

    return aiming_angle, tof, predict


def clamp[A: int | float](value: A, a: float, b: float) -> A:
    """Clamp a value between a and b."""
    if value < a:
        return a

    if value > b:
        return b

    return value
