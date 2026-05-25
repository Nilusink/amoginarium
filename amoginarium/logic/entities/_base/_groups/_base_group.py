"""
Defines the BaseGroup class, extending LogicGroup with spatial querying methods.

Provides static and instance methods for finding entities within circles or arcs.

| ``Path``: amoginarium/logic/entities/_base/_groups/_base_group.py
| ``Project``: amoginarium
| ``Created``: 25.01.2024
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import operator
import typing as tp

from amoginarium.shared import PositionedLogicEntityLike
from amoginarium.shared.utility import normalize_angle

from ._logic_group import LogicGroup

if tp.TYPE_CHECKING:
    from amoginarium.shared.utility import Vec2


class BaseGroup[T: PositionedLogicEntityLike](LogicGroup[T]):
    """Basic group for logic entities."""

    __slots__ = ()

    @staticmethod
    def entities_in_circle(
        entities: list[PositionedLogicEntityLike],
        center: Vec2,
        radius: float,
        min_radius: float = 0,
    ) -> list[tuple[float, PositionedLogicEntityLike]]:
        """
        Check which of the given entities are in the circle
        :param entities: List of entities to check
        :param center: Center of the circle
        :param radius: Radius of the circle (Max distance)
        :param min_radius: Minimum distance
        :return: list of tuples (distance, entity) of entities in the circle.
        """
        out: list[tuple[float, PositionedLogicEntityLike]] = []

        for sprite in entities:
            delta: Vec2 = sprite.position - center

            if min_radius <= delta.length <= radius:
                out.append((delta.length, sprite))

        return sorted(out, key=operator.itemgetter(0))

    @staticmethod
    def entities_in_partial_circle(
        entities: list[PositionedLogicEntityLike],
        center: Vec2,
        radius: float,
        angle_start: Vec2,
        angle_end: Vec2,
        min_radius: float = 0,
    ) -> list[tuple[float, PositionedLogicEntityLike]]:
        """
        Check which of the given entities are in the partial circle
        :param entities: List of entities to check
        :param center: Center of the circle
        :param radius: Radius of the circle (Max distance)
        :param angle_start: Starting angle of the partial circle
        :param angle_end: Ending angle of the partial circle
        :param min_radius: Minimum distance
        :return: list of tuples (distance, entity) of entities in the circle.
        """
        out: list[tuple[float, PositionedLogicEntityLike]] = []
        angle_delta: float = normalize_angle(angle_end.angle - angle_start.angle)
        start2: float = angle_start.angle + angle_delta
        end2: float = angle_end.angle - angle_delta

        for sprite in entities:
            delta: Vec2 = sprite.position - center

            if min_radius <= delta.length <= radius:
                delta.angle = normalize_angle(delta.angle)
                if any(
                    [
                        angle_start.angle < delta.angle < start2,
                        angle_end.angle > delta.angle > end2,
                    ]
                ):
                    out.append((delta.length, sprite))

        return sorted(out, key=operator.itemgetter(0))

    def get_entities_in_circle(
        self, center: Vec2, radius: float
    ) -> list[tuple[float, PositionedLogicEntityLike]]:
        """
        Get entities of this group inside a circle, sorted by distance (closest first).

        :param center: center of the circle
        :param radius: radius of the circle
        :return: list of tuples (distance, entity) of entities in the circle.
        """
        return self.entities_in_circle(self.entities(), center, radius)
