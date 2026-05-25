"""
Base attributes of an entity that can ride things.

| ``Path``: amoginarium/logic/entities/_rideables/_passenger_protocol.py
| ``Project``: amoginarium
| ``Created``: 05.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from .. import LogicGameEntity
    from ._ridable_protocol import RideableGameEntity


class Passenger:
    """an entity that can ride things."""

    # region ClassVars
    _observe_time: tp.ClassVar[float] = 1  # time after rideable death
    # endregion

    # region InstanceVars
    _controlled_entity: list[RideableGameEntity]
    _current_observe_time: float  # endregion

    def __init__(self, *args, **kwargs) -> None:
        self._controlled_entity = []

        # further init MRO chain
        super().__init__(*args, **kwargs)

        self._current_observe_time = 0

    @property
    def is_passenger(self) -> bool:
        """True if currently riding something."""
        return len(self._controlled_entity) > 0

    @property
    def is_controlled(self) -> bool:
        """True if riding and being controlled."""
        ce = self.controlled_entity
        return ce is not None and ce.control_authority

    @property
    def controlled_entity(self) -> RideableGameEntity | None:
        """Get currently ridden entity."""
        if len(self._controlled_entity) > 0:
            return self._controlled_entity[-1]

        return None

    def set_controlled_entity(self, entity: RideableGameEntity) -> bool:
        """
        Set currently ridden entity.

        :param entity: must be "RideablePerks"
        :return: true if success
        """
        # if self._controlled_entity:
        #     return False

        self._controlled_entity.append(entity)
        return True

    def clear_controlled_entity(self, to_clear: RideableGameEntity) -> bool:
        """
        Clear currently ridden entity.

        :param to_clear: entity to clear from stack
        :returns: true if success
        """
        if to_clear in self._controlled_entity:
            self._controlled_entity.remove(to_clear)
            return True

        return False

    def update_passenger(self, delta: float) -> None:
        """Update."""
        for i, e in enumerate(self._controlled_entity):
            e: LogicGameEntity
            if not e.alive:
                if i == len(self._controlled_entity) - 1:
                    if self._current_observe_time == 0:
                        self._current_observe_time = self._observe_time

                    elif self._current_observe_time > 0:
                        self._current_observe_time -= delta

                    elif self._current_observe_time < 0:
                        self._current_observe_time = 0
                        self.clear_controlled_entity(e)

                else:
                    self.clear_controlled_entity(e)
