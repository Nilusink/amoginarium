"""
_base.py
10.05.2026

base weapons sensor used in weapons guidance

Author:
Nilusink
"""

from abc import ABC, abstractmethod

# from types import EllipsisType
# import typing as tp
from amoginarium.shared import DynamicEntityParentViable, WeaponSensorCIDs
from amoginarium.shared.utility import Vec2

from .._base_actor import BaseActor

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
        """Component ID"""
        return cls._CID.value

    # endregion

    # region interface
    @abstractmethod
    def get_target(self) -> Vec2 | None:
        """Get sensor target"""

    # endregion
