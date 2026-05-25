"""
Base track class.

Path: amoginarium/shared/utility/_tracks/_base_track.pxd
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from libc.stdint cimport int8_t

from .._cvectors cimport Vec2
from ._ctrack_enums cimport TrackClassification


cdef class BaseTrack:

    cdef double sx, sy

    cdef double g
    cdef double x, y
    cdef Vec2 vel
    cdef Vec2 acc
    cdef double last_update

    cdef int8_t _track_quality
    cdef int8_t _track_state

    cdef public TrackClassification track_classification

    cpdef increment_time(self, double dt)

    cpdef reset(self)
    cpdef set_size(self, double x, double y)
    cpdef initialize(self, double x, double y, double vx, double vy, double g)
    cdef predict(self, double dt)
    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    )
    cdef inline update_classification(self)
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
