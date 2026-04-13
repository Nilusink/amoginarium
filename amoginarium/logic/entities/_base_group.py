
"""
amoginarium/logic/entities/_base_group.py

Project: amoginarium
Created: 13.04.2026
Authors: LukasKrah
"""

import pygame as pg
import typing as tp

from ...shared.utility import Vec2, normalize_angle
from ...shared import BaseLogicEntityLike


class BaseGroup(pg.sprite.Group):
    @staticmethod
    def entities_in_circle(
            entities: list[pg.sprite.Sprite],
            center: Vec2,
            radius: float,
            min_radius: float = 0
    ) -> list[tuple[float, tp.Any]]:
        """
        check which of the given entities are in the circle
        """
        out = []

        for sprite in entities:
            delta = sprite.position - center

            if min_radius <= delta.length <= radius:
                out.append((delta.length, sprite))

        return sorted(out, key=lambda r: r[0])

    @staticmethod
    def entities_in_partial_circle(
            entities: list[pg.sprite.Sprite],
            center: Vec2,
            radius: float,
            angle_start: Vec2,
            angle_end: Vec2,
            min_radius: float = 0
    ):
        out = []
        angle_delta = normalize_angle(
            angle_end.angle
            - angle_start.angle
        )
        start2 = angle_start.angle + angle_delta
        end2 = angle_end.angle - angle_delta

        for sprite in entities:
            delta = sprite.position - center

            if min_radius <= delta.length <= radius:
                delta.angle = normalize_angle(delta.angle)
                if any([
                    angle_start.angle < delta.angle < start2,
                    angle_end.angle > delta.angle > end2,
                ]):
                    out.append((delta.length, sprite))

        return sorted(out, key=lambda r: r[0])

    def get_entities_in_circle(
            self,
            center: Vec2,
            radius: float
    ) -> list[tuple[float, tp.Any]]:
        """
        get all entities inside a circle, sorted by distance (closest first)
        """
        return self.entities_in_circle(self.sprites(), center, radius)

    def sprites(self) -> list[BaseLogicEntityLike]:
        return super().sprites()
