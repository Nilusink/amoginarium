"""
_visual_sensors.py
10.03.2026

sensors limited to direct visual contact

Author:
Nilusink
"""
from time import perf_counter

import numpy as np
from icecream import ic
import typing as tp

from ..entities._base_entity import GameEntity, VisibleBaseEntity
from ..base._groups import Players, Bullets, Walls
from ..logic import coord_t, convert_coord, Vec2, lidar_sphere, \
    point_in_triangle, is_related
from ..render_bindings import renderer
from ._sensors import BaseSensor


class VisualSensor(BaseSensor):
    _debug: bool = False

    def __init__(
            self,
            parent: GameEntity,
            detection_range: float,
            position_offset: coord_t = ...,
            sphere_accuracy: int = 128,
            min_rcs: float = .06,
            visible: bool = True
    ) -> None:
        super().__init__(parent, detection_range, position_offset, visible)
        self._sphere = None
        self._highlighted_sectors = []
        self._target_RCSs = []
        self._sphere_accuracy = sphere_accuracy
        self._min_rcs = min_rcs

    def _check_in_sphere(
            self,
            targets: tp.Iterable[GameEntity]
    ) -> list[GameEntity]:
        """
        check if a target is inside the calculated sphere
        """
        out = []
        center = self.parent.position + self._position_offset
        for target in targets:
            delta = target.position - center

            # filter by range
            if delta.length <= self.detection_range:

                if self._sphere:
                    delta.angle = Vec2.normalize_angle(delta.angle)

                    # filter by in sphere
                    angle_index = (delta.angle / (np.pi * 2)) * len(self._sphere)
                    angle_index = int(angle_index)

                    # get sector
                    t1 = self._sphere[angle_index]
                    t2 = self._sphere[(angle_index + 1) % len(self._sphere)]

                    if point_in_triangle(
                            delta,
                            t1,
                            t2,
                            Vec2()
                    ):
                        # check RCS
                        # check left and right side of target
                        size_factor = Vec2.from_polar(
                            delta.angle + np.pi/2,
                            target.size.length / 2
                        )

                        a1 = (target.position + size_factor) - center
                        a2 = (target.position - size_factor) - center

                        da = Vec2.normalize_angle(a1.angle - a2.angle)
                        if da >= self._min_rcs:
                            out.append(target)

                            if not is_related(self.parent, target, 4):
                                t1 += self.parent.world_position + self._position_offset
                                t2 += self.parent.world_position + self._position_offset

                                self._highlighted_sectors.append((t1, t2))

                        self._target_RCSs.append((
                            a1 + self.parent.world_position + self._position_offset,
                            a2 + self.parent.world_position + self._position_offset
                        ))

                    continue

                out.append(target)

        return out

    def get_targets(
            self,
            from_entities: tp.Iterable[GameEntity] = None
    ) -> list[GameEntity]:
        if from_entities is None:
            targets = [p for p in Players.sprites() if p.alive]
            targets.extend(Bullets.sprites())

        else:
            targets = from_entities

        # check if target is in pre-calculated sphere
        valid_targets = self._check_in_sphere(targets)

        return valid_targets

    def update(self, delta: float) -> None:
        if self._sphere is None:
            # funny stuff
            self._sphere = lidar_sphere(
                self.parent.position,
                self.detection_range,
                self._sphere_accuracy,
                Walls.sprites(),
                5
            )

    def gl_draw(self, draw: bool = True) -> None:
        # detection sphere
        if draw:
            for sector in self._highlighted_sectors:
                renderer.draw_polygon(
                    (self.parent.world_position + self._position_offset, *sector),
                    (.4, .4, 1, .2)
                )
            self._highlighted_sectors.clear()

            for RCS in self._target_RCSs:
                renderer.draw_line(
                    self.parent.world_position + self._position_offset,
                    RCS[0],
                    (1, 0, 0)
                )
                renderer.draw_line(
                    self.parent.world_position + self._position_offset,
                    RCS[1],
                    (1, 0, 0)
                )
            self._target_RCSs.clear()

            if self._debug and self._sphere:
                renderer.draw_polygon(
                    self._sphere,
                    (1, 0, 0, .5),
                    self.parent.world_position
                )
                for delta in self._sphere:
                    renderer.draw_circle(
                        self.parent.world_position + delta,
                        4,
                        4,
                        (1, .5, 0)
                    )

        super().gl_draw()
