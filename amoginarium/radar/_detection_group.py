"""
_detection_group.py
10.03.2026

"Data-link" to share target informatino

Author:
Nilusink
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from icecream import ic
import typing as tp

from ..base._groups import Bullets, Players
from ._sensors import BaseSensor
from ..debugging import run_with_debug, CC

if tp.TYPE_CHECKING:
    from ..entities._base_entity import GameEntity


@dataclass(frozen=False)
class TargetInfo:
    last_seen: float
    seen_by: GameEntity


class _DetectionGroupManager:
    _instance: _DetectionGroupManager = ...
    _detection_groups: list[DetectionGroup]

    def __new__(cls, *args, **kwargs):
        if cls._instance is ...:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self._detection_groups = []

    def add(self, group: DetectionGroup) -> None:
        self._detection_groups.append(group)

    def remove(self, group: DetectionGroup) -> None:
        if group in self._detection_groups:
            self._detection_groups.remove(group)

    def get_all(self) -> list[DetectionGroup]:
        return self._detection_groups.copy()

    # will later be used for target tracks
    # def update(self, delta: float) -> None:
    #     for group in self._detection_groups:
    #         group.update(delta)

    def update_detection(self) -> None:
        """
        ask all sensors to get their targeting information
        """
        # create targets list once so it doesn't get re-checked
        # for every sensor
        targets = [p for p in Players.sprites() if p.alive]
        targets.extend(Bullets.sprites())

        for group in self._detection_groups:
            group.update_detection(targets)

    def reset(self) -> None:
        """
        reset all target groups each loop so targets won't
        be visible forever
        """
        for group in self._detection_groups:
            group.reset()


detection_id: int = 0
class DetectionGroup:
    _targets: dict[GameEntity, TargetInfo]
    _sensors: list[BaseSensor]

    def __new__(cls, *args, **kwargs):
        i = super().__new__(cls)
        DETECTION_GROUP_MANAGER.add(i)
        return i

    def __init__(
            self,
            name: str = None
    ) -> None:
        global detection_id

        # assign unique id
        self.__id = detection_id
        detection_id += 1

        self._name = name
        self._targets = {}
        self._sensors = []

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self._name

    @property
    def targets(self) -> list[GameEntity]:
        return list(self._targets.keys())

    @property
    def sensors(self) -> list[BaseSensor]:
        return self._sensors.copy()

    def add_target(
            self,
            target: GameEntity | tp.Iterable[GameEntity],
            detector: GameEntity
    ) -> None:
        """
        add target to detection scope
        """
        if isinstance(target, tp.Iterable):
            for t in target:
                if t not in self._targets:
                    self._targets[t] = TargetInfo(
                        last_seen=perf_counter(),
                        seen_by=detector
                    )
            return

        if target not in self._targets:
            self._targets[target] = TargetInfo(
                last_seen=perf_counter(),
                seen_by=detector
            )

    def add_sensor(self, sensor: BaseSensor) -> None:
        """
        adds a sensor to detection scope
        """
        self._sensors.append(sensor)
        sensor.group_add(self)

    def remove_sensor(self, sensor: BaseSensor) -> None:
        """
        remove a sensor
        """
        if sensor in self._sensors:
            self._sensors.remove(sensor)
        #
        # else:
        #     ic(CC.fg.RED + "sensor not in list!")

    def update_detection(
            self,
            from_entities: tp.Iterable[GameEntity] = None
    ) -> None:
        """
        ask all sensors to get their targeting information
        """
        for sensor in self._sensors:
            self.add_target(
                sensor.get_targets(from_entities),
                sensor.parent
            )

    # def update(self, delta: float) -> None:
    #     now = perf_counter()
    #     for target, info in self._targets.items():
    #         if now - info.last_seen > ...:

    def reset(self) -> None:
        self._targets.clear()

    def __str__(self) -> str:
        return f"<Detection group \"{self.name}\", id \"{self.id}\">"

    def __repr__(self) -> str:
        return self.__str__()


DETECTION_GROUP_MANAGER = _DetectionGroupManager()
DETECTION_GLOBAL_RED = DetectionGroup("RED")
DETECTION_GLOBAL_BLUE = DetectionGroup("BLUE")
DETECTION_GLOBAL_NEUTRAL = DetectionGroup("NEUTRAL")
