"""
amoginarium/graphics/ui/_surface_renderer.py

Project: amoginarium
Created: 15.03.2026
Authors: LukasKrah
"""

import pygame as pg
import typing as tp

from amoginarium.shared.utility import convert_coord, coord_t, color_t


class PygameSurfaceRenderer:
    """PygameSurfaceRenderer"""

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
        """
        Draws a rectangle on the given surface.
        :param Surface surface: surface to draw on
        :param color: color to draw with
        :param top_left: top left position
        :param size: size of the rectangle
        :param int width: (optional) used for line thickness or to indicate that
            the rectangle is to be filled (not to be confused with the width value
            of the ``rect`` parameter)
                | if ``width == 0``, (default) fill the rectangle
                | if ``width > 0``, used for line thickness
                | if ``width < 0``, nothing will be drawn
                |
        :param int border_radius: (optional) used for drawing rectangle with rounded corners.
            The supported range is [0, min(height, width) / 2], with 0 representing a rectangle
            without rounded corners.
        :param int border_top_left_radius: (optional) used for setting the value of top left
            border. If you don't set this value, it will use the border_radius value.
        :param int border_top_right_radius: (optional) used for setting the value of top right
            border. If you don't set this value, it will use the border_radius value.
        :param int border_bottom_left_radius: (optional) used for setting the value of bottom left
            border. If you don't set this value, it will use the border_radius value.
        :param int border_bottom_right_radius: (optional) used for setting the value of bottom right
            border. If you don't set this value, it will use the border_radius value.
        :returns: a rect bounding the changed pixels, if nothing is drawn the
            bounding rect's position will be the position of the given ``rect``
            parameter and its width and height will be 0
        """
        return pg.draw.rect(
            surface=surface,
            color=color,
            rect=(convert_coord(top_left), convert_coord(size)),
            width=width,
            border_radius=int(border_radius),
            border_top_left_radius=int(border_top_left_radius),
            border_top_right_radius=int(border_top_right_radius),
            border_bottom_left_radius=int(border_bottom_left_radius),
            border_bottom_right_radius=int(border_bottom_right_radius)
        )

    draw_rounded_rect = draw_rect
