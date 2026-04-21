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
import numpy as np

from amoginarium.shared import base_entity_t, SensorCIDs, ProcessCommand
from amoginarium.shared.utility import coord_t, convert_coord, Vec2
from amoginarium.shared.utility import pack_int, MASK16
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
    _has_sectors: float = 0
    _min_rcs: float = 0

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
        self._targets = []
        self._sphere = self._calculate_sphere()
        self._highlighted_sectors = []

        bits_per_value = len(self._sphere).bit_length()  # make sure +1 is available
        self._values_per_param = 64//bits_per_value

        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs={
                    "id": self.id,
                    "cid": self.cid(),
                    "sectors": self._sphere,
                    "min_rcs": self._min_rcs,
                    "vpp": self._values_per_param
                },
            )
        )
        self._update(0)

    @property
    def detection_range(self) -> float:
        return self._detection_range

    @property
    def parent(self) -> PositionedLogicEntity:
        return self._parent

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

        # set target
        if self._targets:
            self._buff.param1 = self._targets[0].position.x
            self._buff.param2 = self._targets[0].position.y

        else:
            self._buff.param1 = 0
            self._buff.param2 = 0

        # write sectors sectors
        self._buff.param3 = -1
        self._buff.param4 = -1
        sectors = self._highlighted_sectors.copy()
        self._highlighted_sectors.clear()
        if sectors:
            if len(sectors) > self._values_per_param:
                self._buff.param3 = pack_int(
                    64, self._values_per_param, sectors[: self._values_per_param]
                )

                if len(sectors) > 2*self._values_per_param:
                    self._buff.param4 = pack_int(
                        64,
                        self._values_per_param,
                        sectors[self._values_per_param:2 * self._values_per_param],
                    )

                else:
                    self._buff.param4 = pack_int(
                        64,
                        self._values_per_param,
                        sectors[self._values_per_param:]
                        + [MASK16] * (2*self._values_per_param - len(sectors)),
                    )

            else:
                self._buff.param3 = pack_int(
                    64,
                    self._values_per_param,
                    sectors + [MASK16] * (self._values_per_param - len(sectors)),
                )

    def kill(self, *_args, **_kwargs) -> None:
        if self._detection_group:
            self._detection_group.remove_sensor(self)

        super().kill(*_args, **_kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} range={self.detection_range}>"


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent

    ``param0`` detection range
    """

    _cid = SensorCIDs.sensor_magic

    def get_targets(
            self,
            from_entities: tp.Iterable[LogicGameEntity] = None
    ) -> list[LogicGameEntity]:
        if from_entities is None:
            targets = [p for p in Players.sprites() if p.alive]
            targets.extend(Bullets.sprites())

        else:
            targets = from_entities

        self._targets = [e[1] for e in Players.entities_in_circle(
            targets,
            self.parent.position + self._position_offset,
            self.detection_range,
        )]

        return self._targets.copy()
