"""
"Radar" sensors that can see through walls.

Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_radar_sensor.py
Project: amoginarium
Created: 10.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

import numpy as np
from icecream import ic

from amoginarium.shared import SensorCIDs
from amoginarium.shared.utility import normalize_angle, point_in_triangle, Vec2

from ...._base import Bullets, Players
from ._base_sensor import BaseSensor

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.utility import coord_t

    from ...._base import LogicGameEntity


class RadarSensor(BaseSensor):
    """
    sensor split into sectors, detection using angle width.

    ``param0`` detection range
    ``param3`` detect sectors (x4, 16 bit each)
    ``param4`` detect sectors (x4, 16 bit each)
    """

    # __slots__ = []

    _CID = SensorCIDs.sensor_radar
    _debug: tp.ClassVar[bool] = False
    _has_sectors = True

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        detection_range: float,
        position_offset: coord_t = ...,
        sphere_accuracy: int = 128,
        min_rcs: float = 0.04,
        visible: bool = True,
    ) -> None:
        self._sphere = None
        self._sphere_accuracy = sphere_accuracy
        self._has_sectors = sphere_accuracy
        self._min_rcs = min_rcs

        super().__init__(
            runtime_buffer, parent, detection_range, position_offset, visible
        )

    def _check_in_sphere(
        self, targets: tp.Iterable[LogicGameEntity]
    ) -> list[LogicGameEntity]:
        """
        Check if a target is inside the calculated sphere.
        """
        out = []
        center: Vec2 = self.parent.position + self._position_offset
        angle_step = (np.pi * 2) / self._sphere_accuracy
        for target in targets:
            delta = target.position - center

            if not hasattr(target, "size"):
                continue

            # filter by range
            if delta.length <= self.detection_range:
                if self._sphere:
                    # filter by in sphere
                    angle_index = normalize_angle(delta.angle) / angle_step
                    angle_index = int(angle_index)

                    # get sector
                    t1 = self._sphere[angle_index]
                    t2 = self._sphere[(angle_index + 1) % self._sphere_accuracy]

                    if point_in_triangle(delta, t1, t2, Vec2()):
                        # check RCS
                        # check left and right side of target
                        size_factor = Vec2().from_polar(
                            normalize_angle(delta.angle) + np.pi / 2,
                            target.size.length / 2,
                        )

                        a1 = (target.position + size_factor) - center
                        a2 = (target.position - size_factor) - center

                        da = normalize_angle(a1.angle - a2.angle)
                        if da >= self._min_rcs:
                            out.append(target)

                            if self.parent.coalition != target.coalition:
                                if angle_index not in self._highlighted_sectors:
                                    self._highlighted_sectors.append(angle_index)

                    continue

                out.append(target)

        return out

    def get_targets(
        self, from_entities: tp.Iterable[LogicGameEntity] | None = None
    ) -> list[LogicGameEntity]:
        if from_entities is None:
            targets = [p for p in Players.entities() if p.alive]
            targets.extend(Bullets.entities())

        else:
            targets = from_entities

        # check if target is in pre-calculated sphere
        valid_targets = self._check_in_sphere(targets)

        self._targets = valid_targets.copy()

        return valid_targets

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} range={self.detection_range}, "
            f"sa={self._sphere_accuracy}, min_rcs={self._min_rcs}>"
        )

    # def gl_draw(self, draw: bool = True) -> None:
    #     # detection sphere
    #     if draw:
    #         po = self.parent.world_position + self._position_offset
    #         for sector in self._highlighted_sectors:
    #             t1 = self._sphere[sector] + po
    #             t2 = self._sphere[(sector + 1) % self._sphere_accuracy] + po
    #             renderer.draw_polygon(
    #                 (self.parent.world_position + self._position_offset, t1, t2),
    #                 (.4, .4, 1, .2)
    #             )
    #         self._highlighted_sectors.clear()
    #
    #         if self._debug and self._sphere:
    #             renderer.draw_polygon(
    #                 self._sphere,
    #                 (1, 0, 0, .5),
    #                 center=self.parent.world_position,
    #                 # convert_global=False
    #             )
    #             for delta in self._sphere:
    #                 renderer.draw_circle(
    #                     self.parent.world_position + delta,
    #                     4,
    #                     4,
    #                     (1, .5, 0)
    #                 )
    #
    #             for target in self.get_targets(Players.entities() + Bullets.entities()):
    #                 renderer.draw_line(
    #                     self.parent.world_position,
    #                     target.world_position,
    #                     (1, 1, 0)
    #                 )
    #
    #     super().gl_draw()
