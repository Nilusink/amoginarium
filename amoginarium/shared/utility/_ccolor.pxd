from libc.stdint cimport uint8_t

from amoginarium.shared.utility cimport Color

cdef class Color:
    cdef public double _r1, _g1, _b1, _a1
    cdef public uint8_t _r255, _g255, _b255, _a255

    # region c functions
    cpdef tuple get_rgb1(self)

    cpdef tuple get_rgb255(self)

    cpdef tuple get_rgba1(self)

    cpdef tuple get_rgba255(self)

    cpdef Color set_rgb1(self, double r, double g, double b)  # type: (float, float, float) -> Color

    cpdef Color set_rgb255(self, uint8_t r, uint8_t g, uint8_t b)  # type: (int, int, int) -> Color

    cpdef Color set_rgba1(self, double r, double g, double b, double a)  # type: (float, float, float, float) -> Color

    cpdef Color set_rgba255(self, uint8_t r, uint8_t g, uint8_t b, uint8_t a)  # type: (int, int, int, int) -> Color
    # endregion

    # region constructors
    cpdef Color from_1(self, double r, double g, double b, double a = *)  # type: (float, float, float, float) -> Color

    cpdef Color from_255(self, uint8_t r, uint8_t g, uint8_t b, uint8_t a = *)  # type: (int, int, int, int) -> Color
    # endregion

    # region utility
    cpdef Color copy(self)  # type: () -> Color
    # endregion
