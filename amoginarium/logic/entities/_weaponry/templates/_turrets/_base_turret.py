"""
Base class for automated turrets with target tracking and engagement.

Path: amoginarium/logic/entities/_weaponry/templates/_turrets/_base_turret.py
Project: amoginarium
Created: 19.03.2024
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import ctypes
import typing as tp
from contextlib import suppress
from dataclasses import dataclass
from time import perf_counter
from types import EllipsisType, NoneType

import numpy as np
from icecream import ic

from amoginarium import pv
from amoginarium.shared import BaseCommandType, ProcessCommand, TurretCIDs
from amoginarium.shared.audio import MetalPings
from amoginarium.shared.utility import calculate_launch_angle, get_default, MASK16
from amoginarium.shared.utility import MASK32, MASK64, normalize_angle, Vec2

from ...._base import Bullets, GameCollisions, GravityAffected, LogicGameEntity
from .._sensors import DetectionGroup

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, Coalitions, VisibleGameEntityLike
    from amoginarium.shared.collision_detection import CollisionEvent

    from .._bullets import Bullet
    from .._sensors import BaseSensor
    from .._weapons import BaseWeapon


@dataclass
class TargetSolution:
    """a solution for pollution."""

    target_predict: Vec2
    angle: Vec2
    tof: float
    target: VisibleGameEntityLike | EllipsisType | None = ...


class SensorInit(tp.TypedDict):
    """values needed for sensor to init."""

    type: type[BaseSensor]
    detection_range: float | None
    sphere_accuracy: float | None
    min_rcs: float | None


def check_target(target: LogicGameEntity, self: LogicGameEntity) -> bool:
    """Check if a target should be fired on."""
    if target.parent == self:
        return False

    return not (
        not isinstance(target.coalition, (EllipsisType, NoneType))
        and target.coalition == self.coalition
    )


type target_solution_t = TargetSolution | None  # noqa: PYI042


class BaseTurret(LogicGameEntity):
    """
    base turret type.
    """

    _CID = TurretCIDs.base
    size: Vec2
    weapon: BaseWeapon
    _default_max_hp: int = 80
    _hp: int = 0
    _target: LogicGameEntity | type[...] = ...
    _target_predict: list[Vec2] = ...
    available_targets: dict = ...
    _high_tof_multiplier: float = 1.1
    _number_target_taps: int

    _default_size: Vec2 | float | tuple[float, float] | list[float] = (23, 24)
    _default_turn_speed: float = np.inf  # max rad/s
    _default_facing_angle: float = np.pi
    _default_max_error: float | EllipsisType = ...
    _default_allow_static_target: bool = False
    _default_airburst_munition: bool = False

    _default_engagement_valid_angles: tuple[float, float] | EllipsisType = ...
    _default_engagement_aim_type: tp.Literal["low", "high"] = "low"
    _default_engagement_min_range: float = 0
    _default_engagement_max_range: float = 100

    _default_target_bullets: bool = False
    _default_target_players: bool = True
    _default_target_taps: int = -1

    _default_weapon_type: type[BaseWeapon] | EllipsisType = ...
    _default_weapon_drop_casings: bool = False
    _default_weapon_position_offset: Vec2 | list[float] | tuple[float, float] = (0, 0)

    _sensors_list: tp.ClassVar[list[SensorInit]] = []

    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_turrets

    def __init__(  # noqa: C901, PLR0912, PLR0915
        self,
        runtime_buffer: Array[base_entity_t],
        coalition: Coalitions,
        position: Vec2,
        *,
        size: Vec2 | float | tuple[float, float] | list[float] | EllipsisType = ...,
        weapon: BaseWeapon | EllipsisType = ...,
        max_range: float | EllipsisType = ...,
        min_range: float | EllipsisType = ...,
        airburst_munition: bool | EllipsisType = ...,
        intercept_bullets: bool | EllipsisType = ...,
        intercept_players: bool | EllipsisType = ...,
        target_taps: int | EllipsisType = ...,
        sensors: tp.Iterable[BaseSensor] | None = None,
        detection_group: DetectionGroup = None,
        valid_angles: tuple[Vec2, Vec2] | EllipsisType = ...,
        turn_speed: float | EllipsisType = ...,
        allow_static_target: bool | EllipsisType = ...,
        cluster: bool = False,
        weapon_kwargs: dict[str, tp.Any] | EllipsisType = ...,
    ) -> None:
        size = get_default(size, self._default_size)
        weapon_kwargs: dict = get_default(weapon_kwargs, {})

        if isinstance(size, (float, int)):
            size: Vec2 = Vec2().from_cartesian(size, size)

        elif not isinstance(size, Vec2):
            size: list[float] | tuple[float, float]
            size: Vec2 = Vec2().from_cartesian(size[0], size[1])

        size: Vec2
        position.y -= size.y / 2

        self._set_pos = position.copy()

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            coalition=coalition,
            centered=True,
        )

        # audio
        self._ping = MetalPings().set_volume(0.4, 0.5)

        # params
        if not isinstance(weapon, EllipsisType):
            self.weapon = weapon

        else:
            if isinstance(self._default_weapon_position_offset, Vec2):
                offset = self._default_weapon_position_offset

            else:
                offset = Vec2().from_cartesian(
                    self._default_weapon_position_offset[0],
                    self._default_weapon_position_offset[1],
                )

            if isinstance(self._default_weapon_type, EllipsisType):
                msg = f"No weapon set for {self.__class__.__name__}"
                raise RuntimeError(msg)

            if cluster:
                weapon_kwargs["cluster"] = True

            self.weapon = self._default_weapon_type(
                parent=self,
                runtime_buffer=runtime_buffer,
                drop_casings=self._default_weapon_drop_casings,
                parent_position_offset=offset,
                **weapon_kwargs,
            )
            self.weapon.reload(True)

        self.weapon.set_parent(self)
        self.weapon.show()
        self.max_range = get_default(max_range, self._default_engagement_max_range)
        self.min_range = get_default(min_range, self._default_engagement_min_range)
        self._aim_type = self._default_engagement_aim_type

        self.airburst_munition = (
            get_default(airburst_munition, self._default_airburst_munition) or cluster
        )
        self.intercept_bullets = get_default(
            intercept_bullets, self._default_target_bullets
        )
        self.intercept_players = get_default(
            intercept_players, self._default_target_players
        )
        self._allow_static_target = get_default(
            allow_static_target, self._default_allow_static_target
        )
        self._max_error = self._default_max_error
        self.available_targets = {}
        self._target_predict = []
        self._last_shot = perf_counter()
        self._valid_angles = get_default(
            valid_angles, self._default_engagement_valid_angles
        )
        if not isinstance(self._valid_angles, EllipsisType):
            self._valid_angles = [
                Vec2().from_polar(a, 1) if isinstance(a, (float, int)) else a
                for a in self._valid_angles
            ]

        if self._valid_angles is not ...:
            self._valid_angles[0].length = self.max_range
            self._valid_angles[1].length = self.max_range

        target_taps = get_default(target_taps, self._default_target_taps)
        if target_taps > 0:
            self._target_tapping = True
            self._number_target_taps = target_taps

        else:
            self._target_tapping = False
            self._number_target_taps = 1

        self._turn_speed = get_default(turn_speed, self._default_turn_speed)

        self._hp = self._default_max_hp

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
        if sensors is None and self._sensors_list:
            sensors: list[BaseSensor] = []
            for sensor in self._sensors_list:
                sensor_args = sensor.copy()
                sensor_type: type[BaseSensor] = sensor_args.pop("type")
                sensors.append(
                    sensor_type(
                        runtime_buffer=runtime_buffer, parent=self, **sensor_args
                    )
                )

        if sensors is not None:
            for sensor in sensors:
                self._children.append(sensor)
                self.detection_group.add_sensor(sensor)

        # spawn logic dummy
        self._runtime_buffer[self.id].param3 = MASK64
        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs={"id": self.id, "cid": self.cid(), "weapon_id": self.weapon.id},
            )
        )

    @property
    def max_hp(self) -> int:
        return self._default_max_hp

    @property
    def hp(self) -> int:
        return self._hp

    def hit(self, damage: float, hit_by: tp.Self = ...) -> None:
        """
        Deal damage to the turret.
        """
        self._hp -= damage

        # ping on bullet hit
        if hit_by is not ... and "bullet" in hit_by._tags:
            self._ping.play(pos=self.position)

        # check for turret death
        if self._hp <= 0:
            self.kill(hit_by)

    def _kill(self, killed_by: tp.Any = ...) -> None:
        self.weapon.stop()
        self.weapon.kill(killed_by)
        super()._kill(killed_by)

    def get_next_target(self, *, include_all: bool = False) -> target_solution_t:
        """
        Return next best target to shoot at.
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

            if t["distance"] > self.max_range:
                continue

            if t["shot_at"] < -0.5:
                # check if firing solution inside engagement envelope
                if self._valid_angles is not ...:
                    angle_delta = normalize_angle(
                        self._valid_angles[1].angle - self._valid_angles[0].angle
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

    def _update(self, delta: float) -> None:
        # update weapon
        self.weapon.update(delta)

        # scan for targets and engage the closest one
        targets = self.detection_group.targets

        # only check targets that are supposed to be engaged
        bullets = Bullets.entities()
        targets = [
            t
            for t in targets
            if ((is_bullet := t in bullets) and self.intercept_bullets)
            or (not is_bullet and self.intercept_players)
        ]

        # filter stuff shot by myself
        targets = [e for e in targets if check_target(e, self)]

        for target in targets:
            if target not in self.available_targets:
                self.available_targets[target] = {
                    "shot_at": -self._number_target_taps,
                    "distance": np.inf,
                    "solution": None,
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
                    if self._allow_static_target or not sol:
                        self.available_targets[target]["distance"] = np.inf
                        continue

                self.available_targets[target]["distance"] = (
                    sol.target_predict
                    - self.position
                    + self.weapon.parent_position_offset
                ).length

        new_target = self.get_next_target()
        simulate_target = self.get_next_target(include_all=True)
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

        if perf_counter() - self._last_shot >= 0.1:
            self.weapon.stop_shooting()

        # check if reload
        if self.weapon.get_mag_state(1)[0] == 0:
            self.weapon.reload()

        super()._update(delta)

        # update parameters
        # bars
        self._runtime_buffer[self.id].param0 = self._hp / self._default_max_hp

        # target
        if self._target_predict:
            target = self._target_predict[0]
            x32 = ctypes.c_int32(int(target.x)).value
            y32 = ctypes.c_int32(int(target.y)).value
            self._runtime_buffer[self.id].param3 = ctypes.c_uint64(
                x32 & MASK32
            ).value | (ctypes.c_uint64(y32 & MASK32).value << 32)

        # range
        param4 = int(self.min_range) & MASK16
        param4 |= (int(self.max_range) & MASK16) << 16

        if self._valid_angles is not ...:
            param4 |= (
                int(normalize_angle(self._valid_angles[0].angle) * 10_000) & MASK16
            ) << 32
            param4 |= (
                int(normalize_angle(self._valid_angles[1].angle) * 10_000) & MASK16
            ) << 48

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
        Aim at specified target.

        :param target: target to aim at
        :returns:
        """
        player_velocity = target.velocity.copy()
        player_acceleration = target.acceleration.copy()

        # if target is on ground, subtract gravitational acceleration
        if hasattr(target, "on_ground") and target.on_ground:
            player_acceleration.y -= GravityAffected.gravity

        target_position = target.position

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
                self._default_engagement_aim_type,
                # *2 because for some reason I gave bullets 2x gravity
                g=GravityAffected.gravity * 2,
            )

            aiming_angle.y *= -1
            predict.y *= -1

            if mirror:
                aiming_angle.x *= -1
                predict.x *= -1

            # check if inside range
            if predict.length > self.max_range:
                return None

            target_predict = (
                self.position + self.weapon.parent_position_offset + predict
            )

            if predict.length < self.min_range:
                return None

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
            target_pos=solution.target_predict,
        )

    def _shoot_at(
        self, solution: TargetSolution, *, max_error: float | EllipsisType = ...
    ) -> None:
        """
        Shoot at specified target
        :param solution: where to shoot to
        :param max_error: max facing offset to target solution.
        """
        if isinstance(max_error, EllipsisType):
            max_error = self.weapon.inaccuracy

        if normalize_angle(self.facing.angle - solution.angle.angle) > max_error:
            return

        if self._valid_angles is not ...:
            angle_delta = normalize_angle(
                self._valid_angles[1].angle - self._valid_angles[0].angle
            )
            start2 = self._valid_angles[0].angle + angle_delta
            end2 = self._valid_angles[1].angle - angle_delta

            # check if firing-solution is inside engagement envelope
            if not any(
                [
                    self._valid_angles[0].angle < solution.angle.angle < start2,
                    self._valid_angles[1].angle > solution.angle.angle > end2,
                ]
            ):
                return

        shot = self._shoot_weapon(solution)

        if shot:
            self._target_predict = [solution.target_predict]
            if self.available_targets[solution.target]["shot_at"] < -1:
                self.available_targets[solution.target]["shot_at"] += 1

            else:
                self.available_targets[solution.target]["shot_at"] = solution.tof

    def _turn_at(self, solution: TargetSolution, delta: float) -> None:
        """Turn towards a target."""
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
                    new_angle = min_a if new_angle + d / 2 > min_a else max_a

            else:
                new_angle = min(max(new_angle, min_a), max_a)

        # apply rotation
        self.facing.angle = new_angle
        self.weapon.facing.angle = self.facing.angle

    def __on_collision_bullet(self, event: CollisionEvent[Bullet]) -> None:
        dmg = event.other_entity.damage
        if dmg > 0 and event.other_entity.parent != self:
            self.hit(dmg, hit_by=event.other_entity)

    def _collision_start(self, events: list[CollisionEvent[Bullet]]) -> None:

        # bullet - 5 turrets - events länge 5
        # turret - events 1 bullet
        for event in events:
            if event.group_id == GameCollisions.collision_group_bullets:
                self.__on_collision_bullet(event)
