"""
_vectors.py
25. January 2024

defines game Vectors

Author:
Nilusink
"""
from __future__ import annotations
import math as m
from icecream import ic

from ..debugging import timeit


class Vec2:
    x: float
    y: float
    angle: float
    length: float
    __slots__ = ("__x", "__y", "__angle", "__length", "_p", "_c")

    def __init__(self) -> None:
        self.__x: float = 0
        self.__y: float = 0
        self.__angle: float = 0
        self.__length: float = 0
        self._p = False
        self._c = False

    # variable getters / setters
    @property
    def x(self):
        if self._p:
            self.__update()

        return self.__x

    @x.setter
    def x(self, value):
        if self._p:
            self.__update()

        self.__x = value
        self._c = True

    @property
    def y(self):
        if self._p:
            self.__update()

        return self.__y

    @y.setter
    def y(self, value):
        if self._p:
            self.__update()

        self.__y = value
        self._c = True

    @property
    def xy(self):
        if self._p:
            self.__update()

        return self.__x, self.__y

    @xy.setter
    def xy(self, xy):
        if self._p:
            self.__update()

        self.__x = xy[0]
        self.__y = xy[1]
        self._c = True

    @property
    def angle(self):
        """
        value in radian
        """
        if self._c:
            self.__update()

        return self.__angle

    @angle.setter
    def angle(self, value):
        """
        value in radian
        """
        if self._c:
            self.__update()

        self.__angle = self.normalize_angle(value)
        self._p = True

    @property
    def length(self):
        if self._c:
            self.__update()

        return self.__length

    @length.setter
    def length(self, value):
        if self._c:
            self.__update()

        self.__length = value
        self._p = True

    @property
    def polar(self):
        if self._c:
            self.__update()

        return self.__angle, self.__length

    @polar.setter
    def polar(self, polar):
        if self._c:
            self.__update()

        self.__angle = polar[0]
        self.__length = polar[1]
        self._p = True

    # interaction
    def split_vector(self, direction):
        """
        :param direction: A vector facing in the wanted direction
        :return: tuple[Vector in only that direction, everything else]
        """
        a = (direction.angle - self.angle)
        facing = Vec2.from_polar(
            angle=direction.angle,
            length=self.length * m.cos(a)
        )
        other = Vec2.from_polar(
            angle=direction.angle - m.pi / 2,
            length=self.length * m.sin(a)
        )

        return facing, other

    def dot(self, other: Vec2) -> float:
        return self.x * other.x + self.y * other.y

    # @timeit(10)
    def copy(self):
        v = Vec2()
        v.__x = self.__x
        v.__y = self.__y
        v.__angle = self.__angle
        v.__length = self.__length
        v._c = self._c
        v._p = self._p
        return v

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "length": self.length,
        }

    def normalize(self) -> "Vec2":
        if self._c:
            self.__update()

        self.__length = 1
        self._p = True
        return self

    def mirror(self, mirror_by: "Vec2") -> "Vec2":
        mirror_by = mirror_by.copy().normalize()
        ang_d = mirror_by.angle - self.angle
        self.angle = mirror_by.angle + 2 * ang_d
        return self

    # maths
    def __add__(self, other):
        if isinstance(other, Vec2):
            return Vec2.from_cartesian(x=self.x + other.x, y=self.y + other.y)

        return Vec2.from_cartesian(x=self.x + other, y=self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vec2):
            return Vec2.from_cartesian(x=self.x - other.x, y=self.y - other.y)

        return Vec2.from_cartesian(x=self.x - other, y=self.y - other)

    def __mul__(self, other):
        if isinstance(other, Vec2):
            return Vec2.from_polar(
                angle=self.angle + other.angle,
                length=self.length * other.length
            )

        return Vec2.from_cartesian(x=self.x * other, y=self.y * other)

    def __truediv__(self, other):
        return Vec2.from_cartesian(x=self.x / other, y=self.y / other)

    # internal functions
    def __update(self):
        """
        :param calc_from: polar (p) | cartesian (c)
        """
        if self._p and self._c:
            raise RuntimeError("polar and cartesian have both been set without recalc")

        if not any([self._p, self._c]):
            ic(self._p, self._c)

        if self._p:
            self.__x = m.cos(self.__angle) * self.__length
            self.__y = m.sin(self.__angle) * self.__length
            self._p = False

        elif self._c:
            self.__length = m.sqrt(self.__x*self.__x + self.__y*self.__y)
            self.__angle = m.atan2(self.__y, self.__x)
            self._c = False

        else:
            raise ValueError("Invalid value for \"calc_from\"")

    def __abs__(self):
        return m.sqrt(self.x**2 + self.y**2)

    def __repr__(self):
        return f"<\n" \
               f"\tVec2:\n" \
               f"\tx:{self.x}\ty:{self.y}\n" \
               f"\tangle:{self.angle}\tlength:{self.length}\n" \
               f">"

    # static methods.
    # creation of new instances
    @staticmethod
    def from_cartesian(x, y) -> "Vec2":
        p = Vec2()
        p.__x = x
        p.__y = y
        p._c = True
        p.__update()

        return p

    @staticmethod
    def from_polar(angle, length) -> "Vec2":
        p = Vec2()
        p.__angle = angle
        p.__length = length
        p._p = True
        p.__update()

        return p

    @staticmethod
    def from_dict(dictionary: dict) -> "Vec2":
        if "x" in dictionary and "y" in dictionary:
            return Vec2.from_cartesian(x=dictionary["x"], y=dictionary["y"])

        elif "angle" in dictionary and "length" in dictionary:
            return Vec2.from_polar(
                angle=dictionary["angle"],
                length=dictionary["length"]
                )

        else:
            raise KeyError(
                "either (x & y) or (angle & length) must be in dict!"
            )

    @staticmethod
    def normalize_angle(value: float) -> float:
        return value % (2 * m.pi)
