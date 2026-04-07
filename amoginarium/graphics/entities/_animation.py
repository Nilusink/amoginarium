"""
_basic_animation.py
19. March 2024

An animation made from multiple images

Author:
Nilusink
"""
import typing as tp

from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared.utility import Vec2, coord_t, convert_coord
from amoginarium.shared import HasPosition
from amoginarium.base._textures import textures
from amoginarium import pv

from ._graphics_groups import Drawn_0
from ._base_entity import BaseGraphicsEntity


class Animation(BaseGraphicsEntity):
    def __init__(
            self,
            textures: tp.Sequence[int],
            size: coord_t,
            delay: float,
            position: coord_t = ...,
            position_reference: HasPosition | tp.Callable[[], Vec2] = ...,
            position_offset: coord_t = ...,
            loop: bool = False
    ) -> None:
        super().__init__()

        self._current_image = 0
        self._current_t = delay
        self._textures = textures
        self._size: Vec2 = convert_coord(size, Vec2)
        self._delay = delay
        self._loop = loop
        self._position = convert_coord(position, Vec2) if position is not ... \
            else ...
        self._position_reference = position_reference
        self._position_offset = convert_coord(position_offset, Vec2) \
            if position_offset is not ... else ...

        self._playing = False

    @property
    def position(self) -> Vec2:
        if self._position is ...:
            if hasattr(self._position_reference, "position"):
                pos = self._position_reference.position

            else:
                pos = self._position_reference()

        else:
            pos = self._position

        if self._position_offset is ...:
            return pos

        return pos + self._position_offset

    @property
    def playing(self) -> bool:
        return self._playing

    def play(self) -> None:
        if self._playing:
            return

        self._current_image = 0
        self._current_t = self._delay
        self.add(Drawn_0)
        self._playing = True

    def stop(self) -> None:
        self.kill()
        # self.remove(Drawn)
        self._playing = False
        del self

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        self._current_t -= delta_cal
        if self._current_t <= 0:
            if (self._current_image + 1) >= len(self._textures):
                if self._loop:
                    self._current_image = 0

                else:
                    self.stop()

            else:
                self._current_image += 1

            self._current_t = self._delay

        if self._current_image >= len(self._textures):
            self.stop()
            return

        texture = self._textures[self._current_image]

        renderer.draw_textured_quad(
            texture,
            self.position - (self._size / 2) - pv.global_vars.get_world_position(),
            self._size,
            pixel_perfect=True
        )


def play_animation(
        sizes: tp.Sequence[Vec2],
        textures: tp.Sequence[int],
        position: Vec2 = ...,
        position_reference: HasPosition = ...,
        position_offset: coord_t = ...,
        delay=.2
) -> None:
    """
    play an animation based on textures
    """
    Animation(
        textures,
        sizes[0],
        delay,
        position,
        position_reference,
        position_offset
    ).play()


class ImageAnimation:
    """
    play an animation from a directory
    """
    _textures: list[int] = ...
    _sizes: list[Vec2] = ...

    def __init__(
            self,
            animation_scope: str,
    ) -> None:
        self._scope = animation_scope

    def load_textures(self, size: Vec2 = None) -> None:
        """
        load all textures required for the animation
        """
        self._textures = []
        self._sizes = []
        for texture, size in textures.get_all_from_scope(self._scope, size):
            self._textures.append(texture)
            self._sizes.append(Vec2().from_cartesian(*size))

    def draw(
            self,
            delay,
            size: Vec2,
            position: Vec2 = ...,
            position_reference: HasPosition = ...
    ) -> None:
        """
        play the recently loaded animation

        either position or position_reference have to be given
        """
        if self._textures is ...:
            self.load_textures() #Vec2().from_cartesian(256, 256))

        Animation(
            self._textures,
            size,
            delay,
            position,
            position_reference,
        ).play()


# constant animations
explosion = ImageAnimation("explosion")
