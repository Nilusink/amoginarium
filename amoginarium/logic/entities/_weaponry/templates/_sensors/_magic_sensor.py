"""
Sensor detecting all entities within a specific circular range.

| Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_magic_sensor.py
| Project: amoginarium
| Created: 18.04.2026
| Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import SensorCIDs

from ...._base import Bullets, Players
from ._base_sensor import BaseSensor

if tp.TYPE_CHECKING:
    from ...._base import LogicGameEntity


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent.

    ``param0`` detection range
    """

    _CID = SensorCIDs.sensor_magic

    @tp.override
    def get_targets(
        self, from_entities: tp.Iterable[LogicGameEntity] | None = None
    ) -> list[LogicGameEntity]:
        if from_entities is None:
            targets = [p for p in Players.entities() if p.alive]
            targets.extend(Bullets.entities())

        else:
            targets = from_entities

        self._targets = [
            e[1]
            for e in Players.entities_in_circle(
                targets,
                self.parent.position + self._position_offset,
                self.detection_range,
            )
        ]

        return self._targets.copy()
