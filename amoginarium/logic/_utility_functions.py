"""
_utility_functions.py
19. March 2024

a few useful functions

Author:
Nilusink
"""
from icecream import ic

from ._vectors import Vec2


type coord_t = tuple[int, int] | tuple[float, float] | Vec2


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
) -> A | tuple[A, A]:
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
