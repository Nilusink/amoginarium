"""
Missile dummies.

Path: amoginarium/graphics/logic_dummies/_missiles.py
Project: amoginarium
Created: 05.05.2026
Authors: Nilusink
"""

import math
import typing as tp
from time import perf_counter
from types import EllipsisType

from amoginarium.shared import MissileCIDs
from amoginarium.shared.utility import Vec2

from ..entities import Animation
from ..textures import textures
from ._bullet import BulletDummy


class MultiStageMissileDummy(BulletDummy):
    """
    ``flags[14]``: thrust active.
    """

    _CID = MissileCIDs.multi_stage

    _animation_scope: str = "flame"
    _animation_size: tuple[int, int] = (16, 16)
    _animation_textures: list[int] = ...

    _image_animation_delay: float = 1 / 12
    _image_scope: tp.ClassVar[str | None] = None
    _image_textures: list[int] = ...

    @classmethod
    def load_textures(cls) -> None:
        super().load_textures()

        if cls.__dict__.get("_animation_textures", ...) is not ...:
            return

        if cls._image_scope is not None:
            cls._image_textures = [
                t[0]
                for t in textures.get_all_from_scope(
                    cls._image_scope, cls._default_size, pixel_perfect=True
                )
            ]

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
            rotation_offset=-math.pi / 2,
            loop=True,
            layer=2,
        )

    @classmethod
    def bullet_image(cls) -> int:
        image_textures = cls._image_textures
        if not isinstance(image_textures, EllipsisType):
            n_textures = len(image_textures)
            return image_textures[
                int((perf_counter() / cls._image_animation_delay) % n_textures)
            ]

        return super().bullet_image()

    def _flame_position(self) -> Vec2:
        """Flame position for animation."""
        return self.pos + Vec2().from_polar(self.facing.angle, self.size.x / 5)

    def _kill(self) -> None:
        self._animation.stop()
        super()._kill()

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
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
        """Flame position for animation."""
        return self.pos + Vec2().from_polar(
            self.facing.angle, self.size.x / 2.1 + self._animation_size[0] / 2
        )


class MultiThrusterMissileDummy(MultiStageMissileDummy):
    _CID = MissileCIDs.multi_thruster


class PlayerControlledMissileDummy(GuidedMultiStageMissileDummy):
    _CID = MissileCIDs.player_controlled
    _animation_size: tuple[int, int] = (48, 48)
