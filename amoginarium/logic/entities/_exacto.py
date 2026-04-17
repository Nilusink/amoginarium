"""
_exacto.py
17.04.2026

Implements both bullet + weapon for the exacto system

Author:
Nilusink
"""

from ctypes import Array
import typing as tp
import math as m

from amoginarium.shared.utility import Vec2, coord_t, multi_raycast_mask, normalize_angle
from amoginarium.shared import base_entity_t, Coalitions, WeaponCIDs, DummyCIDs

from ..audio import Sniper as SniperSound
from ._aerodynamic_entity import AerodynamicEntity
from ._logic_groups import Updated, Walls
from ._base_entity import LogicGameEntity
from ._weapons import BaseWeapon


class ExactoBullet(AerodynamicEntity):

    __slots__ = ("_target_callback", "_guidance_delay")

    _cid = DummyCIDs.base_bullet

    _weight = 5  # knockback
    _default_base_damage = 15

    _default_mass = .1  # aerodynamics
    _default_rudder_size = 2
    _default_rudder_max_angle = m.pi

    _default_guidance_delay: float = .01
    
    _max_alpha: float = .1

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        target_callback: tp.Callable[[], Vec2],
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer=runtime_buffer,
            parent=parent,
            coalition=coalition,
            initial_position=initial_position,
            initial_velocity=initial_velocity,
            size=Vec2().from_cartesian(15, 5),
            **kwargs
        )
        self._target_callback = target_callback
        self._guidance_delay = self._default_guidance_delay

    def _update_rudder(self, delta: float) -> None:
        if self._guidance_delay > 0:
            self._guidance_delay -= delta
            return

        target = self._target_callback()

        delta_pos = self.position - target
        delta_angle = self.velocity.angle - delta_pos.angle

        # normalize to +/- m.pi
        delta_angle = (delta_angle + m.pi) % (2 * m.pi) - m.pi

        # calculate rudder pos
        abs_ang = abs(delta_angle)
        if abs(self.alpha) < self._max_alpha:
            self._rudder_angle = (delta_angle // abs_ang) * min(
                (self._rudder_max_angle, abs_ang*abs_ang)
            )

        else:
            self._rudder_angle = 0
        

class ExactoSniper(BaseWeapon):
    """exacto sniper"""

    _cid = WeaponCIDs.exacto_sniper
    _max_range = 3500

    def __init__(
        self,
        parent: LogicGameEntity,
        runtime_buffer: Array[base_entity_t],
        drop_casings: bool = False,
        parent_position_offset: coord_t = Vec2(),
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
            visibility_offset=.04,
            target_callback=self._get_current_target
        )
        self._current_target = Vec2()

    def _get_current_target(self) -> Vec2:
        return self._current_target

    def _update(self, delta: float) -> None:
        super()._update(delta)

        hits = multi_raycast_mask(
            self,
            Walls.sprites() + Updated.sprites(),
            self.position + Vec2().from_polar(self.facing.angle, 100),
            self.position + Vec2().from_polar(self.facing.angle, self._max_range),
        )
        if hits:
            hits = [hit[1] for hit in hits]
            hits = sorted(hits, key=lambda e: e.length)

            self._current_target.xy = hits[0].xy

        else:
            self._current_target.xy = (self.position + Vec2().from_polar(
                self.facing.angle, self._max_range
            )).xy

        self._buff.param3 = int(normalize_angle(self._current_target.angle) * 10_000)
        self._buff.param4 = int(self._current_target.length)
