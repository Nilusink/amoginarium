"""
_passenger_protocol.py
05.05.2026

base attributes of an entity that can ride things

Author:
Nilusink
"""
from __future__ import annotations
import typing as tp

if tp.TYPE_CHECKING:
    from ._ridable_protocol import RideableGameEntity


class Passenger:
    """an entity that can ride things"""
    def __init__(self, *args, **kwargs) -> None:
        self._controlled_entity: tp.Union["RideableGameEntity", None] = None
        
        # further init MRO chain
        super().__init__(*args, **kwargs)

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

    def update_passenger(self) -> None:
        """update"""
        e = self._controlled_entity

        if e is not None:
            if not e.alive:
                self._controlled_entity = None
