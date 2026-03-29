"""
_sensors.py
14.03.2026

detection-based entities

Author:
Nilusink
"""
import typing as tp

from amoginarium.base._textures import textures
from ..entities import CollisionDestroyed, HasBars, Updated
from ._base_entity import VisibleGameEntity
from amoginarium.logic.radar import RadarSensor, BaseSensor, DetectionGroup
from amoginarium.shared import BaseEntityLike, pv.global_vars
from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared.utility import Vec2


class BaseDetector(VisibleGameEntity):
    _body_texture_path: str | tuple[str, str] = "amogus64right"
    _body_texture_size: tuple[int, int] = (64, 64)
    _max_hp: int = 30

    def __init__(
            self,
            sensors: tp.Iterable[BaseSensor],
            size: Vec2 = ...,
            facing: Vec2 = ...,
            initial_position: Vec2 = ...,
            initial_velocity: Vec2 = ...,
            coalition: tp.Any = ...,
            parent: BaseEntityLike = None,
            detection_group: DetectionGroup = ...,
    ) -> None:
        super().__init__(
            size,
            facing=facing,
            initial_velocity=initial_velocity,
            initial_position=initial_position,
            coalition=coalition,
            parent=parent
        )

        if isinstance(self._body_texture_path, str):
            self._body_texture, _ = textures.get_texture(
                self._body_texture_path,
                self._body_texture_size,
            )

        else:
            self._body_texture, _ = textures.get_texture(
                self._body_texture_path[1],
                self._body_texture_size,
                self._body_texture_path[0],
            )

        # reset stuff
        self._hp = self._max_hp

        self.add(CollisionDestroyed, HasBars)

        if not detection_group:
            self.detection_group = DetectionGroup(str(self.id))

        else:
            self.detection_group = detection_group

        if sensors is not None:
            for sensor in sensors:
                self._children.append(sensor)
                self.detection_group.add_sensor(sensor)

    # @property
    # def detection_group(self) -> DetectionGroup:
    #     if self.coalition == Coalitions.red:
    #         return DETECTION_GLOBAL_RED
    #
    #     elif self.coalition == Coalitions.blue:
    #         return DETECTION_GLOBAL_BLUE
    #
    #     return DETECTION_GLOBAL_NEUTRAL

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def engagement_range(self) -> float:
        return max(s.detection_range for s in self._children)

    def hit(self, damage: float, hit_by: tp.Self = ...) -> None:
        """
        deal damage to the turret
        """
        self._hp -= damage

        # check for turret death
        if self._hp <= 0:
            self.kill(hit_by)

    def kill(self, killed_by: tp.Self = ...) -> None:
        self._children[0].kill()
        super().kill(killed_by)

    def gl_draw(self) -> None:
        # only draw if on screen
        er = self.engagement_range
        if not (
            self.position.x + er < Updated.world_position.x or
            self.position.x - er > Updated.world_position.x + pv.global_vars.screen_pixels.x or
            self.position.y + er < Updated.world_position.y or
            self.position.y - er > Updated.world_position.y + pv.global_vars.screen_pixels.y
        ):
            renderer.draw_textured_quad(
                self._body_texture,
                self.world_position - self.size / 2,
                self.size.xy
            )

        super().gl_draw()


class Radar(BaseDetector):
    _cid = "sensor.static.radar"
    _body_texture_path: str | tuple[str, str] = "amogus64right"
    _body_texture_size: tuple[int, int] = (64, 64)

    def __init__(
            self,
            position: Vec2,
            coalition: tp.Any,
            detection_range: float = 2000,
            min_rcs: float = .001,
            sphere_accuracy: int = 512,
            parent: BaseEntityLike = None,
            detection_group: DetectionGroup = None
    ) -> None:
        super().__init__(
            [
                RadarSensor(
                    self,
                    detection_range,
                    sphere_accuracy=sphere_accuracy,
                    min_rcs=min_rcs
                )
            ],
            size=Vec2().from_cartesian(*self._body_texture_size),
            initial_position=position,
            coalition=coalition,
            parent=parent,
            detection_group=detection_group
        )
