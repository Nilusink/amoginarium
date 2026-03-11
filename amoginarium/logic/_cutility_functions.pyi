import typing as tp
import pygame as pg


class Vec2:
    ...


class EntityLike(tp.Protocol):
    position: Vec2
    size: Vec2
    mask: pg.Mask
    rect: pg.Rect


def raycast_mask(
        sprite: EntityLike,
        start: Vec2,
        end: Vec2,
        sample_rate: int = 10
) -> Vec2:
    ...


def point_in_triangle(
        p: Vec2,
        a: Vec2,
        b: Vec2,
        c: Vec2
) -> bool:
    """
    p: point to test
    a,b,c: triangle vertices
    """
