"""
amoginarium/ui/_surface_renderer.py

Project: amoginarium
Created: 15.03.2026
Authors: LukasKrah
"""

import pygame as pg
import typing as tp

from ..logic import convert_coord, coord_t, color_t, convert_color


class PygameSurfaceRenderer:
    """PygameSurfaceRenderer"""

    @staticmethod
    def draw_circle(
            surface: pg.Surface,
            center: coord_t,
            radius: float,
            *_args: tp.Any,
            color: color_t = (255, 255, 255, 255),
            width: int = 0,
            draw_top_right: bool = False,
            draw_top_left: bool = False,
            draw_bottom_left: bool = False,
            draw_bottom_right: bool = False
    ) -> pg.Rect:
        return pg.draw.circle(
            surface=surface,
            center=convert_coord(center, tuple[float, float]),
            radius=radius,
            color=convert_color(color, int),
            width=width,
            draw_top_right=draw_top_right,
            draw_top_left=draw_top_left,
            draw_bottom_left=draw_bottom_left,
            draw_bottom_right=draw_bottom_right
        )

    @staticmethod
    def draw_rect(
            surface: pg.Surface,
            top_left: coord_t,
            size: coord_t,
            *_args: tp.Any,
            color: color_t = (255, 255, 255, 255),
            width: int = 0,
            border_radius: int | float = -1,
            border_top_left_radius: int | float = -1,
            border_top_right_radius: int | float = -1,
            border_bottom_left_radius: int | float = -1,
            border_bottom_right_radius: int | float = -1,
    ) -> pg.Rect:
        return pg.draw.rect(
            surface=surface,
            color=color,
            rect=(convert_coord(top_left, tuple), convert_coord(size, tuple)),
            width=width,
            border_radius=int(border_radius),
            border_top_left_radius=int(border_top_left_radius),
            border_top_right_radius=int(border_top_right_radius),
            border_bottom_left_radius=int(border_bottom_left_radius),
            border_bottom_right_radius=int(border_bottom_right_radius)
        )

    draw_rounded_rect = draw_rect
