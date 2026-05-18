"""
Heck, I have no idea. A PID Controller, I guess.

Path: amoginarium/shared/utility/_pid_controller.pyi
Project: amoginarium
Created: 10.05.2026
Authors: Nilusink
"""

class PIDController:
    def __init__(self, p: float, i: float, d: float) -> None: ...
    def update(self, error: float, double: float) -> float:
        """update the PID controller"""
