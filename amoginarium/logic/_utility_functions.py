"""
_utility_functions.py
19. March 2024

a few useful functions

Author:
Nilusink
"""
from icecream import ic
import typing as tp
import pygame as pg
import numpy as np

from ._vectors import Vec2
from ..debugging import timeit

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


def convert_coord[A](
        coord: coord_t,
        convert_to: type[A] = tuple
) -> A | tuple[float, float] | tuple[A, A]:
    """
    accepts both tuple and Vec2
    """
    if convert_to is Vec2:
        if isinstance(coord, Vec2):
            return coord.copy()

        return Vec2.from_cartesian(*coord)

    if convert_to is tuple:
        if isinstance(coord, tuple):
            return coord

        return coord.xy

    if convert_to is int:
        if isinstance(coord, Vec2):
            coord = coord.xy

        return int(coord[0]), int(coord[1])

    raise ValueError("Unsupported conversion: ", convert_to)


# @timeit(1)
def raycast_mask(
        sprite: EntityLike,
        start: coord_t,
        end: coord_t,
        sample_rate: float = 10
) -> Vec2 | None:
    start = convert_coord(start, Vec2)
    end = convert_coord(end, Vec2)

    # subtract sprites position (masks don't have positions)
    sprite_start = sprite.position

    # check if in collision box first to save time
    clipped = sprite.rect.clipline(start.xy, end.xy)
    if clipped:
        # only calculate points actually in sprite
        start, end = clipped

        # position offsets
        start = Vec2.from_cartesian(*start) - sprite_start
        end = Vec2.from_cartesian(*end) - sprite_start

        # calculate line
        delta = end - start
        sample_rate = int(
            max(abs(delta.x), abs(delta.y)) / sample_rate
        )

        # trace line through entity
        for i in range(sample_rate):
            current = start + delta * i / sample_rate

            try:
                if sprite.mask.get_at(current.xy):
                    return sprite_start + current

            except IndexError:
                continue

    return None


@timeit(1)
def lidar_sphere(
        position: Vec2,
        radius: float,
        segments: int,
        entity_sample: tp.Iterable[EntityLike],
        sample_rate: float = 1,
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
        delta = Vec2.from_polar(curr_angle, radius)

        hits = []
        for entity in entity_sample:
            res = raycast_mask(
                entity,
                position,
                position + delta,
                sample_rate
            )

            if res is not None:
                hits.append(res)

        if hits:
            hits = sorted(hits, key=lambda x: x.length)

            out.append(hits[0] - position)
            continue

        out.append(delta)

    return out


def point_in_triangle(
        p: Vec2,
        a: Vec2,
        b: Vec2,
        c: Vec2
) -> bool:
    """
    p: point to test
    a,b,c: triangle vertices
    """

    v0 = c - a
    v1 = b - a
    v2 = p - a

    dot00 = v0.dot(v0)
    dot01 = v0.dot(v1)
    dot02 = v0.dot(v2)
    dot11 = v1.dot(v1)
    dot12 = v1.dot(v2)

    denom = dot00 * dot11 - dot01 * dot01
    if denom == 0:
        return False

    inv = 1 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv
    v = (dot00 * dot12 - dot01 * dot02) * inv

    return (u >= 0) and (v >= 0) and (u + v <= 1)
