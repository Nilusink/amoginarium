# fast Color.pyx
from typing import Tuple

cimport cython
from libc.stdint cimport uint8_t


cdef class Color:
    cdef double _r1, _g1, _b1, _a1
    cdef uint8_t _r255, _g255, _b255, _a255

    def __cinit__(self):
        self._r1 = 0.0
        self._g1 = 0.0
        self._b1 = 0.0
        self._a1 = 0.0
        self._r255 = 0
        self._g255 = 0
        self._b255 = 0
        self._a255 = 0

    # region single properties
    @property
    def r1(self):
        return self._r1

    @property
    def g1(self):
        return self._g1

    @property
    def b1(self):
        return self._b1

    @property
    def a1(self):
        return self._a1

    @property
    def r255(self):
        return self._r255

    @property
    def g255(self):
        return self._g255

    @property
    def b255(self):
        return self._b255

    @property
    def a255(self):
        return self._a255
    # endregion

    # region tuple properties
    @property
    def rgb1(self):
        return self.get_rgb1()

    @rgb1.setter
    def rgb1(self, value):
        self.set_rgb1(value[0], value[1], value[2])

    @property
    def rgba1(self):
        return self.get_rgba1()

    @rgba1.setter
    def rgba1(self, value):
        self.set_rgba1(value[0], value[1], value[2], value[3])

    @property
    def rgb255(self):
        return self.get_rgb255()

    @rgb255.setter
    def rgb255(self, value):
        self.set_rgb255(value[0], value[1], value[2])

    @property
    def rgba255(self):
        return self.get_rgba255()

    @rgba255.setter
    def rgba255(self, value):
        self.set_rgba255(value[0], value[1], value[2], value[3])
    # endregion

    # region c functions
    cpdef tuple get_rgb1(self):
        return self._r1, self._g1, self._b1

    cpdef tuple get_rgb255(self):
        return self._r255, self._g255, self._b255

    cpdef tuple get_rgba1(self):
        return self._r1, self._g1, self._b1, self._a1

    cpdef tuple get_rgba255(self):
        return self._r255, self._g255, self._b255, self._a255

    cpdef Color set_rgb1(self, double r, double g, double b):  # type: (float, float, float) -> Color
        self._r1 = r
        self._g1 = g
        self._b1 = b
        self._r255 = <uint8_t>(r * 255 + 0.5)  # apparently the same as round
        self._g255 = <uint8_t>(g * 255 + 0.5)
        self._b255 = <uint8_t>(b * 255 + 0.5)
        return self

    cpdef Color set_rgb255(self, uint8_t r, uint8_t g, uint8_t b):  # type: (int, int, int) -> Color
        self._r1 = r / 255.0
        self._g1 = g / 255.0
        self._b1 = b / 255.0
        self._r255 = r
        self._g255 = g
        self._b255 = b
        return self

    cpdef Color set_rgba1(self, double r, double g, double b, double a):  # type: (float, float, float, float) -> Color
        self._r1 = r
        self._g1 = g
        self._b1 = b
        self._a1 = a
        self._r255 = <uint8_t>(r * 255 + 0.5)  # apparently the same as round
        self._g255 = <uint8_t>(g * 255 + 0.5)
        self._b255 = <uint8_t>(b * 255 + 0.5)
        self._a255 = <uint8_t>(a * 255 + 0.5)
        return self

    cpdef Color set_rgba255(self, uint8_t r, uint8_t g, uint8_t b, uint8_t a):  # type: (int, int, int, int) -> Color
        self._r1 = r / 255.0
        self._g1 = g / 255.0
        self._b1 = b / 255.0
        self._a1 = a / 255.0
        self._r255 = r
        self._g255 = g
        self._b255 = b
        self._a255 = a
        return self
    # endregion

    # region constructors
    cpdef Color from_1(self, double r, double g, double b, double a = 1):  # type: (float, float, float, float) -> Color
        cdef c = Color()
        c.set_rgba1(r, g, b, a)
        return c

    cpdef from_255(self, uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255):  # type: (int, int, int, int) -> Color
        cdef c = Color()
        c.set_rgba255(r, g, b, a)
        return c
    # endregion

    # region utility
    cpdef Color copy(self):  # type: () -> Color
        cdef c = Color()
        c.set_rgba1(*self.get_rgba1())
        return c
    # endregion


cpdef Color fade(Color a, Color b, double t):  # type: (Color, Color, float) -> Color
    cdef double ar, ag, ab, aa
    cdef double br, bg, bb, ba

    ar, ag, ab, aa = a.get_rgba1()
    br, bg, bb, ba = b.get_rgba1()

    return Color().from_1(
        ar + (br - ar) * t,
        ag + (bg - ag) * t,
        ab + (bb - ab) * t,
        aa + (ba - aa) * t,
    )


cpdef tuple c_255_to_1(uint8_t r, uint8_t g, uint8_t b):  # type: (float, float, float) -> tuple[float, float, float]
    return r / 255.0, g / 255.0, b / 255.0
