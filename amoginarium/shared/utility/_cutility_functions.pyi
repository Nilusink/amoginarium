import typing as tp
import pygame as pg


class Vec2:
    ...


type coord_t = tuple[int, int] | tuple[float, float] | Vec2


class EntityLike(tp.Protocol):
    position: Vec2
    size: Vec2
    mask: pg.Mask
    rect: pg.Rect


def convert_coord[A: Vec2 | tuple | float](
        coord: coord_t,
        convert_to: type[A] = tuple
) -> A | tuple[float, float] | tuple[A, A]:
    """
    accepts both tuple and Vec2
    """


def is_related(a: object, b: object, depth: int = 2) -> bool:
    """
    check if either is parent or child or self

    depths:
    1: true if a == b
    2: true if a == b or parent
    3: true if all of the above or siblings
    4: coalition
    """


def raycast_mask(
        sprite: EntityLike,
        start: Vec2,
        end: Vec2,
        sample_rate: int = 10
) -> Vec2:
    ...


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


def infinite_lines_intersect(a: Vec2, b: Vec2, c: Vec2, d: Vec2) -> bool:
    """
    check if the lines between a-b and c-d intersect (infinite, no bounds)
    """

def raycast_size(a: Vec2, b: Vec2, center: Vec2, size: Vec2) -> Vec2:
    """
    checks if the line from a to b intersects the circle at center+radius
    """

def add_tuple(t1: tuple[float, float], t2: tuple[float, float]) -> float: #tuple[float, float]:
    """
    add two 2-dimensional tuples together
    """


def pack_int(i: int, n: int, values: list[int]) -> int:
    """pack ``n`` amount of values into an integer with ``i`` bits"""


def unpack_int(i: int, n: int, value: int) -> list[int]:
    """pack ``n`` amount of values from an integer with ``i`` bits"""
