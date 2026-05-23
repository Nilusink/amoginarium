"""
Simple PID controller.

| Path: amoginarium/shared/utility/_pid_controller.pyx
| Project: amoginarium
| Created: 10.05.2026
| Authors: Nilusink
"""


cdef class PIDController:
    def __init__(self, double p, double i, double d):
        self.integral = 0
        self.prev_error = 0
        self.kp = p
        self.ki = i
        self.kd = d

        self._value = 0

    @property
    def value(self) -> float:
        return self._value

    cpdef set_value(self, double new_val):
        self._value = new_val

    cpdef double update_value(self, double new_val, double dt):
        return self.update(new_val - self._value, dt)

    cpdef double update(self, double error, double dt):
        cdef:
            double derivative
            double output

        if dt <= 1e-9:
            # self._value += error
            return self._value

        self.integral += error * dt

        derivative = (error - self.prev_error) / dt
        self.prev_error = error

        output = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )

        # apply PID output TO the value
        self._value += output * dt

        return self._value
