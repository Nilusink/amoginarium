"""
Base attributes a rideable entity needs.

| ``Path``: amoginarium/logic/entities/_rideables/_ridable_protocol.py
| ``Project``: amoginarium
| ``Created``: 05.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from amoginarium.shared.utility import Vec2


class RideablePerks(tp.Protocol):
    """perks of an entity that can be ridden."""

    __slots__ = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def control_authority(self) -> bool:
        """Specifies weather the entity takes controls or not."""
        return False

    @property
    def passenger_visible(self) -> bool:
        """Specifies weather the passenger is visible or not."""
        return True

    @property
    def camera_centered(self) -> bool:
        return True

    def get_passenger_position(self) -> Vec2 | None:
        """:return: position of passenger if modified"""

    def get_camera_position(self) -> Vec2 | None:
        """:return: position of camera if modified"""

    def get_camera_zoom(self) -> float | None:
        """:return cam zoom if modified"""


RideableGameEntity = RideablePerks

# class RideableGameEntity(RideablePerks, LogicGameEntity):
#     """an entity that can be ridden"""
#     pass
