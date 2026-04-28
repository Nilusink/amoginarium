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
from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.utility import Vec2
from amoginarium import pv

# from .._groups import CollisionDestroyed
from ..._base import LogicGameEntity, GameCollisions
from ._detection_group import DetectionGroup
from ._magic_sensor import MagicSensor
from ._radar_sensor import RadarSensor
from ._base_sensor import BaseSensor

if tp.TYPE_CHECKING:
    from .._bullets import Bullet


# todo - mytodo - collisiondestroyed

class VisualSensor(LogicGameEntity):
    __slots__ = ("detection_group", "coalition", "_hp")

    _CID = SensorCIDs.magic
    _sensor_type: tp.Type[BaseSensor] = MagicSensor
    _size: tuple[float, float] = (64, 64)
    _max_hp = 40

    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_turrets

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
            size=Vec2().from_cartesian(*self._size),
            centered=True
        )
        self._create_collision()
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
                kwargs={"id": self.id, "cid": DummyCIDs.base_bullet.value, "spawn_time": 0, "position": position.xy},
            )
        )

    def hit(self, damage: float, hit_by: LogicGameEntity = ...) -> None:
        self._hp -= damage

        if self._hp <= 0:
            self.kill()

    def __on_collision_bullet(self, event: CollisionEvent["Bullet"]) -> None:
        dmg = event.other_entity.damage
        if dmg > 0 and event.other_entity.parent != self:
            self.hit(dmg, hit_by=event.other_entity)

    def _collision_start(self, events: list[CollisionEvent["Bullet"]]) -> None:
        for event in events:
            if event.group_id == GameCollisions.collision_group_bullets:
                self.__on_collision_bullet(event)


class VisualRadarSensor(VisualSensor):
    __slots__ = ()

    _CID = SensorCIDs.radar
    _sensor_type = RadarSensor
