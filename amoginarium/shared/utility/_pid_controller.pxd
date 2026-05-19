"""
_pid_controller.pxd
10.05.2026

simple PID controller

Author:
Nilusink
"""


cdef class PIDController:
    cdef double kp, ki, kd, integral, prev_error, _value
    cpdef set_value(self, double new_val)
    cpdef double update_value(self, double new_val, double dt)
    cpdef double update(self, double error, double dt)
