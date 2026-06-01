"""
Approximates inertial behavior of a value.

Can be used for both angular and linear movements.

| ``Path``: amoginarium/shared/utility/_physics_estimations/_inertial_value.pxd
| ``Project``: amoginarium
| ``Created``: 01.06.2026
| ``Authors``: Nilusink
"""


cdef class InertialValue:
    cdef double _value, vel, inertia, max_velocity, max_acceleration, friction

    cpdef double update(self, double control_input, double dt)

    cpdef double get_value(self)
