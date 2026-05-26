"""
"Data-link" to share target information.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_sensors/_detection_group.py
| ``Project``: amoginarium
| ``Created``: 10.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass
from time import perf_counter
from types import EllipsisType

from icecream import ic

from amoginarium.shared.utility import RadarTrack2D, TrackState

from ...._base import Bullets, Dead, DebugPolygonEntity, GravityAffected, Updated, Walls

if tp.TYPE_CHECKING:
    from ...._base import LogicGameEntity, PositionedLogicEntity
    from ._base_sensor import BaseSensor


@dataclass(frozen=False)
class TargetInfo:
    """target info."""

    last_seen: float
    seen_by: PositionedLogicEntity


class _DetectionGroupManager:
    """manages all detection groups."""

    _instance: tp.ClassVar[tp.Self | EllipsisType] = ...
    _detection_groups: list[DetectionGroup]

    def __new__(cls, *args: tp.Any, **kwargs: tp.Any) -> tp.Self:  # noqa: ARG004
        if isinstance(cls._instance, EllipsisType):
            instance = super().__new__(cls)

            cls._instance = instance
            return instance

        return cls._instance

    def __init__(self) -> None:
        self._detection_groups = []
        self.__current_id: int = 0

    def get_id(self) -> int:
        """Get new detection group ID."""
        dg_id = self.__current_id
        self.__current_id += 1
        return dg_id

    def add(self, group: DetectionGroup) -> None:
        self._detection_groups.append(group)

    def remove(self, group: DetectionGroup) -> None:
        if group in self._detection_groups:
            self._detection_groups.remove(group)

    def get_all(self) -> list[DetectionGroup]:
        return self._detection_groups.copy()

    def update_detection(self, delta: float) -> None:
        """
        Ask all sensors to get their targeting information.
        """
        # create targets list once so it doesn't get re-checked
        # for every sensor
        walls = Walls.entities()

        # create base group of targets that are viable for detection
        targets = [
            t
            for t in Bullets.entities() + Updated.entities()
            if hasattr(t, "coalition") and t not in walls and t.alive
        ]
        dead = Dead.entities()

        for group in self._detection_groups:
            group.update_detection(delta, from_entities=targets, dead_entities=dead)

    def reset(self) -> None:
        """
        Reset all target groups each loop so targets won't be visible forever.
        """
        for group in self._detection_groups:
            group.reset()


class DetectionGroup:
    """Group of sensors."""

    _DEBUG: tp.ClassVar[bool] = False

    _targets: dict[PositionedLogicEntity, TargetInfo]
    _tracks: dict[int, RadarTrack2D]
    _sensors: list[BaseSensor]

    @tp.override
    def __new__(cls, *args: tp.Any, **kwargs: tp.Any) -> tp.Self:
        i = super().__new__(cls)
        DETECTION_GROUP_MANAGER.add(i)
        return i

    def __init__(self, name: str | None = None) -> None:
        # assign unique id
        self.__id = DETECTION_GROUP_MANAGER.get_id()

        self._name = name
        self._targets = {}
        self._tracks = {}
        self._sensors = []

        if self._DEBUG:
            self._debug_entities = {}

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def targets(self) -> list[PositionedLogicEntity]:
        return list(self._targets.keys())

    @property
    def tracks(self) -> list[RadarTrack2D]:
        return list(self._tracks.values())

    @property
    def sensors(self) -> list[BaseSensor]:
        return self._sensors.copy()

    def _add_target(
        self,
        target: LogicGameEntity,
        detector: PositionedLogicEntity,
        delta: float,
    ) -> None:
        if target not in self._targets:
            self._targets[target] = TargetInfo(
                last_seen=perf_counter(), seen_by=detector
            )

        # try to get velocity from target, else velocity=0
        velocity = (target.position - target.last_position) / target.last_delta
        tid = target.id

        if target.id not in self._tracks:
            g = GravityAffected.gravity

            if target in Bullets.entities():
                g *= 2

            self._tracks[tid] = RadarTrack2D()
            self._tracks[tid].initialize(
                *target.position.xy,
                *velocity.xy,
                g=g,
            )
            self._tracks[tid].set_size(*target.size.xy)

            if self._DEBUG:
                self._debug_entities[tid] = DebugPolygonEntity(
                    target.runtime_buffer, point_radius=8, fill_color=(0, 0, 0, 0)
                )

        else:
            self._tracks[tid].step(*target.position.xy, *velocity.xy, delta)

    def add_target(
        self,
        target: PositionedLogicEntity | tp.Iterable[PositionedLogicEntity],
        detector: PositionedLogicEntity,
        delta: float,
    ) -> None:
        """
        Add target to detection scope.
        """
        if isinstance(target, tp.Iterable):
            for t in target:
                self._add_target(t, detector, delta)

            return

        self._add_target(target, detector, delta)

    def add_sensor(self, sensor: BaseSensor) -> None:
        """
        Add a sensor to detection scope.
        """
        self._sensors.append(sensor)
        sensor.group_add(self)

    def remove_sensor(self, sensor: BaseSensor) -> None:
        """
        Remove a sensor.
        """
        if sensor in self._sensors:
            self._sensors.remove(sensor)

    def update_detection(
        self,
        delta: float,
        *,
        from_entities: tp.Iterable[LogicGameEntity] | None = None,
        dead_entities: tp.Iterable[LogicGameEntity] | None = None,
    ) -> None:
        """
        Ask all sensors to get their targeting information.
        """
        for tid, track in self._tracks.copy().items():
            if self._DEBUG:
                self._debug_entities[tid].p1 = track.get_position()
                self._debug_entities[tid].p2 = track.predict_future_position(0.25 / 2)
                self._debug_entities[tid].p3 = track.predict_future_position(0.25)
                self._debug_entities[tid].p4 = track.predict_future_position(0.75 / 2)
                self._debug_entities[tid].p5 = track.predict_future_position(0.5)

            # check if track has marked itself as dead in last iteration
            if track.state == TrackState.DEAD:
                self._tracks.pop(tid)
                self._debug_entities.pop(tid).kill()

            # increment track time and predicted position
            track.increment_time(delta)

        for sensor in self._sensors:
            self.add_target(
                sensor.get_targets(delta, from_entities=from_entities),
                sensor.parent,
                delta,
            )

        # mark tracks from dead entities as dead
        if dead_entities:
            for entity in dead_entities:
                if entity.id in self._tracks:
                    self._tracks[entity.id].kill()

    def reset(self) -> None:
        self._targets.clear()

    def __str__(self) -> str:
        return f'<Detection group "{self.name}", id "{self.id}">'

    def __repr__(self) -> str:
        return self.__str__()


DETECTION_GROUP_MANAGER = _DetectionGroupManager()
DETECTION_GLOBAL_RED = DetectionGroup("RED")
DETECTION_GLOBAL_BLUE = DetectionGroup("BLUE")
DETECTION_GLOBAL_NEUTRAL = DetectionGroup("NEUTRAL")
