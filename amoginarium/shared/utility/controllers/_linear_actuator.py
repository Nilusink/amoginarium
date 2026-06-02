from __future__ import annotations

import numpy as np
from types import EllipsisType


def calculate_actuator(
    dt: float,
    error: float,
    velocity: float,
    max_acceleration: float,
    max_brake_acc: float | EllipsisType = ...,
    *,
    safety_margin: float = 1.1
) -> float:
    """
    Calculate control value for a 1D actuator.

    :param dt: approximate time delta until next call
    :param error: error to target
    :param velocity: current object velocity
    :param max_acceleration: max accelerational value
    :param max_brake_acc: max breaking acceleration, if not given equal to acc
    :param safety_margin: minimum abort range multiplier
    :return: control value (-max_acc, +max_acc)
    """
    # calculate minimum required braking distance
    brake_acc = abs(
        max_acceleration if isinstance(max_brake_acc, EllipsisType)
        else max_brake_acc
    )
    min_brake_range = abs(velocity) / brake_acc

    if abs(error) <= min_brake_range * safety_margin:  # braking
        return -np.sign(velocity) * brake_acc

    # accelerating
    return np.sign(error) * max_acceleration

    return 0
