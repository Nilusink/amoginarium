"""
amoginarium/logic/entities/_groups/_base_group.py

Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

import typing as tp

from amoginarium.shared.utility import Vec2, normalize_angle
from amoginarium.shared import BaseLogicEntityLike

from ._logic_group import LogicGroup


class BaseGroup(LogicGroup):
    """Basic group for logic entities"""

    @staticmethod
    def entities_in_circle(
            entities: list[BaseLogicEntityLike],
            center: Vec2,
            radius: float,
            min_radius: float = 0
    ) -> list[tuple[float, tp.Any]]:
        """
        Check which of the given entities are in the circle
        :param entities: List of entities to check
        :param center: Center of the circle
        :param radius: Radius of the circle (Max distance)
        :param min_radius: Minimum distance
        :return: list of tuples (distance, entity) of entities in the circle
        """
        out = []

        for sprite in entities:
            delta = sprite.position - center

            if min_radius <= delta.length <= radius:
                out.append((delta.length, sprite))

        return sorted(out, key=lambda r: r[0])

    @staticmethod
    def entities_in_partial_circle(
            entities: list[BaseLogicEntityLike],
            center: Vec2,
            radius: float,
            angle_start: Vec2,
            angle_end: Vec2,
            min_radius: float = 0
    ) -> list[tuple[float, BaseLogicEntityLike]]:
        """
        Check which of the given entities are in the partial circle
        :param entities: List of entities to check
        :param center: Center of the circle
        :param radius: Radius of the circle (Max distance)
        :param angle_start: Starting angle of the partial circle
        :param angle_end: Ending angle of the partial circle
        :param min_radius: Minimum distance
        :return: list of tuples (distance, entity) of entities in the circle
        """
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
        get all entities of this group inside a circle, sorted by distance (closest first)
        :param center: center of the circle
        :param radius: radius of the circle
        :return: list of tuples (distance, entity) of entities in the circle
        """
        return self.entities_in_circle(self.sprites(), center, radius)

    def sprites(self) -> list[BaseLogicEntityLike]:
        """return: list of all sprites in the group"""
        return super().sprites()
