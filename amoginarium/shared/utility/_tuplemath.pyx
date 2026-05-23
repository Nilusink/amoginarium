"""
Fast tuple basic math operations.

| Path: amoginarium/shared/utility/_tuplemath.pyx
| Project: amoginarium
| Created: 03.04.2026
| Authors: LukasKrah
"""

cimport cython


cdef class _TupleMath:
    """
    A fast Cython implementation providing element-wise mathematical operations.
    """

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def add(self, tuple t1, tuple t2) -> tuple:
        cdef Py_ssize_t i
        cdef Py_ssize_t n = len(t1)
        return tuple([t1[i] + t2[i] for i in range(n)])

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def sub(self, tuple t1, tuple t2) -> tuple:
        cdef Py_ssize_t i
        cdef Py_ssize_t n = len(t1)
        return tuple([t1[i] - t2[i] for i in range(n)])

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def mul(self, tuple t1, tuple t2) -> tuple:
        cdef Py_ssize_t i
        cdef Py_ssize_t n = len(t1)
        return tuple([t1[i] * t2[i] for i in range(n)])

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def div(self, tuple t1, tuple t2) -> tuple:
        cdef Py_ssize_t i
        cdef Py_ssize_t n = len(t1)
        return tuple([t1[i] / t2[i] for i in range(n)])


TupleMath = _TupleMath()
