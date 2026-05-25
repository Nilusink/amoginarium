"""
Implements scrolling and parallax background systems.

| ``Path``: amoginarium/base/_scrolling_background.py
| ``Project``: amoginarium
| ``Created``: 26.01.2024
| ``Authors``: Nilusink
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic

from amoginarium import pv
from amoginarium.graphics.render_bindings import renderer
from amoginarium.graphics.textures import textures

if TYPE_CHECKING:
    from types import EllipsisType

    import pygame as pg


class ScrollingBackground:
    """scrolling background."""

    def __init__(
        self,
        background_file: str,
        screen_width: int,
        screen_height: int,
    ) -> None:
        self._texture_id, self._texture_size = textures.get_texture(background_file)
        ic(self._texture_id)
        self._position = 0

        self._screen_width = screen_width
        self._screen_height = screen_height

    def scroll(self, value: float) -> None:
        """
        Scroll by `value` pixels (first layer).
        """
        self._position -= value

    def draw(self, _surface: pg.surface.Surface) -> None:
        """
        Draw background to surface.
        """
        renderer.draw_textured_quad(
            self._texture_id, (0, 0), self._texture_size, layer=-1
        )


class ParallaxBackground:
    """background using scrolling and parallax effect."""

    _animation_counter: float

    def __init__(
        self,
        background_scope: str,
        parallax_multiplier: float = 1.2,
        animated_layers: list[int] | EllipsisType = ...,
        load: bool = False,
    ) -> None:
        self._scope = background_scope
        self._multiplier = parallax_multiplier
        self._animation_counter = 0
        self._position = 0
        #
        # self._screen_width = screen_width
        # self._screen_height = screen_height
        self._animated_layers = animated_layers

        self._textures = []
        self._sizes = []

        if load:
            self.load_textures()

    def load_textures(self) -> None:
        """
        Load all textures.
        """
        screen_size = pv.global_vars.get_screen_size()
        for texture, _ in textures.get_all_from_scope(self._scope, size=screen_size):
            self._textures.append(texture)
            self._sizes.append(screen_size.xy)

    @property
    def loaded(self) -> bool:
        """
        Checks if textures have been loaded.
        """
        return len(self._textures) > 0

    @property
    def position(self) -> float:
        """
        Get the position of the top layer.
        """
        return -self._position * self._multiplier ** len(self._textures)

    def set_position(self, position: float) -> None:
        """
        Set the position of the top layer.
        """
        self._position = -position / (self._multiplier ** len(self._textures))
        # pv.global_vars.background_position = self.position

    def scroll(self, value: float) -> None:
        """
        Scroll by `value` pixels (first layer).
        """
        if self._position - value <= 0:
            self._position -= value

        # tmp = pv.global_vars.world_position
        # tmp.x = self.position
        # pv.global_vars.world_position = tmp
        # pv.global_vars.background_position = self.position

    def reset_scroll(self) -> None:
        """Reset scroll position."""
        self._animation_counter = 0
        self._position = 0

        # tmp = pv.global_vars.world_position
        # tmp.x = self.position
        # pv.global_vars.world_position = tmp
        pv.global_vars.background_position = self.position

    def draw(self, delta: float) -> None:
        """
        Draw background to surface.
        """
        self._animation_counter += delta

        screen_size = pv.global_vars.get_screen_size()

        n_layers = len(self._textures) - 1
        if n_layers == -1:
            self.load_textures()
            self.draw(delta)
            return

        for layer in range(n_layers, -1, -1):
            image_pos = self._position + 10 % screen_size.x
            image_pos *= self._multiplier ** (n_layers - layer)

            # if layer in self._animated_layers:
            #     image_pos *= self._animation_counter * .1
            #     image_pos *= self._multiplier**(n_layers-layer)

            image_pos = int(image_pos % screen_size.x)
            image_pos -= screen_size.x

            renderer.draw_textured_quad(
                self._textures[layer],
                (image_pos, 0),
                self._sizes[layer],
                convert_global=False,
                layer=-layer,
            )
            renderer.draw_textured_quad(
                self._textures[layer],
                (image_pos + screen_size.x, 0),
                self._sizes[layer],
                convert_global=False,
                layer=-layer,
            )
