"""
Specialized group for tracking entities that require regular update ticks.

Includes boundary checking and bulk texture loading utility methods.

Path: amoginarium/logic/entities/_base/_groups/_updated.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

import typing as tp

from amoginarium import pv
from amoginarium.shared import PositionedLogicEntityLike
from amoginarium.shared.utility import Vec2

from ._base_group import BaseGroup


class _Updated(BaseGroup[PositionedLogicEntityLike]):
    """
    A specialized group for entities that require regular logic updates.
    """

    __slots__ = ("world_position",)
    world_position: Vec2

    def __init__(self, *args) -> None:
        """
        Initializes the updated group with a default world position.
        :param args: Arguments passed to the BaseGroup constructor.
        """
        self.world_position = Vec2()
        super().__init__(*args)

    def out_of_bounds_x(
        self, sprite: PositionedLogicEntityLike, margin: float = 0
    ) -> bool:
        """
        Checks if a sprite is outside the horizontal bounds
        :param sprite: The entity to check.
        :param margin: Additional padding for the boundary check.
        :return: True if the sprite is out of bounds, False otherwise.
        """
        return any(
            [
                self.world_position.x + margin > sprite.position.x,
                sprite.position.x + margin
                > self.world_position.x + pv.global_vars.get_screen_size().x,
            ]
        )

    def load_textures(self) -> None:
        """
        Iterates through all unique entity types in the group and triggers
        their texture loading logic if available.
        """
        # get the different types of entities
        types = tuple({s.__class__ for s in self.entities()})

        # load the textures for each different type
        for t in types:
            # only load textures if the type has a function
            # to load the textures
            if hasattr(t, "load_textures"):
                t.load_textures()


Updated: tp.Final[_Updated] = _Updated()
