"""
An animation made from multiple images.

| ``Path``: amoginarium/graphics/entities/_animation.py
| ``Project``: amoginarium
| ``Created``: 13.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from amoginarium import pv
from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared.utility import convert_coord, normalize_angle, RTD, Vec2

from ..textures import textures
from ._base_entity import BaseGraphicsEntity
from ._graphics_groups import Drawn_0

if tp.TYPE_CHECKING:
    from amoginarium.shared import HasFacing, HasPosition
    from amoginarium.shared.utility import coord_t


class Animation(BaseGraphicsEntity):
    """base animation class."""

    def __init__(
        self,
        textures: tp.Sequence[int],
        size: coord_t,
        delay: float,
        position: coord_t | EllipsisType = ...,
        position_reference: HasPosition | tp.Callable[[], Vec2] | EllipsisType = ...,
        position_offset: coord_t | EllipsisType = ...,
        rotation_reference: HasFacing | tp.Callable[[], Vec2] | EllipsisType = ...,
        rotation_offset: float | EllipsisType = ...,
        rotate_anchor: Vec2 | EllipsisType = ...,
        loop: bool = False,
        layer: int = 0,
    ) -> None:
        """
        :param textures: list of texture ids to play as an animation
        :param size: animation size
        :param delay: delay between animations
        :param position: fixed position in world
        :param position_reference: function or entity with position, will
            overwrite fixed position and update live
        :param position_offset: offset from position reference
        :param rotation_reference: function or entity with facing
        :param rotation_offset: fixed rotational offset
        :param rotate_anchor: rotate point, if unspecified size/2 will be used
        :param loop: loop animation
        """
        super().__init__()

        self._current_image = 0
        self._current_t = delay
        self._textures = textures
        self._size: Vec2 = convert_coord(size, Vec2)  # type: ignore
        self._delay = delay
        self._loop = loop

        if isinstance(position, EllipsisType):
            self._position: Vec2 | EllipsisType = ...

        else:
            self._position: Vec2 | EllipsisType = convert_coord(
                position, Vec2
            )  # ignore: type

        if isinstance(position_offset, EllipsisType):
            self._position_offset: Vec2 | EllipsisType = ...

        else:
            self._position_offset: Vec2 | EllipsisType = convert_coord(
                position_offset, Vec2
            )  # type: ignore

        self._position_reference = position_reference
        self._rotation_reference = rotation_reference
        self._rotation_offset = rotation_offset
        self._rotate_anchor = rotate_anchor

        self._playing = False
        self._layer = layer

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
    def rotation(self) -> float:
        """Rotation."""
        rot = 0

        # get rotation reference
        if not isinstance(self._rotation_reference, EllipsisType):
            if hasattr(self._rotation_reference, "facing"):
                rot += self._rotation_reference.facing.angle

            else:
                rot += self._rotation_reference()

        # add offset
        if not isinstance(self._rotation_offset, EllipsisType):
            rot += self._rotation_offset

        return normalize_angle(rot)

    @property
    def rotate_anchor(self) -> Vec2:
        """Image rotation anchor."""
        if isinstance(self._rotate_anchor, EllipsisType):
            return self._size / 2

        return self._rotate_anchor

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

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
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
            rotate_angle=self.rotation * RTD,
            rotate_anchor=self.rotate_anchor,
            layer=self._layer,
        )


def play_animation(
    sizes: tp.Sequence[Vec2],
    textures: tp.Sequence[int],
    position: Vec2 = ...,
    position_reference: HasPosition = ...,
    position_offset: coord_t = ...,
    delay=0.2,
) -> None:
    """
    Play an animation based on textures.
    """
    Animation(
        textures, sizes[0], delay, position, position_reference, position_offset
    ).play()


class ImageAnimation:
    """
    play an animation from a directory.
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
        Load all textures required for the animation.
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
        position_reference: HasPosition = ...,
        layer: int = 0,
    ) -> None:
        """
        Play the recently loaded animation.

        either position or position_reference have to be given
        """
        if self._textures is ...:
            self.load_textures()

        Animation(
            self._textures, size, delay, position, position_reference, layer=layer
        ).play()


# constant animations
explosion = ImageAnimation("explosion")
