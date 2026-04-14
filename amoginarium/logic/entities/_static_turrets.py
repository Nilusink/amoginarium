"""
_static_turrets.py
01.04.2026

base turret types

Author:
Nilusink
"""

from dataclasses import dataclass
from contextlib import suppress
from types import EllipsisType
from time import perf_counter
from ctypes import Array
from icecream import ic
import typing as tp
import numpy as np
import ctypes

from amoginarium.shared import Coalitions, VisibleGameEntityLike, base_entity_t
from amoginarium.shared import ProcessCommand, BaseCommandType, DummyCIDs
from amoginarium.shared import TurretCIDs
from amoginarium.shared.utility import is_related, normalize_angle, MASK32
from amoginarium.shared.utility import Vec2, calculate_launch_angle, MASK16
from amoginarium.shared.utility import MASK64, get_default
from amoginarium import pv

from ..audio import MetalPings
from ._logic_groups import CollisionDestroyed, Players, Updated, Bullets
from ._logic_groups import GravityAffected
from ._weapons import BaseWeapon, Minigun, Sniper, Ak47, Mortar, Flak, CRAM, SkyShieldWeapon
from ._base_entity import LogicGameEntity
from ._sensors import MagicSensor, BaseSensor
from ._detection_group import DetectionGroup
from ._radar import RadarSensor


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
            coalition=coalition
        )
        self.facing.angle = self._default_facing_angle
        self.weapon.facing.angle = self.facing.angle

        self.add(CollisionDestroyed)

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
            kwargs={"id": self.id, "cid": self.cid()}
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
                        self.__turn_at(solution, delta)
                        self.__shoot_at(solution, max_error=self._max_error)

                    else:
                        new_target = None

                else:
                    new_target = None

            else:
                self.__turn_at(solution, delta)
                self.__shoot_at(solution, max_error=self._max_error)

        # aim but don't shoot
        if new_target is None and simulate_target is not None:
            self.__turn_at(simulate_target, delta)

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
                player_velocity * (1-ignore_velocity),
                player_acceleration * (1-ignore_acceleration),
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

    def __shoot_at(
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

        shot = self.weapon.shoot(
            self.facing,
            solution.tof if self.airburst_munition else ...,
            target_pos=solution.target_predict
        )

        if shot:
            self._target_predict = [solution.target_predict]
            if self.available_targets[solution.target]["shot_at"] < -1:
                self.available_targets[solution.target]["shot_at"] += 1

            else:
                self.available_targets[solution.target]["shot_at"] = solution.tof

    def __turn_at(self, solution: TargetSolution, delta: float) -> None:
        """turn towards a target"""
        diff = solution.angle.angle - self.facing.angle

        if diff > np.pi:
            diff -= 2 * np.pi

        if diff < -np.pi:
            diff += 2 * np.pi

        # limit turn speed
        increment = np.sign(diff) * min(abs(diff), self._turn_speed * delta)

        # apply rotation
        self.facing.angle += increment
        self.weapon.facing.angle = self.facing.angle


class MinigunTurret(BaseTurret):
    _cid = TurretCIDs.minigun
    _max_hp: int = 60

    _default_turn_speed = 2

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Minigun(
            self,
            runtime_buffer,
            False,
            parent_position_offset=(0, -13)
        )
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(48, 48),
            position,
            weapon,
            2000,
            sensors=[
                MagicSensor(self, 1500)
            ],
            **kwargs
        )


class SniperTurret(BaseTurret):
    _cid = TurretCIDs.sniper
    _max_hp: int = 40

    _default_turn_speed = 2

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Sniper(self, runtime_buffer, True, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(31, 32),
            position,
            weapon,
            2400,
            sensors=[
                RadarSensor(self, 2500, sphere_accuracy=256)
            ],
            **kwargs
        )


class AkTurret(BaseTurret):
    _cid = TurretCIDs.ak47
    _max_hp: int = 60

    _default_turn_speed = 2

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Ak47(self, runtime_buffer, False, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(31, 32),
            position,
            weapon,
            1500,
            sensors=[
                RadarSensor(self, 1500)
            ],
            **kwargs
        )


class MortarTurret(BaseTurret):
    _cid = TurretCIDs.mortar
    _max_hp: int = 90
    _aim_type = "high"

    _default_facing_angle = -np.pi / 2
    _default_turn_speed = .3
    _default_max_error = .05
    _default_allow_static_target = True

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Mortar(self, runtime_buffer, False, parent_position_offset=(0, -13))
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(23 * 1.5, 24 * 1.5),
            position,
            weapon,
            3000,
            min_range=550,
            sensors=[
                RadarSensor(self, 3000, min_rcs=0.01)
            ],
            airburst_munition=True,
            **kwargs
        )


class FlakTurret(BaseTurret):
    _cid = TurretCIDs.flak
    _max_hp: int = 170
    _aim_type = "low"

    _default_turn_speed = .8
    _default_valid_angles = (
        Vec2().from_cartesian(-1, .3),
        Vec2().from_cartesian(-.1, -1)
    )
    _default_allow_static_target = True

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Flak(self, runtime_buffer, True, parent_position_offset=(16, -26))
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(98, 44) * 2,
            position,
            weapon,
            2300,
            min_range=300,
            airburst_munition=True,
            intercept_bullets=False,
            target_taps=2,
            sensors=[
                RadarSensor(self, 1700)
            ],
            **kwargs
        )


class CRAMTurret(BaseTurret):
    _cid = TurretCIDs.cram
    _max_hp: int = 60
    _aim_type = "low"

    _default_turn_speed = 1.745
    _default_valid_angles = (
        Vec2().from_cartesian(-.5, 1),
        Vec2().from_cartesian(.5, 1)
    )

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = CRAM(
            self,
            runtime_buffer,
            False,
            parent_position_offset=(0, 15)
        )  # don't eject casings because I like my pc
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(64, 128),
            position,
            weapon,
            1900,
            min_range=150,
            intercept_bullets=True,
            intercept_players=False,
            airburst_munition=True,
            target_taps=8,  # TODO: smart target tap (max)
            sensors=[
                MagicSensor(
                    self,
                    2200,
                    # sphere_accuracy=256,
                    # min_rcs=.04
                )
            ],
            **kwargs
        )


class SkyShield(BaseTurret):
    _cid = TurretCIDs.sky_shield
    _max_hp: int = 60
    _aim_type = "low"

    _default_turn_speed = 1.57
    _default_valid_angles = (
        Vec2().from_cartesian(-.5, 1),
        Vec2().from_cartesian(.5, 1)
    )

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            coalition: Coalitions,
            position: Vec2,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = SkyShieldWeapon(
            self,
            runtime_buffer,
            parent_position_offset=(0, 15)
        )  # don't eject casings because I like my pc
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(64, 128),
            position,
            weapon,
            1900,
            min_range=150,
            intercept_bullets=True,
            intercept_players=False,
            airburst_munition=True,
            target_taps=1,  # TODO: smart target tap (max)
            sensors=[
                MagicSensor(
                    self,
                    2200,
                    # sphere_accuracy=256,
                    # min_rcs=.04
                )
            ],
            **kwargs
        )
