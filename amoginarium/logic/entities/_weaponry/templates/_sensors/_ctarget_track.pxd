"""
Target tracks.

Documents target position, velocity & acceleration over time.

Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_ctarget_track.pxd
Project: amoginarium
Created: 21.05.2026
Authors: Nilusink
"""

from libc.stdint cimport int8_t
from libcpp.vector cimport vector

from amoginarium.shared.utility cimport Vec2


cdef struct simple_vec2



cdef class TargetTrack:
    # private
    cdef int8_t _track_quality
    cdef int8_t _track_state

    cdef vector[simple_vec2] pos_history
    cdef vector[simple_vec2] vel_history

    cdef public Vec2 position
    cdef public Vec2 velocity
    cdef public Vec2 acceleration

    cpdef add_point(self, Vec2 position, double dt)
