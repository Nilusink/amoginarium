"""
_static_sensors.py
15.04.2026

allows sensors to be placed on the map

Author:
Nilusink
"""

from ctypes import Array
import typing as tp

from amoginarium.shared import SensorCIDs, base_entity_t, ProcessCommand
from amoginarium.shared import BaseCommandType, Coalitions, DummyCIDs
from amoginarium.shared.utility import Vec2
from amoginarium import pv

# from .._groups import CollisionDestroyed
from .._base_entities import LogicGameEntity
from ._detection_group import DetectionGroup
from ._magic_sensor import MagicSensor
from ._radar_sensor import RadarSensor
from ._base_sensor import BaseSensor


# todo - mytodo - collisiondestroyed

class VisualSensor(LogicGameEntity):
    __slots__ = ("detection_group", "coalition", "_hp")

    _cid = SensorCIDs.magic
    _sensor_type: tp.Type[BaseSensor] = MagicSensor
    _size: tuple[float, float] = (64, 64)
    _max_hp = 40

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            position: Vec2,
            coalition: Coalitions,
            detection_group: DetectionGroup = None,
            **sensor_args,
    ) -> None:
        self.coalition = coalition
        self._hp = self._max_hp

        super().__init__(
            runtime_buffer=runtime_buffer,
            position=position,
            size=Vec2().from_cartesian(*self._size)
        )
        # self.add(CollisionDestroyed)

        if not detection_group:
            self.detection_group = DetectionGroup(str(self.id))

        else:
            self.detection_group = detection_group

        sensor = self._sensor_type(
            runtime_buffer=runtime_buffer, parent=self, **sensor_args
        )
        self.detection_group.add_sensor(sensor)

        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs={"id": self.id, "cid": DummyCIDs.base_bullet, "spawn_time": 0, "position": position.xy},
            )
        )

    def hit(self, damage: float, hit_by: LogicGameEntity = ...) -> None:
        self._hp -= damage

        if self._hp <= 0:
            self.kill()


class VisualRadarSensor(VisualSensor):
    __slots__ = ()

    _cid = SensorCIDs.radar
    _sensor_type = RadarSensor
