"""
amoginarium/logic/entities/_groups/_updated.py

Project: amoginarium
Created: 25.01.2024
Authors: LukasKrah
"""

from amoginarium.shared.utility import Vec2

from ._base_group import BaseGroup


class _Updated(BaseGroup):
    world_position: Vec2
    pixel_per_meter: Vec2
    screen_size: Vec2

    def __init__(self, *args) -> None:
        self.world_position = Vec2()
        super().__init__(*args)

    def out_of_bounds_x(self, sprite, margin: float = 0) -> bool:
        return any([
            self.world_position.x + margin > sprite.position.x,
            sprite.position.x + margin > self.world_position.x + 1920
        ])

    def load_textures(self) -> None:
        """
        load all textures
        """
        # get the different types of entities
        types = tuple(set([s.__class__ for s in self.sprites()]))

        # load the textures for each different type
        for t in types:

            # only load textures if the type has a function
            # to load the textures
            if hasattr(t, "load_textures"):
                t.load_textures()

Updated = _Updated()