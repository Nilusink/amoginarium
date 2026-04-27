"""
amoginarium/logic/entities/_groups/_entity_type_groups.py

Project: amoginarium
Created: 25.01.2024
Authors: LukasKrah
"""

import numpy as np

from amoginarium.shared.utility import Vec2

from ._base_group import BaseGroup
from ._updated import Updated


class _Bullets(BaseGroup):
    """Group with all bullets"""
    ...


class _Walls(BaseGroup):
    """Group with all walls"""
    ...


class _Players(BaseGroup):
    """Group with all players"""
    _spawn_point: Vec2 = None

    @property
    def spawn_point(self) -> Vec2 | None:
        """
        player spawn point
        """
        if self._spawn_point:
            return Updated.world_position.copy() + self._spawn_point.copy()

        return None

    @spawn_point.setter
    def spawn_point(self, point: Vec2) -> None:
        self._spawn_point = point

    def get_max_position(self) -> Vec2:
        max_pos = Vec2()
        for sprite in self.sprites():
            if sprite.position.x > max_pos.x:
                max_pos = sprite.position.copy()

        return max_pos

    def get_min_position(self) -> Vec2:
        min_pos = np.inf
        for sprite in self.sprites():
            if sprite.position.x < min_pos.x:
                min_pos = sprite.position.copy()

        return min_pos

    def get_position_extremes(self) -> tuple[Vec2, Vec2]:
        """
        get min and max positions

        :returns: min, max
        """
        max_pos = Vec2()
        min_pos = Vec2().from_cartesian(np.inf, np.inf)

        for sprite in self.sprites():
            if sprite.position.x > max_pos.x:
                max_pos = sprite.position.copy()

            if sprite.position.x < min_pos.x:
                min_pos = sprite.position.copy()

        return min_pos, max_pos


Walls = _Walls()
Players = _Players()
Bullets = _Bullets()
