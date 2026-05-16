"""
amoginarium/logic/entities/_sensors/_magic_sensor.py

Project: amoginarium
Created: 18.04.2026
Authors: Nilusink, LukasKrah
"""

import typing as tp

from amoginarium.shared import SensorCIDs

from ...._base import Bullets, LogicGameEntity, Players
from ._base_sensor import BaseSensor


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent

    ``param0`` detection range
    """

    _CID = SensorCIDs.sensor_magic

    def get_targets(
        self, from_entities: tp.Iterable[LogicGameEntity] = None
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
