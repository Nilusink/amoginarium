"""
amoginarium/collision_detection/_collision_detection.py

Project: amoginarium
Created: 01.04.2026
Authors: LukasKrah
"""


def collision_detection_aabb_aabb_minkowski_raycast(
        self_size: tuple[float, float],
        self_position_old: tuple[float, float],
        self_position_new: tuple[float, float],
        other_size: tuple[float, float],
        other_position_old: tuple[float, float],
        other_position_new: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    self_dx = self_position_new[0] - self_position_old[0]
    self_dy = self_position_new[1] - self_position_old[1]

    other_dx = other_position_new[0] - other_position_old[0]
    other_dy = other_position_new[1] - other_position_old[1]

    rel_dx = self_dx - other_dx
    rel_dy = self_dy - other_dy

    m_left = other_position_old[0] - self_size[0]
    m_top = other_position_old[1] - self_size[1]
    m_right = other_position_old[0] + other_size[0]
    m_bottom = other_position_old[1] + other_size[1]

    def get_intersection_times(start: float, delta: float, b_min: float, b_max: float) -> tuple[float, float]:
        if delta == 0:
            if b_min <= start <= b_max:
                return -float('inf'), float('inf')
            return float('inf'), -float('inf')

        t1 = (b_min - start) / delta
        t2 = (b_max - start) / delta
        return min(t1, t2), max(t1, t2)

    tx_min, tx_max = get_intersection_times(self_position_old[0], rel_dx, m_left, m_right)
    ty_min, ty_max = get_intersection_times(self_position_old[1], rel_dy, m_top, m_bottom)

    t_entry = max(tx_min, ty_min)
    t_exit = min(tx_max, ty_max)

    if t_entry <= t_exit and t_exit >= 0 and t_entry <= 1.0:
        t = max(0.0, t_entry)

        self_impact = (
            self_position_old[0] + self_dx * t,
            self_position_old[1] + self_dy * t
        )
        other_impact = (
            other_position_old[0] + other_dx * t,
            other_position_old[1] + other_dy * t
        )

        return self_impact, other_impact

    return None