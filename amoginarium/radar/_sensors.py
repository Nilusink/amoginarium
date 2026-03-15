"""
_sensors.py
10.03.2026

basic sensor prototypes

Author:
Nilusink
"""
from icecream import ic
import typing as tp

from ..debugging import run_with_debug
from ..logic import coord_t, convert_coord, Vec2
from ..base._groups import Players, Bullets
from ..render_bindings import renderer

# if tp.TYPE_CHECKING:
from ..entities._base_entity import GameEntity, VisibleBaseEntity


class BaseSensor(VisibleBaseEntity):
    _parent: GameEntity
    _visible: bool

    def __init__(
            self,
            parent: GameEntity,
            detection_range: float,
            position_offset: coord_t = ...,
            visible: bool = True
    ) -> None:
        self._detection_range = detection_range
        self._visible = visible
        if position_offset is ...:
            self._position_offset = Vec2()

        else:
            self._position_offset = convert_coord(position_offset, Vec2)

        self._detection_group = None

        super().__init__(parent)

    @property
    def detection_range(self) -> float:
        return self._detection_range

    @property
    def parent(self) -> GameEntity:
        return self._parent

    def group_add(self, group) -> None:
        self._detection_group = group

    def get_targets(
            self,
            from_entities: tp.Iterable[GameEntity] = None
    ) -> list[GameEntity]:
        raise NotImplementedError

    def kill(self, *_args, **_kwargs) -> None:
        if self._detection_group:
            self._detection_group.remove_sensor(self)

        super().kill()

    def gl_draw(self, draw: bool = True) -> None:
        if self._visible and draw:
            renderer.draw_line_circle(
                self.parent.world_position + self._position_offset,
                self.detection_range,  # * ((self._current_t % a_time) / a_time)**2,
                64,
                (.3, .3, 1, .6),
                thickness=1
            )

        super().gl_draw()


class MagicSensor(BaseSensor):
    """
    magically gets all targets inside a certain range
    of parent
    """
    def get_targets(self, from_entities: tp.Iterable[GameEntity] = None) -> list[GameEntity]:
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

