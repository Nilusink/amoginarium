"""
Approximates inertial behavior of a _value.

Can be used for both angular and linear movements.

| ``Path``: amoginarium/shared/utility/_physics_estimations/_inertial_value.pyx
| ``Project``: amoginarium
| ``Created``: 01.06.2026
| ``Authors``: Nilusink
"""

from libc.math cimport exp

import numpy as np


cdef inline double clamp(double val, double min_val, double max_val):
    """Clamp value between min_val and max_val."""
    if val < min_val:
        return min_val

    elif val > max_val:
        return max_val

    return val


cdef class InertialValue:
    def __init__(
        self,
        initial_value: float = 0,
        initial_velocity: float = 0,
        inertia: float = 0,
        max_velocity: float = np.inf,
        max_acceleration: float = np.inf,
        friction: float = 1,
    ):
        self._value = initial_value
        self._vel = initial_velocity
        self.inertia = inertia
        self.max_velocity = max_velocity
        self.max_acceleration = max_acceleration
        self.friction = friction

    cpdef double update(self, double control_input, double dt):
        cdef double accel

        if dt <= 1e-9:
            return self._value

        if abs(control_input) < 1e-9:
            self._vel = 0
            return self._value

        # Newton-style dynamics:
        # F = m * a  -> a = F / m
        # inertia acts as mass
        accel = clamp(
            control_input / self.inertia,
            -self.max_acceleration,
            self.max_acceleration,
        )

        # integrate velocity
        self._vel += accel * dt
        self._vel *= exp(-self.friction * dt)

        # velocity limiting (acts like motor saturation)
        if self._vel > self.max_velocity:
            self._vel = self.max_velocity
        elif self._vel < -self.max_velocity:
            self._vel = -self.max_velocity

        # integrate position
        self._value += self._vel * dt

        return self._value

    cpdef double get_value(self):
        return self._value

    cpdef double get_velocity(self):
        return self._vel

    @property
    def value(self) -> float:
        return self._value

    @property
    def velocity(self) -> float:
        return self._vel
