"""
_visual_sensors.py
10.03.2026

sensors limited to direct visual contact

Author:
Nilusink
"""
from icecream import ic
import typing as tp

from ..entities._base_entity import GameEntity, VisibleBaseEntity
from ..base._groups import Players, Bullets, Walls
from ..logic import coord_t, convert_coord, Vec2
from ..render_bindings import renderer
from ._sensors import BaseSensor


class VisualSensor(BaseSensor):
    def get_targets(
            self,
            from_entities: tp.Iterable[GameEntity] = None
    ) -> list[GameEntity]:
        if from_entities is None:
            targets = [p for p in Players.sprites() if p.alive]
            targets.extend(Bullets.sprites())

        else:
            targets = from_entities

        in_range = [e[1] for e in Players.entities_in_circle(
            targets,
            self.parent.position + self._position_offset,
            self.detection_range,
        )]

        # check targets are obstructed by ground
        valid_targets = []
        for target in in_range:
            walls = Walls.walls_in_line(
                self.parent.position + self._position_offset,
                target.position
            )

            if not walls:
                valid_targets.append(target)

        return valid_targets

