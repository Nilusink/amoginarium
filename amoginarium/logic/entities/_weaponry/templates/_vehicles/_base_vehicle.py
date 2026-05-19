"""
Base for all vehicle types.

Path: amoginarium/logic/entities/_weaponry/templates/_vehicles/_base_vehicle.py
Project: amoginarium
Created: 19.05.2026
Authors: Nilusink
"""

from __future__ import annotations

import typing as tp
from types import EllipsisType

from icecream import ic

from amoginarium.shared import Coalitions

from .._turrets import RideableTurret

if tp.TYPE_CHECKING:
    from ctypes import Array

    from amoginarium.shared import base_entity_t

from amoginarium.shared.utility import Vec2


class Vehicle(RideableTurret):
    """Base class for all vehicle types."""

    __slots__ = ()

    # region ClassVars
    _default_size: tp.ClassVar[tuple[int, int] | list[int]] = (128, 64)
    # endregion

    # region InstanceVars
    # endregion

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        coalition: Coalitions,
        position: Vec2,
        *,
        size: Vec2 | float | tuple[float, float] | list[float] | EllipsisType = ...,
        weapon_kwargs: dict[str, tp.Any] | EllipsisType = ...,
    ) -> None:
        super().__init__(
            runtime_buffer,
            size=size,
            position=position,
            coalition=coalition,
            weapon_kwargs=weapon_kwargs,
        )
