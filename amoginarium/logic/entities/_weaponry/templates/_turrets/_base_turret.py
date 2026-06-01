"""
Base class for automated turrets with target tracking and engagement.

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_turrets/_base_turret.py
| ``Project``: amoginarium
| ``Created``: 19.03.2024
| ``Authors``: Nilusink, LukasKrah
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

from amoginarium.shared import TurretCIDs
from amoginarium.shared.audio import MetalPings
from amoginarium.shared.utility import calculate_launch_angle, get_default
from amoginarium.shared.utility import InertialValue, ManeuveringTrackClass, MASK16
from amoginarium.shared.utility import MASK32, MASK64, MotionTrackType, normalize_angle
from amoginarium.shared.utility import PIDController, TrackQuality, TrackState
from amoginarium.shared.utility import UnknownTrackClass, Vec2

from ...._base import GameCollisions, GravityAffected, LogicGameEntity
from .._sensors import DetectionGroup

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t, Coalitions, MurderViable
    from amoginarium.shared.collision_detection import CollisionExceptionIDType
    from amoginarium.shared.utility import BaseTrack

    from .._sensors import BaseSensor
    from .._weapons import BaseWeapon


@dataclass
class TargetSolution:
    """a solution for pollution."""

    target_predict: Vec2
    angle: Vec2
    tof: float
    track: BaseTrack


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

    _ADVANCED_DEBUGGING = True
    _AD_VARS: tp.ClassVar[list[tuple[str, type | tuple[type, int]]]] = [
        ("_hp", float),
        ("weapon._current_reload_time", float),
        ("_target_angle", float),
        ("facing.angle", float),
        ("intercept_bullets", bool),
        ("intercept_players", bool),
        ("control_value", float),
        ("_turret_angle.value", float),
        ("target_turret_angle", float),
    ]
    _AD_CONSOLE_LINES = 1

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
    _default_facing_angle: float = np.pi
    _default_max_error: float | EllipsisType = ...
    _default_allow_static_target: bool = False
    _default_airburst_munition: bool = False

    _default_turret_control_turn_speed: tp.ClassVar[float] = np.inf
    _default_turret_control_turn_acceleration: tp.ClassVar[float] = np.inf
    _default_turret_control_friction: tp.ClassVar[float] = 4
    _default_turret_control_p: tp.ClassVar[float] = 8
    _default_turret_control_i: tp.ClassVar[float] = 0
    _default_turret_control_d: tp.ClassVar[float] = 1.6

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

    _bullets_do_not_initially_hit_turret: CollisionExceptionIDType

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

        self._bullets_do_not_initially_hit_turret = GameCollisions.add_exception()

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
                raise RuntimeError(msg)  # noqa: TRY004

            if cluster:
                weapon_kwargs["cluster"] = True

            self.weapon = self._default_weapon_type(
                parent=self,
                runtime_buffer=runtime_buffer,
                drop_casings=self._default_weapon_drop_casings,
                parent_position_offset=offset,
                **weapon_kwargs,
            )
            self.weapon.reload(instant=True)

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
        self._target_angle = 0
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

        self._turn_speed: float = get_default(
            self._default_turret_control_turn_speed,
            np.inf,
        )
        self._turn_acceleration: float = get_default(
            self._default_turret_control_turn_acceleration,
            np.inf,
        )

        self._hp = self._default_max_hp

        self._collision_exception_ids.append(self._bullets_do_not_initially_hit_turret)

        self._create_collision()
        self.facing.angle = self._default_facing_angle
        self.weapon.facing.angle = self.facing.angle

        # turret stuff
        self.control_value = 0
        self.target_turret_angle = 0
        self._turret_angle = InertialValue(
            self.facing.angle,
            initial_velocity=0,
            inertia=1,
            max_velocity=self._turn_speed,
            max_acceleration=self._turn_acceleration,
            friction=self._default_turret_control_friction,
        )
        self._turret_angle_pid = PIDController(
            p=self._default_turret_control_p,
            i=self._default_turret_control_i,
            d=self._default_turret_control_d,
        )
        self._turret_angle_pid.set_value(self._turret_angle.value)

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
        self._spawn_graphics_entity(weapon_id=self.weapon.id)

    @property
    def max_hp(self) -> int:
        return self._default_max_hp

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def weapon_pos(self) -> Vec2:
        """Position of Weapon."""
        return self.position + self.weapon.parent_position_offset

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
            self.kill(killed_by=hit_by)

    @tp.override
    def _kill(
        self,
        *,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> None:
        self.weapon.stop()
        self.weapon.kill(killed_by=killed_by)
        super()._kill(killed_by=killed_by, kill_children=kill_children)

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

            # require position, velocity AND acceleration and confirmed track
            # before firing
            if (
                target.quality != TrackQuality.POS_VEL_ACC
                and target.state == TrackState.CONFIRMED
            ) or t["distance"] > self.max_range:
                continue

            if t["shot_at"] < -0.5:
                # check if firing solution inside engagement envelope
                if not isinstance(self._valid_angles, EllipsisType):
                    angle_delta = normalize_angle(
                        self._valid_angles[1].angle - self._valid_angles[0].angle
                    )
                    start2 = self._valid_angles[0].angle + angle_delta
                    end2 = self._valid_angles[1].angle - angle_delta

                    # check if firing-solution is inside engagement envelope
                    if not (
                        self._valid_angles[0].angle < t["solution"].angle.angle < start2
                        or self._valid_angles[1].angle
                        > t["solution"].angle.angle
                        > end2,
                    ):
                        continue

                return t["solution"]

        # all targets have been shot at, so shoot at nothing
        # and reset shot_ats
        if not self._target_tapping:
            for target in self.available_targets:
                self.available_targets[target]["shot_at"] = -1

        return None

    @tp.override
    def _update(self, delta: float) -> None:  # noqa: C901, PLR0912, PLR0915
        # update weapon
        self.weapon.update(delta)

        # scan for targets and engage the closest one
        targets = self.detection_group.tracks

        for track in targets:
            if isinstance(track, EllipsisType) or track in self.available_targets:
                continue

            self.available_targets[track] = {
                "shot_at": -self._number_target_taps,
                "distance": np.inf,
                "solution": None,
            }

        # make list only contain the entities
        for track in self.available_targets.copy():
            track: BaseTrack

            if track not in targets:
                self.available_targets.pop(track)
                continue

            is_bullet = (
                track.track_classification.motion
                == MotionTrackType.MOTION_BALLISTIC.value
                or track.track_classification.motion
                == MotionTrackType.MOTION_ORBITAL.value
                or (
                    track.track_classification.motion
                    == MotionTrackType.MOTION_MANEUVERING.value
                    and track.track_classification.type
                    != ManeuveringTrackClass.DRONE.value
                    # ignore cuz player
                )
                or (
                    track.track_classification.motion
                    == MotionTrackType.MOTION_UNKNOWN.value
                    and (
                        track.track_classification.type
                        == UnknownTrackClass.SMALL_FAST.value
                        or track.track_classification.type
                        == UnknownTrackClass.BIG_FAST.value
                    )
                )
            )

            if (not self.intercept_bullets and is_bullet) or (
                not self.intercept_players and not is_bullet
            ):
                self.available_targets[track]["solution"] = None
                continue

            self._target_predict = [track.get_position()]

            if self.available_targets[track]["shot_at"] >= 0:
                sol = self._get_firing_solution(track)
                self.available_targets[track]["solution"] = sol
                self.available_targets[track]["shot_at"] -= delta

            elif self.available_targets[track]["shot_at"] > -1:
                self.available_targets[track]["shot_at"] = -self._number_target_taps

            else:
                sol = self._get_firing_solution(track)
                self.available_targets[track]["solution"] = sol

                if not sol:
                    self.available_targets[track]["distance"] = np.inf

                else:
                    self.available_targets[track]["distance"] = (
                        sol.target_predict
                        - self.position
                        + self.weapon.parent_position_offset
                    ).length

            sol = self.available_targets[track]["solution"]
            if sol:
                self._target_predict = [sol.target_predict]
            else:
                self._target_predict[0] = Vec2()

        if not self.available_targets:
            self._target_predict = [self.position.copy()]

        self._debug_print(f"{len(self.available_targets)} targets")

        new_target = self.get_next_target()
        simulate_target = self.get_next_target(include_all=True)
        if new_target is not None:
            self._target = new_target
            self._last_shot = perf_counter()
            solution = self._get_firing_solution(new_target.track, recalc=25)

            if solution is None:
                # allos mortar to treat target as static position
                if self._allow_static_target:
                    solution = self._get_firing_solution(
                        new_target.track,
                        recalc=25,
                        ignore_velocity=True,
                        ignore_acceleration=True,
                    )

                    if solution:
                        self._turn_at(solution.angle.angle, delta)
                        self._shoot_at(solution, max_error=self._max_error)

                    else:
                        new_target = None

                else:
                    new_target = None

            else:
                self._turn_at(solution.angle.angle, delta)
                self._shoot_at(solution, max_error=self._max_error)

        # aim but don't shoot
        if new_target is None and simulate_target is not None:
            self._turn_at(simulate_target.angle.angle, delta)

        else:
            self._target = None
            if self._target_angle != 0:
                self._turn_at(self._target_angle, delta)

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
        track: BaseTrack,
        *,
        recalc: int = 5,
        ignore_velocity: bool = False,  # noqa: ARG002
        ignore_acceleration: bool = False,  # noqa: ARG002
    ) -> TargetSolution | None:
        """
        Aim at specified target.

        :param track: track to aim at
        :returns:
        """
        position_delta = track.get_position() - self.weapon_pos
        vel = get_default(track.get_velocity(), Vec2())
        acc = get_default(track.get_acceleration(), Vec2())

        # mirror y-axis (because in pygame, + is down)
        position_delta.y *= -1
        vel.y *= -1
        acc.y *= -1

        # mirror x if < 0 because calculate_launch_angle is weird and it works this ways
        mirror = False
        if position_delta.x < 0:
            position_delta.x *= -1
            vel.x *= -1
            acc.x *= -1
            mirror = True

        with suppress(ValueError):
            aiming_angle, tof, predict = calculate_launch_angle(
                position_delta,
                vel,
                acc,
                self.weapon.muzzle_velocity,
                recalc,
                self._default_engagement_aim_type,
                g=GravityAffected.gravity * 2,
            )

            # check if inside range
            if predict.length > self.max_range or predict.length < self.min_range:
                return None

            # mirror back y-axis
            aiming_angle.y *= -1
            predict.y *= -1

            if mirror:
                aiming_angle.x *= -1
                predict.x *= -1

            target_predict = self.weapon_pos + predict

            return TargetSolution(
                target_predict=target_predict, angle=aiming_angle, tof=tof, track=track
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
        Shoot at specified target.

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
            if self.available_targets[solution.track]["shot_at"] < -1:
                self.available_targets[solution.track]["shot_at"] += 1

            else:
                self.available_targets[solution.track]["shot_at"] = solution.tof

    def _turn_at(self, angle: float, delta: float) -> None:
        """Turn towards a target."""
        self.target_turret_angle = angle
        diff = angle - self.facing.angle
        self._target_angle = angle

        if diff > np.pi:
            diff -= 2 * np.pi

        if diff < -np.pi:
            diff += 2 * np.pi

        # get PID controll value
        self._turret_angle_pid.set_value(self.facing.angle)
        self.control_value = self._turret_angle_pid.update(diff, delta)

        # apply pid control value to turret
        new_angle = self._turret_angle.update(
            self.control_value * self._turn_speed / 2,
            delta,
        )

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

    def get_initial_root_collision_exception(self) -> CollisionExceptionIDType:
        return self._bullets_do_not_initially_hit_turret
