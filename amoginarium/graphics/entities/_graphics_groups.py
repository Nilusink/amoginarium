"""
_graphics_groups.py
29.03.2026

pygame groups for drawn entities

Author:
Nilusink
"""
import pygame as pg
import typing as tp


class BaseGroup(pg.sprite.Group):
    def sprites(self) -> list[tp.Any]:
        return super().sprites()

    def gl_draw(self, delta_cal: float) -> None:
        for sprite in self.sprites():
            sprite.gl_draw(delta_cal)


class _UIEntities(BaseGroup):
    ...


class _Drawn(BaseGroup):
    ...


class _Cursor(BaseGroup):
    ...


class _SyncedEntities(BaseGroup):
    def update_from_buffer(self) -> None:
        for entity in self.sprites():
            entity.update_from_buffer(True)


Drawn = _Drawn()
Cursor = _Cursor()
UIEntities = _UIEntities()
SyncedEntities = _SyncedEntities()
