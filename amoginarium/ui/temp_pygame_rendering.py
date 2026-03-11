"""
amoginarium/ui/temp_pygame_rendering.py

Project: amoginarium
"""

from ..logic import convert_coord, Vec2

import pygame as pg


##################################################
#                     Code                       #
##################################################

def draw_circle(
        center, radius, color, surface
):
    pg.draw.circle(
        surface=surface,
        center=convert_coord(center, Vec2).xy,
        radius=radius,
        color=color
    )


def draw_rect(
        start,
        size,
        color,
        surface
):
    pg.draw.rect(surface=surface, rect=(convert_coord(start, Vec2).xy, convert_coord(size, Vec2).xy), color=color)


def draw_rounded_rect(
        surface,
        start,
        size,
        color,
        radius,
) -> None:
    start = convert_coord(start, Vec2)
    size = convert_coord(size, Vec2)

    # circles at edges
    draw_circle(
        start + radius,
        radius,
        color,
        surface
    )
    draw_circle(
        start + size - radius,
        radius,
        color,
        surface
    )
    draw_circle(
        start + size - radius,
        radius,
        color,
        surface
    )
    draw_circle(
        (
            start.x + size.x - radius,
            start.y + radius
        ),
        radius,
        color,
        surface
    )
    draw_circle(
        (
            start.x + radius,
            start.y + size.y - radius
        ),
        radius,
        color,
        surface
    )

    # fill in squares
    if size.x > 2 * radius:
        draw_rect(
            (
                start.x + radius,
                start.y
            ),
            (
                size.x - 2 * radius,
                size.y
            ),
            color,
            surface
        )

    if size.y > 2 * radius:
        draw_rect(
            (
                start.x,
                start.y + radius
            ),
            (
                size.x,
                size.y - 2 * radius
            ),
            color,
            surface
        )
