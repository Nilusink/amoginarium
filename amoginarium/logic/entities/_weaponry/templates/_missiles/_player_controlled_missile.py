"""
_player_controlled_missile.py
12.05.2026

MultiStageMissile than can be controlled by the player

Author:
Nilusink
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared import Coalitions, base_entity_t, MissileCIDs
from amoginarium.shared.utility import Vec2

from ...._base import LogicGameEntity, Updated
from ...._rideables import Passenger, RideablePerks
from ._multi_stage_missile import MultiStageMissile


if tp.TYPE_CHECKING:
    from ...._player import Player


class PlayerControlledMissile(RideablePerks, MultiStageMissile):

    _CID = MissileCIDs.player_controlled

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent: LogicGameEntity,
        coalition: Coalitions,
        initial_position: Vec2,
        initial_velocity: Vec2,
        *,
        initial_facing: float | EllipsisType = ...,
        rudder_size: float | EllipsisType = ...,
        rudder_max_angle: float | EllipsisType = ...,
        base_mass: float | EllipsisType = ...,
        collision_exception_ids: list[int] | int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            runtime_buffer,
            parent,
            coalition,
            initial_position,
            initial_velocity,
            initial_facing=initial_facing,
            rudder_size=rudder_size,
            rudder_max_angle=rudder_max_angle,
            base_mass=base_mass,
            collision_exception_ids=collision_exception_ids,
            **kwargs
        )

        # get player
        self._player: "Player" = self.root  # type: ignore

        # check for passenger protocol
        if not isinstance(self._player, Passenger):
            self.kill(self)
            return
        
        # set self as ridden entity
        self._player.set_controlled_entity(self)
        
        # get controller
        self._controller = self._player.controller

        self._kill_time = -1

    # region Rideable interface
    @property
    def control_authority(self) -> bool:
        return True
    
    @property
    def passenger_visible(self) -> bool:
        return True
    
    def get_passenger_position(self) -> None | Vec2:
        return None
    
    def get_camera_position(self) -> None | Vec2:
        return self.position.copy()
    
    def get_camera_zoom(self) -> None | float:
        return None
    
    # endregion
    
    def _update_rudder(self, delta: float) -> None:
        self._rudder_angle = 0

        # check for controller
        if not self._controller:
            return

        if self._controller.joy_x > .1:
            self._rudder_angle = self._rudder_max_angle

        elif self._controller.joy_x < -.1:
            self._rudder_angle = -self._rudder_max_angle
