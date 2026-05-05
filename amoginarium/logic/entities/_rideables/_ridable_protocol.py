"""
_ridable_protocol.py
05.05.2026

base attributes a rideable entity needs

Author:
Nilusink
"""

import typing as tp

from amoginarium.shared.utility import Vec2
from amoginarium.shared import Controls

from .._base import LogicGameEntity


class RideablePerks(tp.Protocol):
    """perks of an entity that can be ridden"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def control_authority(self) -> bool:
        """specifies weather the entity takes controls or not"""

    @property
    def passenger_visible(self) -> bool:
        """specifies weather the passenger is visible or not"""

    def set_controls(self, controls: Controls) -> None:
        """set rideable controls"""

    def get_passenger_position(self) -> None | Vec2:
        """:returns: position of passenger if modified"""

    def get_camera_position(self) -> None | Vec2:
        """:returns: position of camera if modified"""

    def get_camera_zoom(self) -> None | float:
        """:returns cam zoom if modified"""


class RideableGameEntity(RideablePerks, LogicGameEntity):
    """an entity that can be ridden"""
    pass
