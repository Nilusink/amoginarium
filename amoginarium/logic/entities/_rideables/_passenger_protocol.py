"""
_passenger_protocol.py
05.05.2026

base attributes of an entity that can ride things

Author:
Nilusink
"""
from __future__ import annotations
from icecream import ic
import typing as tp

from .. import LogicGameEntity

if tp.TYPE_CHECKING:
    from ._ridable_protocol import RideableGameEntity


class Passenger:
    """an entity that can ride things"""

    # region ClassVars
    _observe_time: tp.ClassVar[float] = 1  # time after rideable death
    # endregion
    
    def __init__(self, *args, **kwargs) -> None:
        self._controlled_entity: tp.Union["RideableGameEntity", None] = None
        
        # further init MRO chain
        super().__init__(*args, **kwargs)

        self._current_observe_time = 0

    @property
    def is_passenger(self) -> bool:
        """true if currently riding something"""
        return self._controlled_entity is not None

    @property
    def is_controlled(self) -> bool:
        """true if riding and being controlled"""
        return (
            self._controlled_entity is not None
            and self._controlled_entity.control_authority
        )

    @property
    def controlled_entity(self) -> tp.Union["RideableGameEntity", None]:
        """get currently ridden entity"""
        return self._controlled_entity

    def set_controlled_entity(self, entity: RideableGameEntity) -> bool:
        """
        set currently ridden entity

        :param entity: must be "RideablePerks"
        :return: true if success
        """
        if self._controlled_entity:
            return False

        self._controlled_entity = entity
        return True

    def update_passenger(self, delta: float) -> None:
        """update"""
        e: LogicGameEntity = self._controlled_entity  # type: ignore

        if e is not None:
            if not e.alive:
                if self._current_observe_time == 0:
                    self._current_observe_time = self._observe_time

                elif self._current_observe_time > 0:
                    self._current_observe_time -= delta

                elif self._current_observe_time < 0:
                    self._current_observe_time = 0
                    self._controlled_entity = None
