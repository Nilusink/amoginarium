"""
_sensors.py
10.03.2026

basic sensor prototypes

Author:
Nilusink
"""

from ctypes import Array
from icecream import ic
import typing as tp

from amoginarium.shared import base_entity_t, SensorCIDs, ProcessCommand
from amoginarium.shared.utility import coord_t, convert_coord, Vec2
from amoginarium.shared import BaseCommandType
from amoginarium import pv

from ._base_entity import PositionedLogicEntity, LogicGameEntity
from ._logic_groups import Players, Bullets, Updated


class BaseSensor(PositionedLogicEntity):
    """
    sensor entity

    ``param0`` detection range
    """

    _cid = SensorCIDs.hud
    _parent: PositionedLogicEntity
    _visible: bool
    _has_sectors: bool = False

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent: PositionedLogicEntity,
            detection_range: float,
            position_offset: coord_t = ...,
            visible: bool = True,
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer, position=Vec2(), size=Vec2(), parent=parent
        )
        self.remove(Updated)
        self._buff.param0 = detection_range

        self._detection_range = detection_range
        self._visible = visible
        self._parent = parent
        if position_offset is ...:
            self._position_offset: Vec2 = Vec2()

        else:
            self._position_offset: Vec2 = convert_coord(position_offset, Vec2)

        self._detection_group = None

        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={"id": self.id, "cid": self.cid(), "sectors": self._has_sectors}
        ))
        self._update(0)

    @property
    def detection_range(self) -> float:
        return self._detection_range

    @property
    def parent(self) -> PositionedLogicEntity:
        return self._parent

    def group_add(self, group) -> None:
        self._detection_group = group

    def get_targets(
            self,
            from_entities: tp.Iterable[LogicGameEntity] = None
    ) -> list[LogicGameEntity]:
        raise NotImplementedError

    def _update(self, delta: float) -> None:
        if hasattr(self.parent, "position"):
            self.position = self.parent.position + self._position_offset
            # ic(self.position, self._buff.param0)

        super()._update(delta)

    def kill(self, *_args, **_kwargs) -> None:
        if self._detection_group:
            self._detection_group.remove_sensor(self)

        super().kill(*_args, **_kwargs)


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent

    ``param0`` detection range
    """

    def get_targets(
            self,
            from_entities: tp.Iterable[LogicGameEntity] = None
    ) -> list[LogicGameEntity]:
        if from_entities is None:
            targets = [p for p in Players.sprites() if p.alive]
            targets.extend(Bullets.sprites())

        else:
            targets = from_entities

        return [e[1] for e in Players.entities_in_circle(
            targets,
            self.parent.position + self._position_offset,
            self.detection_range,
        )]
