"""
_sensors.py
10.03.2026

basic sensor prototypes

Author:
Nilusink
"""
import typing as tp

from ..base._groups import Players, Bullets

# if tp.TYPE_CHECKING:
from ..entities._base_entity import GameEntity


class BaseSensor:
    _parent: GameEntity

    @property
    def parent(self) -> GameEntity:
        return self._parent

    def get_targets(self, from_entities: tp.Iterable[GameEntity] = None) -> list[GameEntity]:
        raise NotImplementedError

    def update(self, delta: float) -> None:
        pass


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent
    """
    def __init__(
            self,
            parent: GameEntity,
            detection_range: float,
    ) -> None:
        self._parent = parent
        self._detection_range = detection_range

    @property
    def detection_range(self) -> float:
        return self._detection_range

    def get_targets(self, from_entities: tp.Iterable[GameEntity] = None) -> list[GameEntity]:
        if from_entities is None:
            targets = [p for p in Players.sprites() if p.alive]
            targets.extend(Bullets.sprites())

        else:
            targets = from_entities

        return [e[1] for e in Players.entities_in_circle(
            targets,
            self.parent.position,
            self.detection_range,
        )]
