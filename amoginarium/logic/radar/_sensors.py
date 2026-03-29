"""
_sensors.py
10.03.2026

basic sensor prototypes

Author:
Nilusink
"""
import typing as tp

from ...shared.utility import coord_t, convert_coord, Vec2
from ..entities import PositionedLogicEntity, LogicGameEntity
from ..entities import Players, Bullets

# if tp.TYPE_CHECKING:
# from ..entities import GameEntity, VisibleBaseEntity, Players, Bullets


class BaseSensor:
    _parent: PositionedLogicEntity
    _visible: bool

    def __init__(
            self,
            parent: PositionedLogicEntity,
            detection_range: float,
            position_offset: coord_t = ...,
            visible: bool = True
    ) -> None:
        self._detection_range = detection_range
        self._visible = visible
        self._parent = parent
        if position_offset is ...:
            self._position_offset = Vec2()

        else:
            self._position_offset = convert_coord(position_offset, Vec2)

        self._detection_group = None

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

    def kill(self, *_args, **_kwargs) -> None:
        if self._detection_group:
            self._detection_group.remove_sensor(self)

    @tp.final
    def gl_draw(self) -> None:
        raise RuntimeError("trying to gl_draw in logic")


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent
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
