"""
_radar.py
10.03.2026

"radar" sensors that can see through walls

Author:
Nilusink
"""
import typing as tp
import numpy as np

from ..debugging import timeit
from ..logic import coord_t, Vec2, lidar_sphere, point_in_triangle, is_related
from ..base._groups import Players, Bullets, Walls
from ..entities._base_entity import GameEntity
from ..render_bindings import renderer
from ._sensors import BaseSensor


class RadarSensor(BaseSensor):
    _debug: bool = False

    def __init__(
            self,
            parent: GameEntity,
            detection_range: float,
            position_offset: coord_t = ...,
            sphere_accuracy: int = 128,
            min_rcs: float = .04,
            visible: bool = True
    ) -> None:
        super().__init__(parent, detection_range, position_offset, visible)
        self._sphere = None
        self._highlighted_sectors = []
        self._sphere_accuracy = sphere_accuracy
        self._min_rcs = min_rcs

    def _calculate_sphere(self) -> list[Vec2]:
        """
        calculate detection sphere
        """
        angle_step = (np.pi * 2) / self._sphere_accuracy

        out = []
        for i in range(self._sphere_accuracy):
            curr_angle = i * angle_step
            out.append(Vec2.from_polar(curr_angle, self.detection_range))

        return out

    @timeit(1)
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
            self._sphere = self._calculate_sphere()

    def gl_draw(self, draw: bool = True) -> None:
        # detection sphere
        if draw:
            for sector in self._highlighted_sectors:
                renderer.draw_polygon(
                    (self.parent.world_position + self._position_offset, *sector),
                    (.4, .4, 1, .2)
                )
            self._highlighted_sectors.clear()

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
