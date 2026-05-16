"""
_exacto.py
17.04.2026

Implements both bullet + weapon for the exacto system

Author:
Nilusink
"""

from __future__ import annotations

import math as m
import typing as tp
from ctypes import Array
from types import EllipsisType

from shared import VisibleGameEntityLike

from amoginarium.shared import (
    Coalitions,
    DummyCIDs,
    TurretCIDs,
    WeaponCIDs,
    base_entity_t,
)
from amoginarium.shared.audio import Sniper as SniperSound
from amoginarium.shared.utility import Vec2, coord_t, get_default, normalize_angle

from ...._base import CollisionType, GameCollisions, LogicGameEntity
from ...templates import (
    AerodynamicEntity,
    BaseTurret,
    BaseWeapon,
    RadarSensor,
    TargetSolution,
)


class ExactoBullet(AerodynamicEntity):
    __slots__ = ("_target_callback", "_guidance_delay")

    _CID = DummyCIDs.base_bullet

    _default_ttl = 10
    _default_weight = 5  # knockback
    _default_base_damage = 15

    _default_mass = 0.1  # aerodynamics
    _default_rudder_size = 2
    _default_rudder_max_angle = m.pi

    # _default_cluster_depth = 1
    # _default_cluster_amount = 5
    # _default_cluster_spread = 2.5
    # _default_cluster_fuze_ttl_mult = 0
    # _default_cluster_fuze_dist = 1000
    # _default_cluster_step_inertia = 500

    _default_guidance_delay: float = 0.01

    _max_alpha: float = 0.1

    EXACTO_DOES_NOT_TRACE_ITSELF: CollisionType.ExceptionID = (
        GameCollisions.add_exception()
    )

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        target_callback: tp.Callable[[], Vec2 | None],
        guidance_delay: float | EllipsisType = ...,
        **kwargs,
    ) -> None:
        kwargs.pop("size", ...)
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            coalition=coalition,
            initial_position=initial_position,
            initial_velocity=initial_velocity,
            size=Vec2().from_cartesian(15, 5),
            collision_exception_ids=ExactoBullet.EXACTO_DOES_NOT_TRACE_ITSELF,
            **kwargs,
        )
        self._target_callback = target_callback
        self._cluster_args = {"target_callback": target_callback}
        self._guidance_delay = get_default(guidance_delay, self._default_guidance_delay)

    def _update_rudder(self, delta: float) -> None:
        if self._guidance_delay > 0:
            self._guidance_delay -= delta
            return

        self._target_pos = self._target_callback()

        if self._target_pos:
            delta_pos = self.position - self._target_pos
            delta_angle = self.velocity.angle - delta_pos.angle

            # normalize to +/- m.pi
            delta_angle = (delta_angle + m.pi) % (2 * m.pi) - m.pi

            # calculate rudder pos
            abs_ang = abs(delta_angle)
            if abs(self.alpha) < self._max_alpha:
                self._rudder_angle = (delta_angle // abs_ang) * min(
                    (self._rudder_max_angle, abs_ang * 0.5)
                )

            else:
                self._rudder_angle = 0

        else:
            self._rudder_angle = 0


class ExactoSniper(BaseWeapon):
    """exacto sniper"""

    _CID = WeaponCIDs.exacto_sniper
    _max_range = 3500

    def __init__(
        self,
        parent: LogicGameEntity,
        runtime_buffer: Array[base_entity_t],
        drop_casings: bool = False,
        parent_position_offset: coord_t = Vec2(),
        targeting_func: tp.Callable[[], Vec2 | None] | None = None,
        guidance_delay: float | EllipsisType = ...,
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            reload_time=5,
            recoil_time=2,
            mag_size=6,
            inaccuracy=0.005,
            parent_position_offset=parent_position_offset,
            muzzle_velocity=2500,
            drop_casings=drop_casings,
            sound_effect=SniperSound(),
            bullet_type=ExactoBullet,
            spawn_args={"max_range": self._max_range},
            # bullet args
            time_to_life=15,
            visibility_offset=0.04,
            target_callback=self._get_current_target,
            guidance_delay=guidance_delay,
            **kwargs,
        )
        self._current_target: Vec2 | None = None
        self._targeting_func = targeting_func

    def _get_current_target(self) -> Vec2 | None:
        return self._current_target

    def _update(self, delta: float) -> None:
        super()._update(delta)

        # if no targeting func, target with straight laser
        if not self._targeting_func:
            # entities = Updated.entities() + Players.entities() + [
            #     b for b in Bullets.entities() if b.parent != self
            # ]
            hits = GameCollisions.collision_manager.manual_collision(
                group_ids=GameCollisions.all_groups,
                start_position=self.position
                + Vec2().from_polar(self.facing.angle, 100),
                end_position=self.position
                + Vec2().from_polar(self.facing.angle, self._max_range),
                ignore_collisions=[ExactoBullet.EXACTO_DOES_NOT_TRACE_ITSELF],
            )
            if hits:
                self._current_target = hits[0].position
            else:
                self._current_target = self.position + Vec2().from_polar(
                    self.facing.angle, self._max_range
                )

        else:
            self._current_target = self._targeting_func()

        if self._current_target:
            self._buffer.param3 = int(
                normalize_angle(self._current_target.angle) * 10_000
            )
            self._buffer.param4 = int(self._current_target.length)

        else:
            self._buffer.param4 = 0


class ExactoTurret(BaseTurret):
    _CID = TurretCIDs.exacto_sniper
    _default_max_hp: int = 60

    _default_turn_speed = 2
    _default_weapon_position_offset = (0, -13)
    _default_weapon_type = ExactoSniper

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        coalition: Coalitions,
        position: Vec2,
        **kwargs,
    ) -> None:
        self._coalition = coalition

        super().__init__(
            runtime_buffer,
            coalition,
            position,
            size=Vec2().from_cartesian(31, 32),
            max_range=2400,
            sensors=[
                RadarSensor(
                    runtime_buffer, self, 2500, sphere_accuracy=256, min_rcs=0.03
                )
            ],
            weapon_kwargs={"targeting_func": self.__get_target},
            **kwargs,
        )

        self._current_target = None

    def __get_target(self) -> Vec2 | None:
        """Return current target for exacto"""
        if self._current_target:
            if self._current_target in self.available_targets:
                # raycast towards target
                hits = GameCollisions.collision_manager.manual_collision(
                    group_ids=GameCollisions.all_groups,
                    start_position=self.position
                    + Vec2().from_polar(self.facing.angle, 100),
                    end_position=self._current_target.position,
                    ignore_collisions=[ExactoBullet.EXACTO_DOES_NOT_TRACE_ITSELF],
                )
                if hits:
                    return hits[0].position

                return self._current_target.position

        return None

    def _get_firing_solution(
        self,
        target: VisibleGameEntityLike,
        *,
        recalc: int = 5,
        ignore_velocity: bool = False,
        ignore_acceleration: bool = False,
    ) -> TargetSolution | None:
        # shoot directly at target
        t_pos = target.position
        diff = t_pos - (self.position + self.weapon.parent_position_offset)
        return TargetSolution(
            target_predict=t_pos,
            angle=diff,
            target=target,
            tof=(diff.length / self.weapon.muzzle_velocity) * 1.5,
        )

    def _shoot_weapon(self, solution: TargetSolution) -> bool:
        shot = self.weapon.shoot(
            self.facing,
            solution.tof if self.airburst_munition else ...,
            target_pos=solution.target_predict,
            guidance_delay=0,  # solution.tof * .3
        )

        if shot:
            self._current_target = solution.target

        return shot
