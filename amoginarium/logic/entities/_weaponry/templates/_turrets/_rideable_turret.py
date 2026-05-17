"""
_rideable_turret.py
13.05.2026

Turret that can be ridden

Author:
Nilusink
"""

import typing as tp
from ctypes import Array
from types import EllipsisType

import numpy as np
from icecream import ic
from logic.entities import BaseLogicEntity

from amoginarium import pv
from amoginarium.shared import base_entity_t, BaseCommandType
from amoginarium.shared import Coalitions, ProcessCommand, TurretCIDs
from amoginarium.shared.audio import MetalPings
from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.utility import convert_coord, get_default, MASK16
from amoginarium.shared.utility import MASK32, normalize_angle, Vec2

from .....graphics_dummies import Controller
from ...._base import GameCollisions, LogicGameEntity
from ...._rideables import Passenger, RideablePerks
from .._weapons import BaseWeapon

if tp.TYPE_CHECKING:
    from ...._player import Player
    from .._bullets import Bullet


class RideableTurret(RideablePerks, LogicGameEntity):
    """
    a fixed-position turret than can be ridden
    """

    _CID = TurretCIDs.rideable_base
    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_rideable_turrets

    __slots__ = (
        "_hp",
        "_weapon",
        "_passenger_visible",
        "_passenger_offset",
        "_turn_speed",
    )

    # region ClassVars
    _default_size: tp.ClassVar[Vec2 | float | tuple[float, float] | list[float]] = (
        32,
        32,
    )
    _default_max_hp: tp.ClassVar[float] = 50
    _default_turn_speed: tp.ClassVar[float] = np.inf
    _default_facing_angle: tp.ClassVar[float] = 0
    _default_airburst_munition: tp.ClassVar[bool] = False

    _default_engagement_valid_angles: tp.ClassVar[
        tuple[float, float] | EllipsisType
    ] = ...
    _default_engagement_min_range: tp.ClassVar[float] = 0
    _default_engagement_max_range: tp.ClassVar[float] = 300

    _default_target_taps: tp.ClassVar[int] = 1  # shots per click

    _default_weapon_type: tp.Type[BaseWeapon] | EllipsisType = ...
    _default_weapon_drop_casings: tp.ClassVar[bool] = False
    _default_weapon_position_offset: tp.ClassVar[
        Vec2 | list[float] | tuple[float, float]
    ] = (0, 0)
    _default_weapon_static_facing: tp.ClassVar[float | EllipsisType] = ...
    _default_engagement_ignore_solution: tp.ClassVar[bool] = False

    _default_passenger_visible: tp.ClassVar[bool] = True
    _default_passenger_offset: tp.ClassVar[Vec2 | list[float] | tuple[float, float]] = (
        0,
        0,
    )
    # endregion

    # region InstanceVars
    _hp: float
    _weapon: BaseWeapon
    _passenger_visible: bool
    _passenger_offset: Vec2
    _turn_speed: float

    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        coalition: Coalitions,
        position: Vec2,
        *,
        cluster: bool = False,
        size: Vec2 | float | tuple[float, float] | list[float] | EllipsisType = ...,
        weapon_kwargs: dict[str, tp.Any] | EllipsisType = ...,
    ) -> None:
        # get size and convert to Vec2
        _size: Vec2 = convert_coord(  # type: ignore
            get_default(size, self._default_size), Vec2
        )
        weapon_kwargs: dict = get_default(weapon_kwargs, {})

        # get defaults
        self._passenger_visible = self._default_passenger_visible
        self._passenger_offset: Vec2 = convert_coord(  # type: ignore
            self._default_passenger_offset, Vec2
        )
        self._turn_speed: float = get_default(self._default_turn_speed, np.inf)

        self._valid_angles = ...
        _valid_angles = self._default_engagement_valid_angles
        if not isinstance(_valid_angles, EllipsisType):
            self._valid_angles = [
                Vec2().from_polar(a, 1) if isinstance(a, (float, int)) else a
                for a in _valid_angles
            ]

            self._valid_angles[0].length = self.max_range  # type: ignore
            self._valid_angles[1].length = self.max_range  # type: ignore

        # region weapon creation
        if isinstance(self._default_weapon_position_offset, Vec2):
            offset = self._default_weapon_position_offset

        else:
            offset = Vec2().from_cartesian(
                self._default_weapon_position_offset[0],
                self._default_weapon_position_offset[1],
            )

        if isinstance(self._default_weapon_type, EllipsisType):
            raise RuntimeError(f"No weapon set for {self.__class__.__name__}")

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
        # endregion

        # health
        self._hp = self._default_max_hp

        # audio
        self._ping = MetalPings().set_volume(0.4, 0.5)

        # targeting
        self._target_angle = Vec2()

        # init parent class
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=_size,
            position=position,
            coalition=Coalitions.blue,
            centered=True,
        )
        self.weapon.set_parent(self)
        self.weapon.show()

        # create collision
        self._create_collision()

        # player variables
        self._player: tp.Union["Player", None] = None
        self._controller: tp.Union[Controller, None] = None
        self.__ride_pressed = False

        # spawn logic dummy
        pv.COQ.put(
            ProcessCommand(
                type=BaseCommandType.spawn_dummy,
                kwargs={"id": self.id, "cid": self.cid(), "weapon_id": self.weapon.id},
            )
        )

    # region properties
    @property
    def min_range(self) -> float:
        """min engagement range"""
        return self._default_engagement_min_range

    @property
    def max_range(self) -> float:
        """max engagement range"""
        return self._default_engagement_max_range

    @property
    def root(self) -> BaseLogicEntity:
        # return player if ridden
        if self._player:
            return self._player

        return super().root

    # endregion

    # region rideable interface
    @property
    def control_authority(self) -> bool:
        return True

    @property
    def passenger_visible(self) -> bool:
        return self._passenger_visible

    def get_passenger_position(self) -> None | Vec2:
        return self.position + self._passenger_offset

    def get_camera_position(self) -> None | Vec2:
        return self.position

    def get_camera_zoom(self) -> None | float:
        return None

    def set_passenger(self, passenger: "Player") -> bool:
        """
        assign passenger to turret

        :returns: True if successful
        """
        # get player and controller
        self._player = passenger

        # check for passenger protocol
        if not isinstance(self._player, Passenger):
            return False

        self._player.set_controlled_entity(self)

        # get controller
        self._controller = self._player.controller

        self.__ride_pressed = True

        return True

    # endregion

    # region collision
    def __on_collision_bullet(self, event: CollisionEvent["Bullet"]) -> None:
        dmg = event.other_entity.damage
        if dmg > 0 and event.other_entity.root != self.root:
            ic(event.other_entity.root, self, self.weapon)
            self.hit(dmg, hit_by=event.other_entity)

    def _collision_start(
        self, events: list[CollisionEvent[tp.Union["Bullet", "Player"]]]
    ) -> None:
        # bullet - 5 turrets - events länge 5
        # turret - events 1 bullet
        for event in events:
            if event.group_id == GameCollisions.collision_group_bullets:
                event: CollisionEvent["Bullet"]
                self.__on_collision_bullet(event)

    # endregion

    def hit(self, damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        """
        deal damage to the turret
        """
        self._hp -= damage

        # ping on bullet hit
        if not isinstance(hit_by, EllipsisType):
            if hit_by._tags.__contains__("bullet"):
                self._ping.play(pos=self.position)

        # check for turret death
        if self._hp <= 0:
            self.kill(hit_by)

    def _shoot_at(
        self,
        target_angle: Vec2,
        tof: float | EllipsisType = ...,
        target_pos: Vec2 | EllipsisType = ...,
        **bullet_args,
    ) -> None:
        """checks if shot is inside parameters"""
        self.weapon.shoot(
            self.weapon.facing, bullet_tof=tof, target_pos=target_pos, **bullet_args
        )

    def _update(self, delta: float, set_facing: bool = True) -> None:
        # update weapon
        self.weapon.update(delta)

        # update keys
        controller = self._controller
        if controller and self._player:
            self._set_bit("flags", 14, True)  # set ridden
            # update facing
            ppm = pv.global_vars.get_pixel_per_meter()
            ssf = pv.global_vars.get_screen_size_fac()

            mouse_pos = controller.mouse_x, controller.mouse_y
            vector: Vec2 = convert_coord(  # type: ignore
                (
                    (mouse_pos[0] / ppm) * ssf.x,
                    (mouse_pos[1] / ppm) * ssf.y,
                ),
                Vec2,
            )
            vector -= self.world_position
            self._target_angle.xy = vector.xy

            if set_facing:
                self._turn_at(vector.angle, delta)

            if controller.ride and not self.__ride_pressed:
                self._player.clear_controlled_entity(self)
                self._player = None
                self._controller = None

            if controller.shoot:
                self._shoot_at(self._target_angle)

            else:
                self.weapon.stop_shooting()

            if controller.reload:
                self.weapon.reload()

            self.__ride_pressed = controller.ride

        else:
            self._set_bit("flags", 14, False)  # reset ridden

        # check if reload
        if self.weapon.get_mag_state(1)[0] == 0:
            self.weapon.reload()

        # HP
        self._runtime_buffer[self.id].param0 = self._hp / self._default_max_hp

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

        super()._update(delta)

    def _turn_at(self, angle: float, dt: float) -> None:
        """turn towards a target"""
        if not isinstance(self._default_weapon_static_facing, EllipsisType):
            self.weapon.facing.angle = self._default_weapon_static_facing
            return

        diff = angle - self.facing.angle

        if diff > np.pi:
            diff -= 2 * np.pi

        if diff < -np.pi:
            diff += 2 * np.pi

        # limit turn speed
        increment = np.sign(diff) * min(abs(diff), self._turn_speed * dt)
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
