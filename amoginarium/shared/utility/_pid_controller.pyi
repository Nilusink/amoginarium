class PIDController:
    def __init__(self, p: float, i: float, d: float) -> None: ...
    def update(self, error: float, double: float) -> float:
        """update the PID controller"""
