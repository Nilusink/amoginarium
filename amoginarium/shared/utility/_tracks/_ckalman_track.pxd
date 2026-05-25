"""
Implement 2D Kalman Filter tracking.

Path: amoginarium/shared/utility/_ckalman_track.pxd
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from ._base_track cimport BaseTrack


cdef class KalmanTrack2D(BaseTrack):

    # diagonal covariance approximation
    # (much cheaper than full matrix)
    cdef double px
    cdef double py

    cdef double pvx
    cdef double pvy

    cdef double pax
    cdef double pay

    cdef double prev_vx
    cdef double prev_vy

    cdef double alpha

    # tuning
    cdef double measurement_noise
    cdef double process_noise

    cpdef reset(self)
    cpdef initialize(self, double x, double y, double vx, double vy)
    cdef predict(self, double dt)
    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    )
