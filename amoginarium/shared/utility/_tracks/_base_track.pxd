"""
Base track class.

Path: amoginarium/shared/utility/_tracks/_base_track.pxd
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from libc.stdint cimport int8_t

from .._cvectors cimport Vec2

cdef class BaseTrack:

    cdef double x, y
    cdef double vx, vy
    cdef double ax, ay
    cdef double last_update

    cdef int8_t _track_quality
    cdef int8_t _track_state

    cpdef increment_time(self, double dt)

    cpdef reset(self)
    cpdef initialize(self, double x, double y, double vx, double vy)
    cdef predict(self, double dt)
    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    )
    cpdef step(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    )
    cpdef Vec2 get_position(self)
    cpdef Vec2 get_velocity(self)
    cpdef Vec2 get_acceleration(self)
    cpdef Vec2 predict_future_position(self, double t)
    cpdef double get_speed(self)
    cpdef kill(self)
