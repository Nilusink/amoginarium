"""
Color class, fade function, c_255_to_1 function.

Path: amoginarium/shared/utility/_ccolor.pyi
Project: amoginarium
Created: 16.03.2026
Authors: Nilusink
"""

import typing as tp

class Color:
    rgb1: tuple[float, float, float]
    rgb255: tuple[int, int, int]
    rgba1: tuple[float, float, float, float]
    rgba255: tuple[int, int, int, int]
    r1: float
    g1: float
    b1: float
    a1: float
    r255: int
    g255: int
    b255: int
    a255: int

    def get_rgb1(self) -> tuple[float, float, float]: ...
    def get_rgb255(self) -> tuple[int, int, int]: ...
    def get_rgba1(self) -> tuple[float, float, float, float]: ...
    def get_rgba255(self) -> tuple[int, int, int, int]: ...
    def set_rgb1(self, r: float, g: float, b: float) -> None: ...
    def set_rgb255(self, r: int, g: int, b: int) -> None: ...
    def set_rgba1(self, r: float, g: float, b: float, a: float) -> None: ...
    def set_rgba255(self, r: int, g: int, b: int, a: int) -> None: ...
    def from_1(self, r: float, g: float, b: float, a: float = 1) -> Color: ...
    def from_255(self, r: int, g: int, b: int, a: int = 255) -> Color: ...
    def copy(self) -> Color: ...

def fade(a: Color, b: Color, t: float) -> Color:
    """
    :param a: start color
    :param b: end color
    :param t: 0-1
    """

def c_255_to_1(r: int, g: int, b: int) -> tuple[float, float, float]: ...
