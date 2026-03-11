"""
_basic_animation.py
19. March 2024

An animation made from multiple images

Author:
Nilusink
"""
from threading import Thread
import typing as tp
import time

from ..audio import PresetEffect
from ..render_bindings import renderer
from ..shared import global_vars
from ..base._textures import textures
from ..logic import Vec2


def play_animation(
        sizes: tp.Iterable[Vec2],
        textures: tp.Iterable[int],
        position: Vec2 = ...,
        position_reference: object = ...,
        delay=.2
) -> None:
    """
    play an animation based on textures
    """
    # TODO: convert to entity / gl_draw
    if position is ... and position_reference is ...:
        raise ValueError("position and position_reference weren't given")

    def inner():
        for size, texture in zip(sizes, textures):
            if position_reference is not ...:
                position = position_reference.world_position

            position -= size / 2

            key = global_vars.set_in_loop(
                renderer.draw_textured_quad,
                texture,
                position.xy,
                size.xy
            )

            time.sleep(delay)
            global_vars.reset_in_loop(key)

    Thread(target=inner).start()


class ImageAnimation:
    """
    play an animation from a directory
    """
    _textures: list[int] = ...
    _sizes: list[Vec2] = ...

    def __init__(
            self,
            animation_scope: str,
            sound_effect: type[PresetEffect] = ...
    ) -> None:
        self._scope = animation_scope
        self._sound_effect = sound_effect

    def load_textures(self, size: Vec2 = None) -> None:
        """
        load all textures required for the animation
        """
        self._textures = []
        self._sizes = []
        for texture, size in textures.get_all_from_scope(self._scope):
            self._textures.append(texture)
            self._sizes.append(Vec2().from_cartesian(*size))

    def draw(
            self,
            delay=.2,
            size: Vec2 = ...,
            position: Vec2 = ...,
            position_reference: object = ...
    ) -> None:
        """
        play the recently loaded animation

        either position or position_reference have to be given
        """
        if self._textures is ...:
            self.load_textures()

        if self._sound_effect is not ...:
            self._sound_effect().play()

        play_animation(
            self._sizes if size is ... else len(self._sizes) * [size],
            self._textures,
            position,
            position_reference,
            delay
        )


# constant animations
explosion = ImageAnimation("explosion")
