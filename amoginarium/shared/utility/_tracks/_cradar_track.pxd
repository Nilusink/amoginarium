"""
Radar track.

Track type where track is updated by position + velocity

Path: amoginarium/shared/utility/_tracks/_cradar_track.pxd
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from ._base_track cimport BaseTrack


cdef class RadarTrack2D(BaseTrack):

    cdef double px, py
    cdef double pvx, pvy

    cdef double prev_vx, prev_vy

    cdef double measurement_noise_pos
    cdef double measurement_noise_vel

    cpdef reset(self)
    cpdef initialize(self, double x, double y, double vx, double vy)
    cdef predict(self, double dt)
    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    )
