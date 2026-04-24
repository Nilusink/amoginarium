"""
amoginarium/logic/entities/_turrets/_base_turret.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from dataclasses import dataclass
from contextlib import suppress
from types import EllipsisType
from time import perf_counter
from ctypes import Array
import typing as tp
import numpy as np
import ctypes

from amoginarium.shared import Coalitions, VisibleGameEntityLike, base_entity_t
from amoginarium.shared import ProcessCommand, BaseCommandType
from amoginarium.shared.utility import is_related, normalize_angle, MASK32
from amoginarium.shared.utility import Vec2, calculate_launch_angle, MASK16
from amoginarium.shared.utility import MASK64, get_default
from amoginarium import pv
from shared.collision_detection import CollisionEvent

from ...audio import MetalPings
from .._groups import Players, Bullets, GravityAffected
from .._weapons import BaseWeapon
from .._base_entities import LogicGameEntity
from .._sensors import BaseSensor, DetectionGroup
from .._collision.collision_groups import collision_group_turrets, collision_group_bullets

if tp.TYPE_CHECKING:
    from .._bullets import Bullet


@dataclass
class TargetSolution:
    target: VisibleGameEntityLike
    target_predict: Vec2
    angle: Vec2
    tof: float


type target_solution_t = TargetSolution | None


class BaseTurret(LogicGameEntity):
    """
    base turret type
    """

    size: Vec2
    weapon: BaseWeapon
    _max_hp: int = 80
    _hp: int = 0
    _aim_type: tp.Literal["low", "high"] = "low"
    _target: LogicGameEntity | tp.Type[...] = ...
    _target_predict: list[Vec2] = ...
    available_targets: dict = ...
    _high_tof_multiplier: float = 1.1
    _number_target_taps: int

    _default_turn_speed: float = np.inf  # max rad/s
    _default_valid_angles: tuple[Vec2, Vec2] | EllipsisType = ...
    _default_facing_angle: float = np.pi
    _default_max_error: float | EllipsisType = ...
    _default_allow_static_target: bool = False

    _DEFAULT_COLLISION_GROUP = collision_group_turrets

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            size: Vec2,
            position: Vec2,
            weapon: BaseWeapon,
            engagement_range: float,
            *,
            min_range: float = 0,
            airburst_munition: bool = False,
            intercept_bullets: bool = False,
            intercept_players: bool = True,
            target_taps: int = -1,
            sensors: tp.Iterable[BaseSensor] = None,
            detection_group: DetectionGroup = None,
            valid_angles: tuple[Vec2, Vec2] | EllipsisType = ...,
            turn_speed: float | EllipsisType = ...,
            allow_static_target: bool | EllipsisType = ...
    ) -> None:
        self._set_pos = position.copy()
        position.y -= size.y / 2

        # audio
        self._ping = MetalPings().set_volume(.4, .5)

        # params
        self.weapon = weapon
        self.weapon.set_parent(self)
        self.weapon.show()
        self.engagement_range = engagement_range
        self.min_range = min_range
        self.airburst_munition = airburst_munition
        self.intercept_bullets = intercept_bullets
        self.intercept_players = intercept_players
        self._allow_static_target = get_default(
            allow_static_target, self._default_allow_static_target
        )
        self._max_error = self._default_max_error
        self.available_targets = {}
        self._target_predict = []
        self._last_shot = perf_counter()
        self._valid_angles = get_default(valid_angles, self._default_valid_angles)
        if self._valid_angles is not ...:
            self._valid_angles[0].length = self.engagement_range
            self._valid_angles[1].length = self.engagement_range

        if target_taps > 0:
            self._target_tapping = True
            self._number_target_taps = target_taps

        else:
            self._target_tapping = False
            self._number_target_taps = 1

        self._turn_speed = get_default(turn_speed, self._default_turn_speed)

        self._hp = self._max_hp

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            coalition=coalition,
            centered=True
        )
        self._create_collision()
        self.facing.angle = self._default_facing_angle
        self.weapon.facing.angle = self.facing.angle

        # self.add(CollisionDestroyed)

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

        # spawn logic dummy
        self._runtime_buffer[self.id].param3 = MASK64
        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={"id": self.id, "cid": self.cid(), "weapon_id": self.weapon.id}
        ))

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def hp(self) -> int:
        return self._hp

    def hit(self, damage: float, hit_by: tp.Self = ...) -> None:
        """
        deal damage to the turret
        """
        self._hp -= damage

        # ping on bullet hit
        if hit_by is not ...:
            if hit_by.is_bullet:
                self._ping.play(pos=self.position)

        # check for turret death
        if self._hp <= 0:
            self.kill(hit_by)

    def kill(self, killed_by=...):
        self.weapon.stop()
        self.weapon.kill(killed_by)
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
            if not t["solution"]:
                continue

            if include_all:
                return t["solution"]

            if t["distance"] > self.engagement_range:
                continue

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
                    if not any(
                            [
                                self._valid_angles[0].angle
                                < t["solution"].angle.angle
                                < start2,
                                self._valid_angles[1].angle
                                > t["solution"].angle.angle
                                > end2,
                            ]
                    ):
                        continue

                return t["solution"]

        # all targets have been shot at, so shoot at nothing
        # and reset shot_ats
        if not self._target_tapping:
            for target in self.available_targets:
                self.available_targets[target]["shot_at"] = -1

        # deleted because targets will now be shot at if last shot missed

        return None

    def _update(self, delta):
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
                    "distance": np.inf,
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
                    sol = self._get_firing_solution(
                        target,
                        ignore_acceleration=True,
                        ignore_velocity=True,
                    )
                    self.available_targets[target]["solution"] = sol

                    # if aim type is high, allow no-movement targets
                    if self._allow_static_target:
                        self.available_targets[target]["distance"] = np.inf
                        continue

                    elif not sol:
                        self.available_targets[target]["distance"] = np.inf
                        continue

                self.available_targets[target]["distance"] = (
                        sol.target_predict
                        - self.position + self.weapon.parent_position_offset
                ).length

        new_target = self.get_next_target()
        simulate_target = self.get_next_target(True)
        if new_target is not None:
            self._target = new_target
            self._last_shot = perf_counter()
            solution = self._get_firing_solution(new_target.target, recalc=25)

            if solution is None:
                # allos mortar to treat target as static position
                if self._allow_static_target:
                    solution = self._get_firing_solution(
                        new_target.target,
                        recalc=25,
                        ignore_velocity=True,
                        ignore_acceleration=True,
                    )

                    if solution:
                        self._turn_at(solution, delta)
                        self._shoot_at(solution, max_error=self._max_error)

                    else:
                        new_target = None

                else:
                    new_target = None

            else:
                self._turn_at(solution, delta)
                self._shoot_at(solution, max_error=self._max_error)

        # aim but don't shoot
        if new_target is None and simulate_target is not None:
            self._turn_at(simulate_target, delta)

        else:
            self._target = None
            # self._target_predict = []

        if perf_counter() - self._last_shot >= .1:
            self.weapon.stop_shooting()

        # check if reload
        if self.weapon.get_mag_state(1)[0] == 0:
            self.weapon.reload()

        super()._update(delta)

        # update parameters
        ## bars
        self._runtime_buffer[self.id].param0 = self._hp / self._max_hp

        ## target
        if self._target_predict:
            target = self._target_predict[0]
            x32 = ctypes.c_int32(int(target.x)).value
            y32 = ctypes.c_int32(int(target.y)).value
            self._runtime_buffer[self.id].param3 = ctypes.c_uint64(
                x32 & MASK32
            ).value | (ctypes.c_uint64(y32 & MASK32).value << 32)

        ## range
        param4 = int(self.min_range) & MASK16
        param4 |= (int(self.engagement_range) & MASK16) << 16

        if self._valid_angles is not ...:
            param4 |= (int(normalize_angle(self._valid_angles[0].angle) * 10_000) & MASK16) << 32
            param4 |= (int(normalize_angle(self._valid_angles[1].angle) * 10_000) & MASK16) << 48

        else:
            param4 |= MASK32 << 32

        self._runtime_buffer[self.id].param4 = param4

    def _get_firing_solution(
            self,
            target: VisibleGameEntityLike,
            *,
            recalc: int = 5,
            ignore_velocity: bool = False,
            ignore_acceleration: bool = False,
    ) -> TargetSolution | None:
        """
        aim at specified target
        :param target: target to aim at
        :returns:
        """
        player_velocity = target.velocity.copy()
        player_acceleration = target.acceleration.copy()

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

        # try to predict where the player is going to be
        with suppress(ValueError):
            aiming_angle, tof, predict = calculate_launch_angle(
                position_delta,
                player_velocity * (1 - ignore_velocity),
                player_acceleration * (1 - ignore_acceleration),
                self.weapon.muzzle_velocity,
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

            # check if inside range
            if predict.length > self.engagement_range:
                return None

            target_predict = self.position + self.weapon.parent_position_offset + predict

            if predict.length < self.min_range:
                return

            # tof = min(
            #     tof,
            #     1.3 * self.engagement_range / self.weapon.muzzle_velocity
            # )

            return TargetSolution(
                target_predict=target_predict,
                angle=aiming_angle,
                target=target,
                tof=tof,
            )

        return None

    def _shoot_weapon(self, solution: TargetSolution) -> bool:
        return self.weapon.shoot(
            self.facing,
            solution.tof if self.airburst_munition else ...,
            target_pos=solution.target_predict
        )

    def _shoot_at(
            self,
            solution: TargetSolution,
            *,
            max_error: float | EllipsisType = ...
    ) -> None:
        """
        shoot at specified target
        :param solution: where to shoot to
        :param max_error: max facing offset to target solution
        """
        if isinstance(max_error, EllipsisType):
            max_error = self.weapon._inaccuracy

        if normalize_angle(self.facing.angle - solution.angle.angle) > max_error:
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
                self._valid_angles[0].angle < solution.angle.angle < start2,
                self._valid_angles[1].angle > solution.angle.angle > end2,
            ]):
                return

        shot = self._shoot_weapon(solution)

        if shot:
            self._target_predict = [solution.target_predict]
            if self.available_targets[solution.target]["shot_at"] < -1:
                self.available_targets[solution.target]["shot_at"] += 1

            else:
                self.available_targets[solution.target]["shot_at"] = solution.tof

    def _turn_at(self, solution: TargetSolution, delta: float) -> None:
        """turn towards a target"""
        diff = solution.angle.angle - self.facing.angle

        if diff > np.pi:
            diff -= 2 * np.pi

        if diff < -np.pi:
            diff += 2 * np.pi

        # limit turn speed
        increment = np.sign(diff) * min(abs(diff), self._turn_speed * delta)
        new_angle = normalize_angle(self.facing.angle + increment)

        # check for gimbal limit
        if not isinstance(self._valid_angles, EllipsisType):

            min_a = normalize_angle(self._valid_angles[0].angle)
            max_a = normalize_angle(self._valid_angles[1].angle)

            # end angle < start angle (0 crossing)
            if max_a <= min_a:
                if max_a < new_angle < min_a:
                    d = min_a - max_a

                    # clamp to corresponding angle
                    if new_angle + d / 2 > min_a:
                        new_angle = min_a

                    else:
                        new_angle = max_a

            else:
                new_angle = min(max(new_angle, min_a), max_a)

        # apply rotation
        self.facing.angle = new_angle
        self.weapon.facing.angle = self.facing.angle

    def __on_collision_bullet(self, event: CollisionEvent["Bullet"]) -> None:
        dmg = event.other_entity.damage
        if dmg > 0 and event.other_entity.parent != self:
            self.hit(dmg, hit_by=event.other_entity)

    def _collision_start(self, events: list[CollisionEvent["Bullet"]]) -> None:
        for event in events:
            if event.group_id == collision_group_bullets:
                self.__on_collision_bullet(event)
