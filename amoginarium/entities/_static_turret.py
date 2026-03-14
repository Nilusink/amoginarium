"""
_static_turret.py
18. March 2024

defines a player

Author:
Nilusink
"""
from contextlib import suppress
from time import perf_counter
from icecream import ic
import typing as tp

from ..base import HasBars, CollisionDestroyed, Players, Updated, Bullets, \
    GravityAffected
from ._weapons import BaseWeapon, Sniper, Ak47, Minigun, Mortar, Flak, CRAM
from ..logic import Vec2, calculate_launch_angle, Color, is_related, \
    normalize_angle
from ._base_entity import VisibleGameEntity
from ..radar import RadarSensor, BaseSensor, VisualSensor, DetectionGroup, \
    DETECTION_GLOBAL_BLUE, DETECTION_GLOBAL_NEUTRAL, DETECTION_GLOBAL_RED
from ..shared import global_vars, Coalitions
from ..render_bindings import renderer
from ..base._textures import textures


class BaseTurret(VisibleGameEntity):
    size: Vec2
    weapon: BaseWeapon
    _body_texture: int = ...
    # _body_texture_path: str = "static_turret_base"
    # _body_texture_size: tuple[int, int] = (64, 64)
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
            sensors: tp.Iterable[BaseSensor] = None
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

    @property
    def detection_group(self) -> DetectionGroup:
        if self.coalition == Coalitions.red:
            return DETECTION_GLOBAL_RED

        elif self.coalition == Coalitions.blue:
            return DETECTION_GLOBAL_BLUE

        return DETECTION_GLOBAL_NEUTRAL

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

    def get_next_target(self, include_all: bool = False) -> tp.Any:
        """
        returns the next best target to shoot at
        """
        targets = list(self.available_targets.keys())
        for target in sorted(
                targets, key=lambda t: self.available_targets[t]["distance"]
        ):
            t = self.available_targets[target]
            if include_all:
                return target

            if t["shot_at"] < -.5:
                return target

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

        # only check targets inside engagement envelope
        if self._valid_angles is not ...:
            targets = Players.entities_in_partial_circle(
                targets,
                self.position,
                self.engagement_range,
                *self._valid_angles,
                min_radius=self.min_range
            )

        else:
            targets = Players.entities_in_circle(
                targets,
                self.position,
                self.engagement_range,
                min_radius=self.min_range
            )

        # filter stuff shot by myself
        targets = [e for e in targets if not is_related(self, e[1], depth=4)]
        # targets = []

        for target in targets:
            if target[1] not in self.available_targets:
                self.available_targets[target[1]] = {
                    "shot_at": -self._number_target_taps,
                    "distance": target[0]
                }

        # make list only contain the entities
        targets = [value[1] for value in targets]
        for target in self.available_targets.copy():
            if target not in targets:
                self.available_targets.pop(target)
                continue

            if self.available_targets[target]["shot_at"] >= 0:
                self.available_targets[target]["shot_at"] -= delta

            elif self.available_targets[target]["shot_at"] > -1:
                self.available_targets[target]["shot_at"] = -self._number_target_taps

        new_target = self.get_next_target()
        simulate_target = self.get_next_target(True)
        if new_target is not None:
            self._last_shot = perf_counter()
            self._target_predict = [
                self.__shoot_at(new_target),
            ]

        # aim but don't shoot
        elif simulate_target is not None:
            self._target_predict = [
                self.__shoot_at(simulate_target, True),
            ]

        else:
            self._target = ...
            self._target_predict = []

        if perf_counter() - self._last_shot >= .1:
            self.weapon.stop_shooting()

        # check if reload
        if self.weapon.get_mag_state(1)[0] == 0:
            self.weapon.reload()

        super().update(delta)

    def __shoot_at(
            self,
            target: VisibleGameEntity,
            simulate: bool = False
    ) -> Vec2 | None:
        """
        shoot at specified target
        :param target:
        :param simulate: calculate & aim but don't shoot
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
                16,
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

            if self._valid_angles is not ...:
                angle_delta = normalize_angle(
                    self._valid_angles[1].angle
                    - self._valid_angles[0].angle
                )
                start2 = self._valid_angles[0].angle + angle_delta
                end2 = self._valid_angles[1].angle - angle_delta

                # check if firing-solution is inside engagement envelope
                if not any([
                    self._valid_angles[0].angle < aiming_angle.angle < start2,
                    self._valid_angles[1].angle > aiming_angle.angle > end2,
                ]):
                    return

            tof = min(
                tof,
                1.3 * self.engagement_range / self.weapon.bullet_speed
            )

            self._aiming_at = aiming_angle.copy()
            self._aiming_at.normalize()

            if simulate:
                return target_predict

            shot = self.weapon.shoot(
                aiming_angle,
                tof if self.airburst_munition else ...,
                target_pos=target_predict
            )

            if shot:
                if self.available_targets[target]["shot_at"] < -1:
                    self.available_targets[target]["shot_at"] += 1

                else:
                    self.available_targets[target]["shot_at"] = tof

            return target_predict

        return None

    def gl_draw(self) -> None:
        # only draw if on screen
        if not any([
            Updated.world_position.x < self.position.x - self.size.x / 2,
            self.position.x + self.size.x / 2 < Updated.world_position.x + 1920,
            Updated.world_position.y < self.position.y - self.size.y / 2,
            self.position.y + self.size.y / 2 < Updated.world_position.y + 1080,
        ]):
            return

        engage_center = self.world_position + self.weapon.parent_position_offset

        # weapon
        self.weapon.draw_at(
            self.position,
            self._aiming_at.angle * (180/3.14159265)
        )

        renderer.draw_textured_quad(
            self._body_texture,
            self.world_position - self.size / 2,
            self.size.xy
        )

        # draw engagement range
        if self._valid_angles is not ...:
            min_1 = self._valid_angles[0].copy()
            min_2 = self._valid_angles[1].copy()

            min_1.length = self.min_range
            min_2.length = self.min_range

            renderer.draw_line(
                engage_center + min_1,
                engage_center + self._valid_angles[0],
                Color.white()
            )

            renderer.draw_line(
                engage_center + min_2,
                engage_center + self._valid_angles[1],
                Color.white()
            )

            angle_delta = abs(normalize_angle(
                self._valid_angles[1].angle
                - self._valid_angles[0].angle
            ))
            segments = int(64 * (angle_delta / (2*3.1415926)))

            renderer.draw_partial_dashed_circle(
                engage_center,
                self.engagement_range,
                *self._valid_angles,
                num_segments=segments,
                color=Color.white(),
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
                Color.white(),
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

        # targets
        if global_vars.show_targets:
            if self._target is not ...:
                renderer.draw_line(
                    self.world_position + self.weapon.parent_position_offset,
                    self._target.world_position,
                    Color.from_255(255, 0, 0, 100)
                )
                renderer.draw_circle(
                    self._target.world_position,
                    global_vars.translate_scale(self._target.size.length / 2),
                    32,
                    Color.from_255(255, 0, 0, 100)
                )

            if self._target_predict is not ...:
                for target in self._target_predict:
                    if target is None:
                        continue

                    renderer.draw_line(
                        engage_center,
                        target - Updated.world_position,
                        Color.from_255(50, 200, 0, 100)
                    )
                    renderer.draw_circle(
                        target - Updated.world_position,
                        global_vars.translate_scale(32),
                        32,
                        Color.from_255(50, 200, 0, 100)
                    )

        super().gl_draw()

        debug_surface = self.mask.to_surface()
        renderer.draw_pg_surf(
            (
                self.rect.x - Updated.world_position.x,
                self.rect.y - Updated.world_position.y + self.size.y
            ),
            debug_surface
        )


class SniperTurret(BaseTurret):
    _max_hp: int = 40

    def __init__(self, coalition: Coalitions, position: Vec2) -> None:
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
            ]
        )


class AkTurret(BaseTurret):
    _max_hp: int = 60

    def __init__(self, coalition: Coalitions, position: Vec2) -> None:
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
            ]
        )


class MinigunTurret(BaseTurret):
    _max_hp: int = 60

    def __init__(self, coalition: Coalitions, position: Vec2) -> None:
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
            ]
        )


class MortarTurret(BaseTurret):
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

    def __init__(self, coalition: Coalitions, position: Vec2) -> None:
        self._coalition = coalition  # needed becauuse the weapon wants it
        weapon = Mortar(self, False, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(23*1.5, 24*1.5),
            position,
            weapon,
            1800,
            sensors=[
                RadarSensor(self, 1500)
            ]
        )


class FlakTurret(BaseTurret):
    _max_hp: int = 170
    _body_texture_path = "FLAK_base"
    _body_texture_size = (98, 44)
    _aim_type = "low"

    def __init__(self, coalition: Coalitions, position: Vec2) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Flak(self, True, parent_position_offset=(16, -26))
        weapon.reload(True)

        super().__init__(
            coalition,
            Vec2().from_cartesian(*self._body_texture_size)*2,
            position,
            weapon,
            1850,
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
            ]
        )


class CRAMTurret(BaseTurret):
    _max_hp: int = 60
    _body_texture_path = "CRAM_base"
    _body_texture_size = (64, 128)
    _aim_type = "low"

    def __init__(self, coalition: Coalitions, position: Vec2) -> None:
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
            ]
        )
