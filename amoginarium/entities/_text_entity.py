"""
_text_entity.py
06. June 2024

an entity displaying text

Author:
Nilusink
"""
# from icecream import ic
import typing as tp
import pygame as pg

from ..logic import coord_t, Color, Vec2, convert_coord
from ..render_bindings import renderer, tColor
from ._groups import Drawn, Updated


class TextEntity(pg.sprite.Sprite):
    def __init__(
            self,
            _coalition,
            position: coord_t,
            text: str,
            size: int = 64,
            color: Color | tColor = ...,
            bg_color: Color | tColor = ...,
            bold: bool = False,
            italic: bool = False,
            font_family: str = "arial"
    ) -> None:
        if color is ...:
            color = Color.white(255)

        elif issubclass(type(color), tp.Iterable):
            tcolor = Color.from_255(*color)
            color = tcolor

        if bg_color is ...:
            bg_color = Color.black(0)

        elif issubclass(type(color), tp.Iterable):
            bg_color = Color.from_255(*bg_color)

        self._pos = convert_coord(position, Vec2)
        self._text = text
        self._color = color
        self._size = size
        self._bold = bold
        self._italic = italic
        self._font_family = font_family
        self._bg_color = bg_color

        super().__init__()
        self.add(Drawn)

        # generate text surface once
        self._regenerate_surface()

    def _regenerate_surface(self) -> None:
        """
        update the pygame surface (on parameter change)
        """
        self._text_surf = renderer.generate_pg_surf_text(
            self._text,
            self._color,
            self._bg_color,
            self._size,
            self._font_family,
            self._bold,
            self._italic,
        )

    def gl_draw(self):
        now = self._pos - Updated.world_position
        renderer.draw_pg_surf(
            now,
            self._text_surf,
            centered=False,
        )
