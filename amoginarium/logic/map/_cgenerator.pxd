"""
Cython functions for the map generator.

| Path: amoginarium/logic/map/_cgenerator.pxd
| Project: amoginarium
| Created: 18.05.2026
| Authors: Nilusink
"""


cpdef int array_get(object array, object pos, object default)

cpdef bint iterate_chunk(
    double[:, :] chunk,
    int i,
    int n_steps
)
