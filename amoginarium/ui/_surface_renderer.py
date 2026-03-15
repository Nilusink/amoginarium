"""
amoginarium/ui/_surface_renderer.py

Project: amoginarium
Created: 15.03.2026
Authors: LukasKrah
"""

import pygame as pg
import typing as tp

from ..logic import convert_coord, coord_t


class PygameSurfaceRenderer:
    """PygameSurfaceRenderer"""

    @staticmethod
    def draw_circle(
            surface: pg.Surface,
            center: coord_t,
            radius: float,
            color: pg.typing.ColorLike,
            *_args: tp.Any,
            width: int = 0,
            draw_top_right: bool = False,
            draw_top_left: bool = False,
            draw_bottom_left: bool = False,
            draw_bottom_right: bool = False
    ) -> pg.Rect:
        return pg.draw.circle(
            surface=surface,
            center=convert_coord(center, tuple[int]),
            radius=radius,
            color=color,
            width=width,
            draw_top_right=draw_top_right,
            draw_top_left=draw_top_left,
            draw_bottom_left=draw_bottom_left,
            draw_bottom_right=draw_bottom_right
        )
