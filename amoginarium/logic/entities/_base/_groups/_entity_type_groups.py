"""
amoginarium/logic/entities/_groups/_entity_type_groups.py

Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

import typing as tp

from amoginarium.shared.utility import Vec2
from amoginarium.shared import PositionedLogicEntityLike

from ._base_group import BaseGroup
from ._updated import Updated


class _Bullets(BaseGroup[PositionedLogicEntityLike]):
    """Group containing all active bullet entities."""
    __slots__ = ()


class _Walls(BaseGroup[PositionedLogicEntityLike]):
    """Group containing all static wall/collision entities."""
    __slots__ = ()


class _Players(BaseGroup[PositionedLogicEntityLike]):
    """Group containing all player entities and spawn logic."""
    __slots__ = ()

    _spawn_point: tp.ClassVar[Vec2 | None] = None

    @property
    def spawn_point(self) -> Vec2 | None:
        """
        Get the world-space player spawn point.
        :return: The calculated spawn point Vec2 or None if not set.
        """
        if _Players._spawn_point:
            return Updated.world_position + _Players._spawn_point

        return None

    @spawn_point.setter
    def spawn_point(self, point: Vec2) -> None:
        """
        Set the base spawn point.
        :param point: The Vec2 coordinates for the spawn point.
        """
        _Players._spawn_point = point

    def get_max_position(self) -> Vec2:
        """
        Calculate the maximum X-axis position among all players.
        :return: Vec2 representing the position of the rightmost player.
        """
        max_sprite = None
        max_x = -float('inf')

        for sprite in self.entities():
            px = sprite.position.x
            if px > max_x:
                max_x = px
                max_sprite = sprite

        return max_sprite.position.copy() if max_sprite else Vec2()

    def get_min_position(self) -> Vec2:
        """
        Calculate the minimum X-axis position among all players.
        :return: Vec2 representing the position of the leftmost player.
        """
        min_sprite = None
        min_x = float('inf')

        for sprite in self.entities():
            px = sprite.position.x
            if px < min_x:
                min_x = px
                min_sprite = sprite

        return min_sprite.position.copy() if min_sprite else Vec2().from_cartesian(float('inf'), float('inf'))

    def get_position_extremes(self) -> tuple[Vec2, Vec2]:
        """
        Get the minimum and maximum X-axis positions in a single pass.
        :return: A tuple of (min_pos, max_pos) Vec2 objects.
        """
        max_sprite = None
        min_sprite = None
        max_x = -float('inf')
        min_x = float('inf')

        for sprite in self.entities():
            px = sprite.position.x
            if px > max_x:
                max_x = px
                max_sprite = sprite
            if px < min_x:
                min_x = px
                min_sprite = sprite

        return (
            min_sprite.position.copy() if min_sprite else Vec2().from_cartesian(float('inf'), float('inf')),
            max_sprite.position.copy() if max_sprite else Vec2()
        )


Walls: tp.Final[_Walls] = _Walls()
Players: tp.Final[_Players] = _Players()
Bullets: tp.Final[_Bullets] = _Bullets()
