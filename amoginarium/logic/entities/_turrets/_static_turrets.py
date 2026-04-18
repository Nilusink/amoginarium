"""
_static_turrets.py
01.04.2026

base turret types

Author:
Nilusink
"""

from ctypes import Array
import numpy as np

from amoginarium.shared import Coalitions, base_entity_t
from amoginarium.shared import TurretCIDs
from amoginarium.shared.utility import Vec2

from .._weapons import Minigun, Sniper, Ak47, Mortar, Flak, CRAM, SkyShieldWeapon
from .._sensors import MagicSensor, RadarSensor

from ._base_turret import BaseTurret


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
                MagicSensor(runtime_buffer, self, 1500)
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
                RadarSensor(runtime_buffer, self, 2500, sphere_accuracy=256)
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
                RadarSensor(runtime_buffer, self, 1600)
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
            cluster: bool = False,
            **kwargs
    ) -> None:
        self._coalition = coalition  # needed because the weapon wants it
        weapon = Mortar(
            self,
            runtime_buffer,
            False,
            parent_position_offset=(0, -13),
            cluster=cluster
        )
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
                RadarSensor(runtime_buffer, self, 2500, min_rcs=0.01)
            ],
            airburst_munition=cluster,
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
                RadarSensor(runtime_buffer, self, 1700)
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
                RadarSensor(
                    runtime_buffer,
                    self,
                    2200,
                    sphere_accuracy=256,
                    min_rcs=.04
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
        Vec2().from_cartesian(-1, .2),
        Vec2().from_cartesian(1, .2)
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
            parent_position_offset=(0, -8)
        )  # don't eject casings because I like my pc
        weapon.reload(True)

        super().__init__(
            runtime_buffer,
            coalition,
            Vec2().from_cartesian(128, 128),
            position,
            weapon,
            2300,
            min_range=150,
            intercept_bullets=True,
            intercept_players=False,
            airburst_munition=True,
            target_taps=1,  # TODO: smart target tap (max)
            sensors=[
                RadarSensor(
                    runtime_buffer,
                    self,
                    2200,
                    sphere_accuracy=256,
                    min_rcs=.04
                )
            ],
            **kwargs
        )

    def _update(self, delta: float) -> None:
        super()._update(delta)
        self.facing.x = self.weapon.facing.x
        self.facing.normalize()
