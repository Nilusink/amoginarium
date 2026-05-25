"""
Utility functions written in cython.

| ``Path``: amoginarium/shared/utility/_cutility_functions.pyi
| ``Project``: amoginarium
| ``Created``: 11.03.2026
| ``Authors``: Nilusink
"""

import typing as tp

import pygame as pg

class Vec2: ...

type coord_t = tuple[int, int] | tuple[float, float] | Vec2

class EntityLike(tp.Protocol):
    position: Vec2
    size: Vec2
    mask: pg.Mask
    rect: pg.Rect

@tp.overload
def convert_coord(coord: coord_t, convert_to: tuple | int | Vec2) -> coord_t:
    """
    Convert 2-dimensional coordinate type
    :param coord: Value to convert
    :param convert_to: What to convert to
    :return: Converted value.
    """

@tp.overload
def convert_coord(coord: coord_t, convert_to: type[Vec2]) -> Vec2: ...
@tp.overload
def convert_coord(coord: coord_t, convert_to: type[int]) -> tuple[int, int]: ...
@tp.overload
def convert_coord(coord: Vec2, convert_to: type[tuple]) -> tuple[float, float]: ...
@tp.overload
def convert_coord(
    coord: tuple[int, int], convert_to: type[tuple]
) -> tuple[int, int]: ...
@tp.overload
def convert_coord(
    coord: tuple[float, int], convert_to: type[tuple]
) -> tuple[float, int]: ...
@tp.overload
def convert_coord(
    coord: tuple[int, float], convert_to: type[tuple]
) -> tuple[int, float]: ...
@tp.overload
def convert_coord(
    coord: tuple[float, float], convert_to: type[tuple]
) -> tuple[float, float]: ...
@tp.overload
def convert_coord[T: tuple[float | int, float | int]](
    coord: T,
) -> T: ...
@tp.overload
def convert_coord(
    coord: Vec2,
) -> tuple[float, float]: ...
def is_related(a: object, b: object, depth: int = 2) -> bool:
    """
    Check if either is parent or child or self.

    depths:
    1: true if a == b
    2: true if a == b or parent
    3: true if all of the above or siblings
    4: coalition
    """

def raycast_mask(
    sprite: EntityLike, start: Vec2, end: Vec2, sample_rate: int = 10
) -> Vec2: ...
def point_in_triangle(p: Vec2, a: Vec2, b: Vec2, c: Vec2) -> bool:
    """
    p: point to test
    a,b,c: triangle vertices.
    """

def infinite_lines_intersect(a: Vec2, b: Vec2, c: Vec2, d: Vec2) -> bool:
    """
    Check if the lines between a-b and c-d intersect (infinite, no bounds).
    """

def raycast_size(a: Vec2, b: Vec2, center: Vec2, size: Vec2) -> Vec2:
    """
    Checks if the line from a to b intersects the circle at center+radius.
    """

def add_tuple(
    t1: tuple[float, float], t2: tuple[float, float]
) -> float:  # tuple[float, float]:
    """
    Add two 2-dimensional tuples together.
    """

def pack_int(i: int, n: int, values: list[int]) -> int:
    """Pack ``n`` amount of values into an integer with ``i`` bits."""

def unpack_int(i: int, n: int, value: int) -> list[int]:
    """Pack ``n`` amount of values from an integer with ``i`` bits."""
