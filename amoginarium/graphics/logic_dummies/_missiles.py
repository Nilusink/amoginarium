"""
_missiles.py
05.05.2026

Missile dummies

Author:
Nilusink
"""

import math as m

from amoginarium.base._textures import textures
from amoginarium.shared.utility import Vec2, coord_t
from amoginarium.shared import MissileCIDs

from ..render_bindings import renderer
from ..entities import Animation
from ._bullet import BulletDummy


class MultiStageMissileDummy(BulletDummy):
    """
    ``flags[14]``: thrust active
    """
    _CID = MissileCIDs.multi_stage

    _animation_scope: str = "flame"
    _animation_size: tuple[int, int] = (16, 16)
    _animation_textures: list[int] = ...

    @classmethod
    def load_textures(cls) -> None:
        super().load_textures()

        if cls._animation_textures is not ...:
            return

        cls._animation_textures = [
            t[0]
            for t in textures.get_all_from_scope(
                cls._animation_scope, cls._animation_size, pixel_perfect=True
            )
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._animation = Animation(
            self._animation_textures,
            self._animation_size,
            0.05,
            position_reference=self._flame_position,
            rotation_reference=self,
            rotation_offset=-3.14159265/2,
            loop=True,
            layer=2
        )

    def _flame_position(self) -> Vec2:
        """flame position for animation"""
        return self.pos + Vec2().from_polar(
            self.facing.angle,
            self.size.x / 5
        )

    def _kill(self) -> None:
        self._animation.stop()
        super()._kill()

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        # update animation
        if not self._get_bit("flags", 14):
            self._show_trace = False

            if self._animation.playing:
                self._animation.stop()

        elif self._get_bit("flags", 14):
            self._show_trace = True

            if not self._animation.playing:
                self._animation.play()

        # update trace and bullet
        super()._gl_draw(delta_cal, layer)


class GuidedMultiStageMissileDummy(MultiStageMissileDummy):
    _CID = MissileCIDs.guided_multi_stage

    _animation_size: tuple[int, int] = (32, 32)

    def _flame_position(self) -> Vec2:
        """flame position for animation"""
        return self.pos + Vec2().from_polar(
            self.facing.angle,
            self.size.x / 2.1 + self._animation_size[0] / 2
        )
