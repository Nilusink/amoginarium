"""
_pid_controller.pyx
10.05.2026

simple PID controller

Author:
Nilusink
"""


cdef class PIDController:
    def __init__(self, double p, double i, double d):
        self.integral = 0
        self.prev_error = 0
        self.kp = p
        self.ki = i
        self.kd = d

    cpdef double update(self, double error, double dt):
        self.integral += error * dt

        derivative = (error - self.prev_error) / dt
        self.prev_error = error

        return (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
