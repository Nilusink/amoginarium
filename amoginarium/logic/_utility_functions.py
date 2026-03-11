"""
_utility_functions.py
19. March 2024

a few useful functions

Author:
Nilusink
"""
from icecream import ic
from numba import njit
import typing as tp
import pygame as pg
import numpy as np

from ._cutility_functions import raycast_mask
from ..debugging import timeit
from ._cvectors import Vec2

type coord_t = tuple[int, int] | tuple[float, float] | Vec2


class EntityLike(tp.Protocol):
    position: Vec2
    size: Vec2
    mask: pg.Mask
    rect: pg.Rect


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


# @run_with_debug(show_args=True)
def is_related(a: object, b: object, depth: int = 2) -> bool:
    """
    check if either is parent or child or self

    depths:
    1: true if a == b
    2: true if a == b or parent
    3: true if all of the above or siblings
    4: coalition
    """
    is_same = a == b
    if depth <= 1:
        return is_same

    is_parented = False

    try:
        is_parented = is_parented or a.parent == b
    except AttributeError:
        pass

    try:
        is_parented = is_parented or b.parent == a
    except AttributeError:
        pass

    if depth <= 2:
        return is_same or is_parented

    try:
        if a.parent is not ... and b.parent is not ...:
            is_sibling = a.parent == b.parent

        else:
            is_sibling = False

    except AttributeError:
        is_sibling = False

    if depth <= 3:
        return is_same or is_parented or is_sibling

    try:
        is_coalition = a.coalition == b.coalition

    except AttributeError:
        is_coalition = False

    if depth <= 4:
        return is_same or is_parented or is_sibling or is_coalition

    return False


def convert_coord[A: Vec2 | tuple | float](
        coord: coord_t,
        convert_to: type[A] = tuple
) -> A | tuple[float, float] | tuple[A, A]:
    """
    accepts both tuple and Vec2
    """
    if convert_to is Vec2:
        if isinstance(coord, Vec2):
            return coord.copy()

        return Vec2().from_cartesian(*coord)

    if convert_to is tuple:
        if isinstance(coord, tuple):
            return coord

        return coord.xy

    if convert_to is int:
        if isinstance(coord, Vec2):
            coord = coord.xy

        return int(coord[0]), int(coord[1])

    raise ValueError("Unsupported conversion: ", convert_to)


@timeit(1)
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
            res = raycast_mask(
                entity,
                position,
                position + delta,
                sample_rate
            )

            if res is not None:
                if res.length > 0:
                    hits.append(res)

        if hits:
            hits = sorted(hits, key=lambda x: x.length)

            out.append(hits[0] - position)
            continue

        out.append(delta)

    return out
