"""
_island_perks.py
05. March 2026

an Island that can Move

Author:
Nilusink
"""
from ._island import Island
from ..logic import coord_t, convert_coord, Vec2


def create_moving_island(
        island: Island,
        offset: coord_t,
        time: float
) -> Island:
    """
    Takes any island and makes it move
    """
    offset = convert_coord(offset, Vec2)

    island.curr_move_pos = 0  # 0-2, current position of movement

    original_update = island.update
    original_position = island.position

    def move_island(delta: float) -> None:
        # count up to 2 (0-1 = up, 1-2 = down)
        if island.curr_move_pos < 2:
            island.curr_move_pos += delta / time

        else:
            # reset to 0 and reset island position to prohibit drift over time
            island.curr_move_pos = 0
            island.position = original_position

        # change islands velocity depending on movement direction
        if island.curr_move_pos <= 1:
            island.velocity = offset / time

        else:
            island.velocity = offset / -time

        # call actual island update function
        return original_update(delta)

    island.update = move_island
    return island
