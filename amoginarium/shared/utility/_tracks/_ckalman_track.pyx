"""
Implement 2D Kalman Filter tracking.

Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_ckalman_track.pyx
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from ._base_track cimport BaseTrack


cdef class KalmanTrack2D(BaseTrack):
    """
    Constant-acceleration Kalman filter.

    State:
        x, y,
        vx, vy,
        ax, ay

    Measurements:
        mx, my
    """

    def __cinit__(
        self,
        double measurement_noise=5.0,
        double process_noise=0.1,
        double alpha=0.05
    ):
        self.measurement_noise = measurement_noise
        self.process_noise = process_noise
        self.alpha = alpha

        self.reset()

    cpdef reset(self):
        self.x = 0
        self.y = 0

        self.vx = 0
        self.vy = 0

        self.ax = 0
        self.ay = 0

        # previous velocity for acceleration estimation
        self.prev_vx = 0
        self.prev_vy = 0

        self.px = 1000
        self.py = 1000

        self.pvx = 1000
        self.pvy = 1000

        self.pax = 1000
        self.pay = 1000

    cpdef initialize(self, double x, double y, double vx, double vy):
        self.x = x
        self.y = y

    cdef predict(self, double dt):
        """
        Predict next state.
        """

        cdef double dt2 = 0.5 * dt * dt

        # store velocity before update
        self.prev_vx = self.vx
        self.prev_vy = self.vy

        # motion model
        self.x += self.vx * dt + self.ax * dt2
        self.y += self.vy * dt + self.ay * dt2

        self.vx += self.ax * dt
        self.vy += self.ay * dt

        # covariance growth (kept simple)
        self.px += self.process_noise
        self.py += self.process_noise
        self.pvx += self.process_noise
        self.pvy += self.process_noise
        self.pax += self.process_noise
        self.pay += self.process_noise

    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        """
        Correct filter using measured position.
        """

        cdef double kx, ky
        cdef double dx, dy

        cdef double dvx, dvy

        # POSITION UPDATE
        kx = self.px / (self.px + self.measurement_noise)
        ky = self.py / (self.py + self.measurement_noise)

        dx = mx - self.x
        dy = my - self.y

        self.x += kx * dx
        self.y += ky * dy

        self.px *= (1.0 - kx)
        self.py *= (1.0 - ky)

        # VELOCITY ESTIMATE (from measurement correction)
        # this stabilizes velocity BEFORE computing acceleration
        self.vx += self.alpha * dx
        self.vy += self.alpha * dy

        # acceleration from velocity delta
        dvx = (self.vx - self.prev_vx) / dt
        dvy = (self.vy - self.prev_vy) / dt

        self.ax = 0.9 * self.ax + 0.1 * dvx
        self.ay = 0.9 * self.ay + 0.1 * dvy

        # decay (prevents runaway)
        self.ax *= 0.95
        self.ay *= 0.95
