"""
Approximates inertial behavior of a value.

Can be used for both angular and linear movements.

| ``Path``: amoginarium/shared/utility/_physics_estimations/_inertial_value.pyi
| ``Project``: amoginarium
| ``Created``: 01.06.2026
| ``Authors``: Nilusink
"""

import numpy as np

class InertialValue:
    def __init__(
        self,
        initial_value: float = 0,
        initial_velocity: float = 0,
        inertia: float = 0,
        max_velocity: float = np.inf,
        max_acceleration: float = np.inf,
        friction: float = 1,
    ) -> None:
        """
        Approximates inertial behavior of a _value.

        The system models a simple 1D inertial body:
        velocity is updated from control input (acceleration/force-like),
        then position is integrated from velocity.

        Can be used for both angular and linear movements.

        :param initial_value: starting value
        :param initial_velocity: starting velocity
        :param inertia: inertia of object
        :param max_velocity: max object velocity
        :param max_acceleration: max object acceleration
        :param friction: "slip" factor
        """

    def update(self, control_input: float, dt: float) -> float:
        """
        Integrate the system state using an external control input.

        :param control_input: External force/acceleration command applied to the system.
        :param dt: Time step in seconds.
        :return: Updated position (state value) after integration.
        """

    def get_value(self) -> float:
        """Get current system value."""

    @property
    def value(self) -> float:
        """Get current system value."""
