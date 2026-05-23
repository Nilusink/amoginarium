"""
Heck, I have no idea. A PID Controller, I guess.

| Path: amoginarium/shared/utility/_pid_controller.pyi
| Project: amoginarium
| Created: 10.05.2026
| Authors: Nilusink
"""

class PIDController:
    def __init__(self, p: float, i: float, d: float) -> None: ...
    @property
    def value(self) -> float:
        """Get current PID controller value."""

    def set_value(self, new_val: float) -> None:
        """Set current value."""

    def update_value(self, new_val: float, dt: float) -> float:
        """Update PID controller based on absolute value."""

    def update(self, error: float, dt: float) -> float:
        """Update the PID controller based on relative error."""
