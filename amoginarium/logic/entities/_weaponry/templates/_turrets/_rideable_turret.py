"""
_rideable_turret.py
13.05.2026

Turret that can be ridden

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
from icecream import ic
import typing as tp
import numpy as np

from amoginarium.shared.utility import Vec2, get_default, convert_coord, MASK16, MASK32
from amoginarium.shared.utility import normalize_angle, is_related
from amoginarium.shared import Coalitions, base_entity_t, TurretCIDs, BaseCommandType
from amoginarium.shared import ProcessCommand
from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.audio import MetalPings
from amoginarium import pv

from .....graphics_dummies import Controller
from ...._rideables import Passenger, RideablePerks
from ...._base import LogicGameEntity, GameCollisions
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
    
    __slots__ = ()
    
    # region ClassVars
    _default_size: tp.ClassVar[
        Vec2 | float | tuple[float, float] | list[float]
    ] = (32, 32)
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

    _default_passenger_visible: tp.ClassVar[bool] = True
    _default_passenger_offset: tp.ClassVar[
        Vec2 | list[float] | tuple[float, float]
    ] = (0, 0)
    # endregion
    
    # region InstanceVars
    _hp: float
    _weapon: BaseWeapon
    _passenger_visible: bool
    _passenger_offset: Vec2
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
            self._default_passenger_offset,
            Vec2
        )

        self._valid_angles = ...
        _valid_angles = self._default_engagement_valid_angles
        if not isinstance(_valid_angles, EllipsisType):
            self._valid_angles = [
                Vec2().from_polar(a, 1) if isinstance(a, (float, int)) else a
                for a in _valid_angles
            ]

            self._valid_angles[0].length = self.max_range  # type: ignore
            self._valid_angles[1].length = self.max_range  # type: ignore

        # weapon
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

        # health
        self._hp = self._default_max_hp

        # audio
        self._ping = MetalPings().set_volume(0.4, 0.5)

        # init parent class
        super().__init__(
            runtime_buffer=runtime_buffer,
            size=_size,
            position=position,
            coalition=Coalitions.blue,
            centered=True
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
        if dmg > 0 and event.other_entity.root != self:
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

    def _update(self, delta: float) -> None:
        # update weapon
        self.weapon.update(delta)

        # update keys
        controller = self._controller
        if controller and self._player:
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
            self.facing.angle = vector.angle
            self.weapon.facing.angle = vector.angle

            if controller.ride and not self.__ride_pressed:
                self._player.clear_controlled_entity()
                self._player = None
                self._controller = None

            if controller.shoot:
                self.weapon.shoot(self.facing)

            else:
                self.weapon.stop_shooting()

            self.__ride_pressed = controller.ride

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
