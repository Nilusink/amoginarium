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

from libc.math cimport sqrt


cdef class KalmanTrack2D:
    """
    Constant-acceleration Kalman filter.

    State:
        x, y,
        vx, vy,
        ax, ay

    Measurements:
        mx, my
    """

    # state
    cdef double x
    cdef double y

    cdef double vx
    cdef double vy

    cdef double ax
    cdef double ay

    # diagonal covariance approximation
    # (much cheaper than full matrix)
    cdef double px
    cdef double py

    cdef double pvx
    cdef double pvy

    cdef double pax
    cdef double pay

    # tuning
    cdef double measurement_noise
    cdef double process_noise

    def __cinit__(
        self,
        double measurement_noise=5.0,
        double process_noise=0.1
    ):
        self.measurement_noise = measurement_noise
        self.process_noise = process_noise

        self.reset()

    cpdef reset(self):
        self.x = 0
        self.y = 0

        self.vx = 0
        self.vy = 0

        self.ax = 0
        self.ay = 0

        # initial uncertainty
        self.px = 1000
        self.py = 1000

        self.pvx = 1000
        self.pvy = 1000

        self.pax = 1000
        self.pay = 1000

    cpdef initialize(self, double x, double y):
        self.x = x
        self.y = y

    cpdef predict(self, double dt):
        """
        Predict next state.
        """

        cdef double dt2 = dt * dt * 0.5

        # position
        self.x += self.vx * dt + self.ax * dt2
        self.y += self.vy * dt + self.ay * dt2

        # velocity
        self.vx += self.ax * dt
        self.vy += self.ay * dt

        # covariance growth
        self.px += self.process_noise
        self.py += self.process_noise

        self.pvx += self.process_noise
        self.pvy += self.process_noise

        self.pax += self.process_noise
        self.pay += self.process_noise

    cpdef update(self, double mx, double my):
        """
        Correct filter using measured position.
        """

        cdef double kx
        cdef double ky

        cdef double dx
        cdef double dy

        #
        # POSITION UPDATE
        #

        kx = self.px / (self.px + self.measurement_noise)
        ky = self.py / (self.py + self.measurement_noise)

        dx = mx - self.x
        dy = my - self.y

        self.x += kx * dx
        self.y += ky * dy

        self.px *= (1.0 - kx)
        self.py *= (1.0 - ky)

        #
        # VELOCITY UPDATE
        #

        self.vx += dx * 0.1
        self.vy += dy * 0.1

        #
        # ACCELERATION UPDATE
        #

        self.ax += dx * 0.01
        self.ay += dy * 0.01

    cpdef step(self, double mx, double my, double dt):
        """
        Full filter step.
        """
        self.predict(dt)
        self.update(mx, my)

    cpdef tuple get_position(self):
        return self.x, self.y

    cpdef tuple get_velocity(self):
        return self.vx, self.vy

    cpdef tuple get_acceleration(self):
        return self.ax, self.ay

    cpdef tuple predict_future_position(self, double t):
        """
        Predict target position t seconds into future.
        """

        cdef double t2 = 0.5 * t * t

        return (
            self.x + self.vx * t + self.ax * t2,
            self.y + self.vy * t + self.ay * t2
        )

    cpdef double get_speed(self):
        return sqrt(self.vx * self.vx + self.vy * self.vy)
