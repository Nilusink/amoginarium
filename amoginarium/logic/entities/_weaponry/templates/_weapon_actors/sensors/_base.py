"""
Base weapons sensor used in weapons guidance.

Path: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/sensors/_base.py
Project: amoginarium
Created: 10.05.2026
Authors: Nilusink
"""

from abc import ABC, abstractmethod

from amoginarium.shared import DynamicEntityParentViable, WeaponSensorCIDs
from amoginarium.shared.utility import Vec2

from .._base_actor import BaseActor

# from types import EllipsisType
# import typing as tp


# if tp.TYPE_CHECKING:
#     from ..._bullets import AerodynamicEntity


class BaseWeaponsSensor(DynamicEntityParentViable, BaseActor, ABC):
    """sensor for weapons guidance"""

    _CID = WeaponSensorCIDs.base

    # def __init__(
    #     self,
    #     parent: "AerodynamicEntity",
    #     *,
    #     offset: tuple[float, float] | Vec2 | EllipsisType = ...,
    #     function_delay: float = 0,
    # ) -> None:
    #     super().__init__(parent, offset=offset, function_delay=function_delay)
    #
    # region class methods
    @classmethod
    def has_cid(cls) -> bool:
        return True

    @classmethod
    def cid(cls) -> str:
        """component ID"""
        return cls._CID.value

    # endregion

    # region interface
    @abstractmethod
    def get_target(self) -> Vec2 | None:
        """get sensor target"""

    # endregion
