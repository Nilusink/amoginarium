"""
_static_turret.py
18. March 2024

defines a player

Author:
Nilusink
"""
from dataclasses import dataclass
from contextlib import suppress
from time import perf_counter
from icecream import ic
import typing as tp
import numpy as np

from amoginarium.logic.entities import HasBars, CollisionDestroyed, Players, Updated, Bullets, \
    GravityAffected
from ._weapons import BaseWeapon, Sniper, Ak47, Minigun, Mortar, Flak, CRAM
from amoginarium.shared.utility import Vec2, calculate_launch_angle, Color, is_related, \
    normalize_angle
from ._base_entity import VisibleGameEntity
from amoginarium.logic.radar import RadarSensor, BaseSensor, VisualSensor, DetectionGroup
from amoginarium.shared import pv, Coalitions, VisibleGameEntityLike
from amoginarium.graphics.render_bindings import renderer
from amoginarium.base._textures import textures


@dataclass
class TargetSolution:
    target: VisibleGameEntityLike
    target_predict: Vec2
    angle: Vec2
    tof: float


type target_solution_t = TargetSolution | None


class BaseTurret(VisibleGameEntity):
    size: Vec2
    weapon: BaseWeapon
    _body_texture: int = ...
    _body_texture_path = "mortar_turret_base"
    _body_texture_size = (23, 24)
    _weapon_texture: int | None = ...
    _weapon_texture_path: str | None
    _max_hp: int = 80
    _hp: int = 0
    _aim_type: tp.Literal["low", "high"] = "low"
    _target: tp.Any = ...
    _target_predict: list[Vec2] = ...
    available_targets: dict = ...
    _high_tof_multiplier: float = 1.1
    _number_target_taps: int

    def __new__(cls, *args, **kwargs):
        # only load texture once
        if cls._body_texture is ...:
            cls.load_textures()

        return super(BaseTurret, cls).__new__(cls)

    @classmethod
    def load_textures(cls) -> None:
        if cls._body_texture is ...:
            cls._body_texture, _ = textures.get_texture(
                cls._body_texture_path,
                cls._body_texture_size
            )

    def __init__(
            self,
            coalition: Coalitions,
            size: Vec2,
            position: Vec2,
            weapon: BaseWeapon,
            engagement_range: float,
            min_range: float = 0,
            airburst_munition: bool = False,
            intercept_bullets: bool = False,
            intercept_players: bool = True,
            target_taps: int = -1,
            valid_angles: tuple[Vec2, Vec2] = ...,
            sensors: tp.Iterable[BaseSensor] = None,
            detection_group: DetectionGroup = None,
    ) -> None:
        self._set_pos = position.copy()
        position.y -= size.y / 2

        self.weapon = weapon
        self.engagement_range = engagement_range
        self.min_range = min_range
        self.airburst_munition = airburst_munition
        self.intercept_bullets = intercept_bullets
        self.intercept_players = intercept_players
        self.available_targets = {}
        self._last_shot = perf_counter()
        self._aiming_at = Vec2().from_cartesian(-1, 0)
        self._valid_angles = valid_angles
        if self._valid_angles is not ...:
            self._valid_angles[0].length = self.engagement_range
            self._valid_angles[1].length = self.engagement_range

        if target_taps > 0:
            self._target_tapping = True
            self._number_target_taps = target_taps

        else:
            self._target_tapping = False
            self._number_target_taps = 1

        self._hp = self._max_hp

        super().__init__(
            size=size,
            initial_position=position,
            coalition=coalition
        )

        self.add(CollisionDestroyed, HasBars)

        if not detection_group:
            self.detection_group = DetectionGroup(str(self.id))

        else:
            self.detection_group = detection_group

        # create detection sensor
        self._sphere = []
        if sensors is not None:
            for sensor in sensors:
                self._children.append(sensor)
                self.detection_group.add_sensor(sensor)

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def hp(self) -> int:
        return self._hp

    # @property
    # def detection_group(self) -> DetectionGroup:
    #     if self.coalition == Coalitions.red:
    #         return DETECTION_GLOBAL_RED
    #
    #     elif self.coalition == Coalitions.blue:
    #         return DETECTION_GLOBAL_BLUE
    #
    #     return DETECTION_GLOBAL_NEUTRAL

    def hit(self, damage: float, hit_by: tp.Self = ...) -> None:
        """
        deal damage to the turret
        """
        self._hp -= damage

        # check for turret death
        if self._hp <= 0:
            self.kill(hit_by)

    def kill(self, killed_by=...):
        self.weapon.stop()
        super().kill(killed_by)

    def get_next_target(self, include_all: bool = False) -> target_solution_t:
        """
        returns the next best target to shoot at
        """
        targets = list(self.available_targets.keys())
        for target in sorted(
                targets, key=lambda t: self.available_targets[t]["distance"]
        ):
            t = self.available_targets[target]
            # don't even aim if predicted impact is oor
            if t["distance"] > self.engagement_range:
                continue

            if not t["solution"]:
                continue

            if include_all:
                return t["solution"]

            if t["shot_at"] < -.5:
                # check if firing solution inside engagement envelope
                if self._valid_angles is not ...:
                    angle_delta = normalize_angle(
                        self._valid_angles[1].angle
                        - self._valid_angles[0].angle
                    )
                    start2 = self._valid_angles[0].angle + angle_delta
                    end2 = self._valid_angles[1].angle - angle_delta

                    # check if firing-solution is inside engagement envelope
                    if not any([
                        self._valid_angles[0].angle < t["solution"].angle.angle < start2,
                        self._valid_angles[
                            1].angle > t["solution"].angle.angle > end2,
                    ]):
                        continue

                return t["solution"]

        # all targets have been shot at, so shoot at nothing
        # and reset shot_ats
        if not self._target_tapping:
            for target in self.available_targets:
                self.available_targets[target]["shot_at"] = -1

        # deleted because targets will now be shot at if last shot missed

        return None

    def update(self, delta):
        # update weapon
        self.weapon.update(delta)

        # scan for targets and engage the closest one
        targets = self.detection_group.targets

        # only check targets that are supposed to be engaged
        targets = [
            t for t in targets if any([
                t in Players.sprites() if self.intercept_players else False,
                t in Bullets.sprites() if self.intercept_bullets else False
            ])
        ]

        # filter stuff shot by myself
        targets = [e for e in targets if not is_related(self, e, depth=4)]

        for target in targets:
            if target not in self.available_targets:
                self.available_targets[target] = {
                    "shot_at": -self._number_target_taps,
                    "distance": None,
                    "solution": None
                }

        # make list only contain the entities
        for target in self.available_targets.copy():
            if target not in targets:
                self.available_targets.pop(target)
                continue

            if self.available_targets[target]["shot_at"] >= 0:
                sol = self._get_firing_solution(target)
                self.available_targets[target]["solution"] = sol
                self.available_targets[target]["shot_at"] -= delta

            elif self.available_targets[target]["shot_at"] > -1:
                self.available_targets[target]["shot_at"] = -self._number_target_taps

            else:
                sol = self._get_firing_solution(target)
                self.available_targets[target]["solution"] = sol
                if not sol:
                    self.available_targets[target]["distance"] = np.inf
                    continue

                self.available_targets[target]["distance"] = (
                    sol.target_predict
                    - self.position + self.weapon.parent_position_offset
                ).length

        new_target = self.get_next_target()
        simulate_target = self.get_next_target(True)
        if new_target is not None:
            self._last_shot = perf_counter()
            solution = self._get_firing_solution(new_target.target, 25)
            if solution is None:
                new_target = None

            else:
                self._target_predict = [solution.target_predict]
                self.__shoot_at(solution)

        # aim but don't shoot
        if new_target is None and simulate_target is not None:
            self._target_predict = [simulate_target.target_predict]
            self._aiming_at = simulate_target.angle.copy()
            self._aiming_at.normalize()

        else:
            self._target = ...
            self._target_predict = []

        if perf_counter() - self._last_shot >= .1:
            self.weapon.stop_shooting()

        # check if reload
        if self.weapon.get_mag_state(1)[0] == 0:
            self.weapon.reload()

        super().update(delta)

    def _get_firing_solution(
            self,
            target: VisibleGameEntityLike,
            recalc: int = 5
    ) -> TargetSolution | None:
        """
        aim at specified target
        :param target: target to aim at
        :returns:
        """
        player_velocity = target.velocity.copy()
        player_acceleration = target.acceleration.copy()

        self._target = target

        # if target is on ground, subtract gravitational acceleration
        if hasattr(target, "on_ground"):
            if target.on_ground:
                player_acceleration.y -= GravityAffected.gravity

        # if issubclass(Bullet, target.__class__)
        # if 1:  # target in Bullets.sprites():
        target_position = target.position

        # else:
        #     target_position = target.position_center

        position_delta = target_position - (
                self.position + self.weapon.parent_position_offset
        )
        position_delta.y *= -1
        player_velocity.y *= -1
        player_acceleration.y *= -1

        mirror = False
        if position_delta.x < 0:
            position_delta.x *= -1
            player_velocity.x *= -1
            player_acceleration.x *= -1
            mirror = True

        # try to negate effects of bullet spawning off-center
        # position_delta.length -= self.weapon.barrel_length / 2

        # try to predict where the player is going to be
        with suppress(ValueError):
            aiming_angle, tof, predict = calculate_launch_angle(
                position_delta,
                player_velocity,
                player_acceleration,
                self.weapon.bullet_speed,
                recalc,
                # 2 * position_delta.length / self.weapon.bullet_speed,
                self._aim_type,
                # *2 because for some reason I gave bullets 2x gravity
                g=GravityAffected.gravity * 2
            )

            aiming_angle.y *= -1
            predict.y *= -1

            if mirror:
                aiming_angle.x *= -1
                predict.x *= -1

            target_predict = self.position + self.weapon.parent_position_offset + predict

            if predict.length < self.min_range:
                return

            tof = min(
                tof,
                1.3 * self.engagement_range / self.weapon.bullet_speed
            )

            return TargetSolution(
                target_predict=target_predict,
                angle=aiming_angle,
                target=target,
                tof=tof,
            )

        return None

    def __shoot_at(
            self,
            solution: TargetSolution,
    ) -> None:
        """
        shoot at specified target
        :param solution: where to shoot to
        """
        self._aiming_at = solution.angle.copy()
        self._aiming_at.normalize()

        if self._valid_angles is not ...:
            angle_delta = normalize_angle(
                self._valid_angles[1].angle
                - self._valid_angles[0].angle
            )
            start2 = self._valid_angles[0].angle + angle_delta
            end2 = self._valid_angles[1].angle - angle_delta

            # check if firing-solution is inside engagement envelope
            if not any([
                self._valid_angles[0].angle < solution.angle.angle < start2,
                self._valid_angles[1].angle > solution.angle.angle > end2,
            ]):
                return

        shot = self.weapon.shoot(
            solution.angle,
            solution.tof if self.airburst_munition else ...,
            target_pos=solution.target_predict
        )

        if shot:
            if self.available_targets[solution.target]["shot_at"] < -1:
                self.available_targets[solution.target]["shot_at"] += 1

            else:
                self.available_targets[solution.target]["shot_at"] = solution.tof

    def gl_draw(self) -> None:
        # only draw engagement range if on screen
        if (
                self.position.x + self.engagement_range < Updated.world_position.x or
                self.position.x - self.engagement_range > Updated.world_position.x + pv.global_vars.screen_pixels.x or
                self.position.y + self.engagement_range < Updated.world_position.y or
                self.position.y - self.engagement_range > Updated.world_position.y + pv.global_vars.screen_pixels.y
        ):
            return

        engage_center = self.world_position + self.weapon.parent_position_offset

        # draw engagement range
        if self._valid_angles is not ...:
            min_1 = self._valid_angles[0].copy()
            min_2 = self._valid_angles[1].copy()

            min_1.length = self.min_range
            min_2.length = self.min_range

            renderer.draw_line(
                engage_center + min_1,
                engage_center + self._valid_angles[0],
                Color().from_1(1, 1, 1)
            )

            renderer.draw_line(
                engage_center + min_2,
                engage_center + self._valid_angles[1],
                Color().from_1(1, 1, 1)
            )

            angle_delta = abs(normalize_angle(
                self._valid_angles[1].angle
                - self._valid_angles[0].angle
            ))
            segments = int(64 * (angle_delta / (2 * 3.1415926)))

            renderer.draw_partial_dashed_circle(
                engage_center,
                self.engagement_range,
                *self._valid_angles,
                num_segments=segments,
                color=Color().from_1(1, 1, 1),
                thickness=3
            )

            if self.min_range > 0:
                renderer.draw_partial_dashed_circle(
                    engage_center,
                    self.min_range,
                    *self._valid_angles,
                    num_segments=segments // 2,
                    color=(1, .5, 0),
                    thickness=2
                )

        else:
            renderer.draw_dashed_circle(
                engage_center,
                self.engagement_range,
                64,
                Color().from_1(1, 1, 1),
                3
            )

            if self.min_range > 0:
                renderer.draw_dashed_circle(
                    engage_center,
                    self.min_range,
                    64,
                    (1, .5, 0),
                    3
                )

        # draw sensor ranges
        super().gl_draw()

        # targets
        if pv.global_vars.show_targets:
            if self._target is not ...:
                renderer.draw_line(
                    self.world_position + self.weapon.parent_position_offset,
                    self._target.world_position,
                    Color().from_255(255, 0, 0, 100)
                )
                renderer.draw_circle(
                    self._target.world_position,
                    pv.global_vars.translate_scale(self._target.size.length / 2),
                    32,
                    Color().from_255(255, 0, 0, 100)
                )

            if self._target_predict is not ...:
                for target in self._target_predict:
                    if target is None:
                        continue

                    renderer.draw_line(
                        engage_center,
                        target - Updated.world_position,
                        Color().from_255(50, 200, 0, 100)
                    )
                    renderer.draw_circle(
                        target - Updated.world_position,
                        pv.global_vars.translate_scale(32),
                        32,
                        Color().from_255(50, 200, 0, 100)
                    )

        # only draw turret if on screen
        if (
                self.position.x + self.size.x / 2 < Updated.world_position.x or
                self.position.x - self.size.x / 2 > Updated.world_position.x + pv.global_vars.screen_pixels.x or
                self.position.y + self.size.y / 2 < Updated.world_position.y or
                self.position.y - self.size.y / 2 > Updated.world_position.y + pv.global_vars.screen_pixels.y
        ):
            return

        if self._highlight:
            renderer.start_stencil(True)

        # weapon
        self.weapon.draw_at(
            self.position,
            self._aiming_at.angle * (180 / 3.14159265)
        )

        renderer.draw_textured_quad(
            self._body_texture,
            self.world_position - self.size / 2,
            self.size
        )

        if self._highlight:
            renderer.enable_stencil(True)

            renderer.draw_rect(
                self.world_position - self.size,
                self.size * 2,
                (1, 1, 1, .5)
            )

            renderer.disable_stencil()

        # debug_surface = self.mask.to_surface()
        # renderer.draw_pg_surf(
        #     (
        #         self.rect.x - Updated.world_position.x,
        #         self.rect.y - Updated.world_position.y + self.size.y
        #     ),
        #     debug_surface
        # )


class SniperTurret(BaseTurret):
    _cid = "turret.static.sniper"
    _max_hp: int = 40

    def __init__(
            self,
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Sniper(self, True, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(31, 32),
            position,
            weapon,
            2400,
            sensors=[
                VisualSensor(self, 2500, sphere_accuracy=256)
            ],
            **kwargs
        )


class AkTurret(BaseTurret):
    _cid = "turret.static.ak47"
    _max_hp: int = 60

    def __init__(
            self,
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Ak47(self, False, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(31, 32),
            position,
            weapon,
            1500,
            sensors=[
                VisualSensor(self, 1500)
            ],
            **kwargs
        )


class MinigunTurret(BaseTurret):
    _cid = "turret.static.minigun"
    _max_hp: int = 60

    def __init__(
            self,
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Minigun(self, False, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(48, 48),
            position,
            weapon,
            2000,
            sensors=[
                VisualSensor(self, 1500)
            ],
            **kwargs
        )


class MortarTurret(BaseTurret):
    _cid = "turret.static.mortar"
    _max_hp: int = 90
    _aim_type = "high"
    _body_texture_path = "mortar_turret_base"
    _body_texture_size = (23, 24)

    @classmethod
    def load_textures(cls) -> None:
        if cls._body_texture is ...:
            ic(cls._body_texture_path)
            cls._body_texture, _ = textures.get_texture(
                cls._body_texture_path,
                cls._body_texture_size
            )

    def __init__(
            self,
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed becauuse the weapon wants it
        weapon = Mortar(self, False, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(23 * 1.5, 24 * 1.5),
            position,
            weapon,
            1800,
            sensors=[
                RadarSensor(self, 1500)
            ],
            **kwargs
        )


class FlakTurret(BaseTurret):
    _cid = "turret.static.flak"
    _max_hp: int = 170
    _body_texture_path = "FLAK_base"
    _body_texture_size = (98, 44)
    _aim_type = "low"

    def __init__(
            self,
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Flak(self, True, parent_position_offset=(16, -26))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(*self._body_texture_size) * 2,
            position,
            weapon,
            2300,
            300,
            airburst_munition=True,
            intercept_bullets=False,
            target_taps=2,
            valid_angles=(
                Vec2().from_cartesian(-1, .3),
                Vec2().from_cartesian(-.1, -1)
            ),
            sensors=[
                VisualSensor(self, 1700)
            ],
            **kwargs
        )


class CRAMTurret(BaseTurret):
    _cid = "turret.static.cram"
    _max_hp: int = 60
    _body_texture_path = "CRAM_base"
    _body_texture_size = (64, 128)
    _aim_type = "low"

    def __init__(
            self,
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = CRAM(
            self,
            False,
            parent_position_offset=(0, 15)
        )  # don't eject casings because I like my pc
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(64, 128),
            position,
            weapon,
            1900,
            150,
            intercept_bullets=True,
            intercept_players=False,
            airburst_munition=True,
            target_taps=4,
            valid_angles=(
                Vec2().from_cartesian(-.5, 1),
                Vec2().from_cartesian(.5, 1)
            ),
            sensors=[
                RadarSensor(
                    self,
                    1500,
                    sphere_accuracy=256,
                    min_rcs=.04
                )
            ],
            **kwargs
        )
