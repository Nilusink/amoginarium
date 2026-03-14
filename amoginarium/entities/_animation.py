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
from ..shared import global_vars, HasPosition
from ..base._textures import textures
from ..base._groups import Updated, Drawn
from ..logic import Vec2, coord_t, convert_coord
from ._base_entity import VisibleBaseEntity


class Animation(VisibleBaseEntity):
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
        self._size = convert_coord(size, Vec2)
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
        self.add(Updated, Drawn)
        self._playing = True

    def stop(self) -> None:
        # self.kill()
        self.remove(Updated, Drawn)
        self._playing = False

    def update(self, delta):
        self._current_t -= delta
        if self._current_t <= 0:
            if (self._current_image + 1) >= len(self._textures):
                if self._loop:
                    self._current_image = 0

                else:
                    self.stop()

            else:
                self._current_image += 1

            self._current_t = self._delay

    def gl_draw(self) -> None:
        if self._current_image >= len(self._textures):
            self.stop()
            return

        texture = self._textures[self._current_image]

        renderer.draw_textured_quad(
            texture,
            self.position - Updated.world_position - self._size / 2,
            self._size
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
    # # TODO: convert to entity / gl_draw
    # if position is ... and position_reference is ...:
    #     raise ValueError("position and position_reference weren't given")
    #
    # def inner():
    #     for size, texture in zip(sizes, textures):
    #         if position_reference is not ...:
    #             position = position_reference.world_position
    #
    #         position -= size / 2
    #
    #         key = global_vars.set_in_loop(
    #             renderer.draw_textured_quad,
    #             texture,
    #             position.xy,
    #             size.xy
    #         )
    #
    #         time.sleep(delay)
    #         global_vars.reset_in_loop(key)
    #
    # Thread(target=inner).start()


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
            self.load_textures()

        if self._sound_effect is not ...:
            self._sound_effect().play()

        Animation(
            self._textures,
            size,
            delay,
            position,
            position_reference,
        ).play()


# constant animations
explosion = ImageAnimation("explosion")
