"""
Base class for logic entities handling spatial detection and targeting.

Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_base_sensor.py
Project: amoginarium
Created: 10.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

import numpy as np

from amoginarium import pv
from amoginarium.shared import BaseCommandType, ProcessCommand, SensorCIDs
from amoginarium.shared.utility import convert_coord, MASK16, pack_int, Vec2

from ...._base import PositionedLogicEntity, Updated

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t
    from amoginarium.shared.utility import coord_t

    from ...._base import LogicGameEntity
    from ...templates import DetectionGroup


class BaseSensor(PositionedLogicEntity):
    """
    sensor entity.

    ``param0`` detection range
    """

    _CID = SensorCIDs.hud
    _has_sectors: tp.ClassVar[bool] = False

    _parent: PositionedLogicEntity
    _visible: bool
    _min_rcs: float = 0

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        detection_range: float,
        position_offset: coord_t = ...,
        *,
        visible: bool = True,
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer, position=Vec2(), size=Vec2(), parent=parent
        )
        self.remove(Updated)
        self._buffer.param0 = detection_range

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
        self._values_per_param = 64 // bits_per_value

        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs={
                    "id": self.id,
                    "cid": self.cid(),
                    "sectors": self._sphere,
                    "min_rcs": self._min_rcs,
                    "vpp": self._values_per_param,
                },
            )
        )
        self._update(0)

    @property
    def detection_range(self) -> float:
        return self._detection_range

    @property
    def parent(self) -> LogicGameEntity:
        return self._parent

    def _calculate_sphere(self) -> list[Vec2]:
        """
        Calculate detection sphere.
        """
        angle_step = (np.pi * 2) / self._sphere_accuracy

        out = []
        for i in range(self._sphere_accuracy):
            curr_angle = i * angle_step
            out.append(Vec2().from_polar(curr_angle, self.detection_range))

        return out

    def group_add(self, group: DetectionGroup) -> None:
        self._detection_group = group

    def get_targets(
        self, delta: float, from_entities: tp.Iterable[LogicGameEntity] | None = None
    ) -> list[LogicGameEntity]:
        raise NotImplementedError

    def _update(self, delta: float) -> None:
        if hasattr(self.parent, "position"):
            self.position = self.parent.position + self._position_offset

        super()._update(delta)

        # set target
        if self._targets:
            self._buffer.param1 = self._targets[0].position.x
            self._buffer.param2 = self._targets[0].position.y

        else:
            self._buffer.param1 = 0
            self._buffer.param2 = 0

        # write sectors
        self._buffer.param3 = -1
        self._buffer.param4 = -1
        sectors = self._highlighted_sectors.copy()
        self._highlighted_sectors.clear()
        if sectors:
            if len(sectors) > self._values_per_param:
                self._buffer.param3 = pack_int(
                    64, self._values_per_param, sectors[: self._values_per_param]
                )

                if len(sectors) > 2 * self._values_per_param:
                    self._buffer.param4 = pack_int(
                        64,
                        self._values_per_param,
                        sectors[self._values_per_param : 2 * self._values_per_param],
                    )

                else:
                    self._buffer.param4 = pack_int(
                        64,
                        self._values_per_param,
                        sectors[self._values_per_param :]
                        + [MASK16] * (2 * self._values_per_param - len(sectors)),
                    )

            else:
                self._buffer.param3 = pack_int(
                    64,
                    self._values_per_param,
                    sectors + [MASK16] * (self._values_per_param - len(sectors)),
                )

    def _kill(self, *_args: tp.Any, **_kwargs: tp.Any) -> None:
        if self._detection_group:
            self._detection_group.remove_sensor(self)

        super()._kill(*_args, **_kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} range={self.detection_range}>"
