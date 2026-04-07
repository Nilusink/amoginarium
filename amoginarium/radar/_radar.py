"""
_radar.py
10.03.2026

"radar" sensors that can see through walls

Author:
Nilusink
"""
from icecream import ic
import typing as tp
import numpy as np

from ..debugging import timeit
from ..logic import coord_t, Vec2, point_in_triangle, is_related, \
    normalize_angle
from ..entities import Players, Bullets, Walls
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
            out.append(Vec2().from_polar(curr_angle, self.detection_range))

        return out

    def _check_in_sphere(
            self,
            targets: tp.Iterable[GameEntity]
    ) -> list[GameEntity]:
        """
        check if a target is inside the calculated sphere
        """
        out = []
        center: Vec2 = self.parent.position + self._position_offset
        angle_step = (np.pi * 2) / self._sphere_accuracy
        position_offset = self.parent.world_position + self._position_offset
        for target in targets:
            delta = target.position - center

            if not hasattr(target, 'size'):
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

                    if point_in_triangle(
                            delta,
                            t1,
                            t2,
                            Vec2()
                    ):
                        # check RCS
                        # check left and right side of target
                        size_factor = Vec2().from_polar(
                            normalize_angle(delta.angle) + np.pi / 2,
                            target.size.length / 2
                        )

                        a1 = (target.position + size_factor) - center
                        a2 = (target.position - size_factor) - center

                        da = normalize_angle(a1.angle - a2.angle)
                        if da >= self._min_rcs:
                            out.append(target)

                            if self.parent.coalition is not target.coalition:
                                if angle_index not in self._highlighted_sectors:
                                    self._highlighted_sectors.append(angle_index)

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
            po = self.parent.world_position + self._position_offset
            for sector in self._highlighted_sectors:
                t1 = self._sphere[sector] + po
                t2 = self._sphere[(sector + 1) % self._sphere_accuracy] + po
                renderer.draw_polygon(
                    (self.parent.world_position + self._position_offset, t1, t2),
                    (.4, .4, 1, .2)
                )
            self._highlighted_sectors.clear()

            if self._debug and self._sphere:
                renderer.draw_polygon(
                    self._sphere,
                    (1, 0, 0, .5),
                    center=self.parent.world_position,
                    # convert_global=False
                )
                for delta in self._sphere:
                    renderer.draw_circle(
                        self.parent.world_position + delta,
                        4,
                        4,
                        (1, .5, 0)
                    )

                for target in self.get_targets(Players.sprites() + Bullets.sprites()):
                    renderer.draw_line(
                        self.parent.world_position,
                        target.world_position,
                        (1, 1, 0)
                    )

        super().gl_draw()
