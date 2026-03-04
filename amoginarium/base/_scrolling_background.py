"""
_scrolling_background.py
27. January 2024

A parralax-scrolling background

Author:
Nilusink
"""
# from OpenGL
from icecream import ic

import pygame as pg

from ..shared import global_vars
from ..render_bindings import renderer
from ..base._textures import textures


class ScrollingBackground:
    def __init__(
            self,
            background_file: str,
            scrolling_part_file: str,
            screen_width: int,
            screen_height: int,
    ) -> None:
        self._texture_id, self._texture_size = textures.get_texture(
            background_file
        )
        ic(self._texture_id)
        self._position = 0

        self._screen_width = screen_width
        self._screen_height = screen_height

    def scroll(self, value: float) -> None:
        """
        scroll by `value` pixels (first layer)
        """
        self._position -= value

    def draw(self, surface: pg.surface.Surface) -> None:
        """
        draw background to surface
        """
        renderer.draw_textured_quad(
            self._texture_id,
            (0, 0),
            self._texture_size
        )


class ParalaxBackground:
    _animation_counter: float

    def __init__(
            self,
            background_scope: str,
            screen_width: int,
            screen_height: int,
            parallax_multiplier: float = 1.2,
            animated_layers: list[int] = ...,
            load: bool = False
    ) -> None:
        self._scope = background_scope
        self._multiplier = parallax_multiplier
        self._animation_counter = 0
        self._position = 0

        self._screen_width = screen_width
        self._screen_height = screen_height
        self._animated_layers = animated_layers

        self._textures = []
        self._sizes = []

        if load:
            self.load_textures()

    def load_textures(self) -> None:
        """
        load all textures
        """
        for texture, _ in textures.get_all_from_scope(
                self._scope, size=(self._screen_width, self._screen_height)
        ):
            self._textures.append(texture)
            self._sizes.append((self._screen_width, self._screen_height))

    @property
    def loaded(self) -> bool:
        """
        checks if textures have been loaded
        """
        return len(self._textures) > 0

    @property
    def position(self) -> float:
        """
        get the position of the top layer
        """
        return -self._position * self._multiplier ** len(self._textures)

    def scroll(self, value: float) -> None:
        """
        scroll by `value` pixels (first layer)
        """
        if self._position - value <= 0:
            self._position -= value

        # tmp = global_vars.world_position
        # tmp.x = self.position
        # global_vars.world_position = tmp
        global_vars.background_position = self.position

    def reset_scroll(self) -> None:
        self._animation_counter = 0
        self._position = 0

        # tmp = global_vars.world_position
        # tmp.x = self.position
        # global_vars.world_position = tmp
        global_vars.background_position = self.position

    def draw(self, delta: float) -> None:
        """
        draw background to surface
        """
        self._animation_counter += delta

        n_layers = len(self._textures) - 1
        if n_layers == -1:
            self.load_textures()
            return self.draw(delta)

        for layer in range(n_layers, -1, -1):
            image_pos = self._position + 10 % self._screen_width
            image_pos *= self._multiplier ** (n_layers - layer)

            # if layer in self._animated_layers:
            #     image_pos *= self._animation_counter * .1
            #     image_pos *= self._multiplier**(n_layers-layer)

            image_pos = int(image_pos % self._screen_width)
            image_pos -= self._screen_width

            renderer.draw_textured_quad(
                self._textures[layer],
                (image_pos, 0),
                self._sizes[layer]
            )
            renderer.draw_textured_quad(
                self._textures[layer],
                (image_pos + self._screen_width, 0),
                self._sizes[layer]
            )
