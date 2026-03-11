from ._cvectors import Vec2


def calculate_launch_angle(
        position_delta: Vec2,
        target_velocity: Vec2,
        target_acceleration: Vec2,
        launch_speed: float,
        recalculate: int = 10,
        aim_type: str = "low",
        g: float = 9.81
) -> tuple[Vec2, float, Vec2]:
    """
    :param position_delta: the position delta between cannon and target
    :param target_velocity: the current velocity of the target, pass empty Vec2 if no velocity is known
    :param target_acceleration: the current acceleration of the target, pass empty Vec2 if no velocity is known
    :param launch_speed: the projectile muzzle speed
    :param recalculate: how often the position is being recalculated, basically a precision parameter
    :param aim_type: either "high" - "h" or "low" - "l". Defines if the lower or higher curve should be aimed for
    :param g: gravitation inflicted on target
    :return: where to aim, tof, predicted position
    """