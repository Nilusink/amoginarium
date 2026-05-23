"""
Pygame groups for drawn entities.

| ``Path``: amoginarium/graphics/entities/_graphics_groups.py
| ``Project``: amoginarium
| ``Created``: 29.03.2026
| ``Authors``: Nilusink
"""

import typing as tp

import pygame as pg


class BaseGroup(pg.sprite.Group):
    def sprites(self) -> list[tp.Any]:
        return super().sprites()

    def gl_draw(self, delta_cal: float) -> None:
        for sprite in self.sprites():
            sprite.gl_draw(delta_cal)


class _UIEntities(BaseGroup): ...


class _Drawn(BaseGroup):
    def __init__(self, layer: int) -> None:
        self._layer = layer
        super().__init__()

    def gl_draw(self, delta_cal: float) -> None:
        for sprite in self.sprites():
            sprite.gl_draw(delta_cal, layer=self._layer)


class _Cursor(BaseGroup): ...


class _SyncedEntities(BaseGroup):
    def update_from_buffer(self) -> None:
        for entity in self.sprites():
            entity.update_from_buffer(True)


Drawn_0 = _Drawn(0)
Drawn_1 = _Drawn(1)
Drawn_2 = _Drawn(2)
Cursor = _Cursor()
UIEntities = _UIEntities()
SyncedEntities = _SyncedEntities()
