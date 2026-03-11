"""
_visual_sensors.py
10.03.2026

sensors limited to direct visual contact

Author:
Nilusink
"""
from ..logic import Vec2, lidar_sphere, coord_t
from ..entities._base_entity import GameEntity
from ..base._groups import Walls
from ._radar import RadarSensor


class VisualSensor(RadarSensor):
    def __init__(
            self,
            parent: GameEntity,
            detection_range: float,
            position_offset: coord_t = ...,
            sphere_accuracy: int = 128,
            min_rcs: float = .06,
            visible: bool = True
    ) -> None:
        super().__init__(
            parent,
            detection_range,
            position_offset,
            sphere_accuracy,
            min_rcs,
            visible
        )

    def _calculate_sphere(self) -> list[Vec2]:
        return lidar_sphere(
            self.parent.position + self._position_offset,
            self.detection_range,
            self._sphere_accuracy,
            Walls.sprites(),
            5
        )
