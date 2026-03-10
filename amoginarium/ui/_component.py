"""
amoginarium/entities/_ui/_ui_component.py

Project: amoginarium
"""

from __future__ import annotations

import typing as tp

from ._entity import UIEntity
from ._types import anchor_t

from ..logic import Vec2, coord_t, convert_coord
from ..shared import global_vars

import pygame as pg


##################################################
#                     Code                       #
##################################################

class UIComponent(UIEntity):
    __relative_position: Vec2
    __relative_size: Vec2
    __placement_anchor: anchor_t

    __absolute_position: Vec2
    __absolute_size: Vec2
    __width: float
    __height: float
    __top_left: Vec2
    __top_right: Vec2
    __bottom_left: Vec2
    __bottom_right: Vec2

    # masks - zwei farben

    # mask get at local

    # hover grob?
    # mask check

    # wenn nix anders - gleiche maske - size/position animations gleich wie davor keine ausrechnen

    __mask: pg.Mask

    def __init__(
            self,
            relative_position: coord_t,
            relative_size: coord_t,
            *_args: tp.Any,
            parent: UIEntity | None = None,
            placement_anchor: anchor_t = "center"
    ) -> None:
        super().__init__(parent=parent)

        self.__relative_position = convert_coord(relative_position, Vec2)
        self.__relative_size = convert_coord(relative_size, Vec2)
        self.__placement_anchor = placement_anchor

        surface = pg.Surface((10, 10))
        pg.draw.rect(surface, (255, 0, 0), (0, 0, 10, 10))

        normal_mask = pg.mask.from_surface(surface)

    @staticmethod
    def __relative_to_absolute(
            relative_position: coord_t,
            relative_size: coord_t
    ) -> tuple[Vec2, Vec2]:
        return (
            convert_coord(
                (
                    int(relative_position.x * global_vars.resolution.x),
                    int(relative_position.y * global_vars.resolution.y)
                ),
                Vec2
            ),
            convert_coord(
                (
                    int(relative_size.x * global_vars.resolution.x),
                    int(relative_size.y * global_vars.resolution.y)
                ),
                Vec2
            )
        )

    def gl_draw(self) -> None:
        super().gl_draw()

        self.__absolute_position, self.__absolute_size = self.__relative_to_absolute(
            self.__relative_position,
            self.__relative_size
        )

        self.__width = self.__absolute_size.x
        self.__height = self.__absolute_size.y

        if self.__placement_anchor == "nw":
            self.__top_left = self.__absolute_position
            self.__top_right = self.__absolute_position + convert_coord((self.__absolute_size.x, 0), Vec2)
            self.__bottom_left = self.__absolute_position + convert_coord((0, self.__absolute_size.y), Vec2)
            self.__bottom_right = self.__absolute_position + self.__absolute_size.y
        elif self.__placement_anchor == "center":
            self.__top_left = self.__absolute_position - self.__absolute_size / 2
            self.__top_right = self.__absolute_position + convert_coord(
                (self.__absolute_size.x / 2, -self.__absolute_size.y / 2),
                Vec2)
            self.__bottom_left = self.__absolute_position + convert_coord(
                (-self.__absolute_size.x / 2, self.__absolute_size.y / 2),
                Vec2)
            self.__bottom_right = self.__absolute_position + self.__absolute_size / 2

    @property
    def _abs_position(self) -> Vec2:
        """:return: Absolute position - anchor not factored in"""
        return self.__absolute_position

    @property
    def _abs_size(self) -> Vec2:
        """:return: Absolute size"""
        return self.__absolute_size

    @property
    def _rel_position(self) -> Vec2:
        """:return: Relative position - anchor not factored in"""
        return self.__relative_position

    @property
    def _rel_size(self) -> Vec2:
        """:return: Relative size"""
        return self.__relative_size

    @property
    def _width(self) -> float:
        """:return: Absolute width"""
        return self.__width

    @property
    def _height(self) -> float:
        """:return: Absolute height"""
        return self.__width

    @property
    def _placement_anchor(self) -> anchor_t:
        """:return: Placement anchor"""
        return self.__placement_anchor

    @property
    def _top_left(self) -> Vec2:
        """:return: Absolute top left"""
        return self.__top_left

    @property
    def _top_right(self) -> Vec2:
        """:return: Absolute top right"""
        return self.__top_right

    @property
    def _bottom_left(self) -> Vec2:
        """:return: Absolute bottom left"""
        return self.__bottom_left

    @property
    def _bottom_right(self) -> Vec2:
        """:return: Absolute bottom right"""
        return self.__bottom_right
