"""
_pid_controller.pxd
10.05.2026

simple PID controller

Author:
Nilusink
"""


cdef class PIDController:
    cdef double kp, ki, kd, integral, prev_error

    cpdef double update(self, double error, double dt)
