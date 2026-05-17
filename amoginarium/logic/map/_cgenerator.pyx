"""
Cython functions for the map generator.

Path: amoginarium/logic/map/_cgenerator.pyx
Project: amoginarium
Created: 18.05.2026
Authors: Nilusink
"""

from libc.stdint cimport uint8_t

import numpy as np


cpdef int array_get(object array, object pos, object default):
    cdef int x, y
    x = pos[1]
    y = pos[0]

    if 0 <= y < array.shape[0] and 0 <= x < array.shape[1]:
        return array[y, x]

    return default


# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: cdivision=True
cdef inline float get_val(
    double[:, :] arr,
    int x,
    int y,
    int sx,
    int sy
) nogil:
    if 0 <= x < sx and 0 <= y < sy:
        return arr[x, y]
    return -1.0


# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: cdivision=True
cpdef bint iterate_chunk(
    double[:, :] chunk,
    int i,
    int n_steps
):
    cdef:
        int col, row
        int sx = chunk.shape[0]
        int sy = chunk.shape[1]

        double[:, :] old_map
        double curr_value
        double total
        int count
        double val

    if i < n_steps:
        old_map = np.array(chunk, copy=True)

        for col in range(sx):
            for row in range(sy):

                curr_value = old_map[col, row]

                # own value weighted 4x
                total = curr_value * 4.0
                count = 4

                val = get_val(old_map, col - 1, row, sx, sy)
                if val >= 0:
                    total += val
                    count += 1

                val = get_val(old_map, col + 1, row, sx, sy)
                if val >= 0:
                    total += val
                    count += 1

                val = get_val(old_map, col, row - 1, sx, sy)
                if val >= 0:
                    total += val
                    count += 1

                val = get_val(old_map, col, row + 1, sx, sy)
                if val >= 0:
                    total += val
                    count += 1

                chunk[col, row] = total / count

        return False

    else:
        for col in range(sx):
            for row in range(sy):
                chunk[col, row] = chunk[col, row] >= 0.5

        return True

