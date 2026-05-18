"""
IDK what this is. Definitely something.

Path: amoginarium/logic/entities/_items/_something.py
Project: amoginarium
Created: 18.04.2026
Authors: Nilusink, LukasKrah
"""

import typing as tp
from ctypes import Array
from types import EllipsisType

from amoginarium.shared import base_entity_t
from amoginarium.shared.utility import Vec2

from .._base import LogicGameEntity
from ._item import Item


class Something(Item):
    _max_uses: tp.ClassVar[int] = 1

    __slots__ = ("_uses_left", "_parent_position_offset", "_used_callback")

    _uses_left: int
    _parent_position_offset: Vec2
    _used_callback: tp.Callable[[int], bool] | None

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        size: Vec2,
        parent_position_offset: Vec2,
    ) -> None:
        super().__init__(runtime_buffer, size)
        self._uses_left = self._max_uses
        self._parent_position_offset = parent_position_offset
        self._used_callback = None

    # region properties
    # noinspection PyTypeChecker
    @property
    def max_uses(self) -> int:
        """max amount of uses"""
        return self._max_uses

    @property
    def uses_left(self) -> int:
        """uses left"""
        return self._uses_left

    # endregion

    def add_used_callback(self, callback: tp.Callable[[int], bool]) -> None:
        """gets called when item is used up"""
        self._used_callback = callback

    def _update(self, delta: float, *, keep_position: bool = False) -> None:
        super()._update(delta, keep_position=keep_position)
        self._runtime_buffer[self.id].param1, _ = self.get_mag_state(1)

    # region interface
    def get_mag_state(self, max_out: float) -> tuple[float, int] | tuple[float, float]:
        """
        returns the current uses (rising when reloading)
        naming borrowed from BaseWeapon for compatability

        :param max_out: output size
        :returns: x out of max_out, value of current state
        """
        return self._uses_left * (max_out / self._max_uses), self._uses_left

    def use(self) -> None:
        """use the item"""
        raise NotImplementedError

    def stop_use(self) -> None:
        """stop using the item"""
        raise NotImplementedError

    def stop(self) -> None:
        """stop ... again?"""
        self.stop_use()
        self._set_bit("flags", 14, False)  # set use to false

    def _kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> None:
        if self._used_callback and self._used_callback(1):
            self._uses_left = self._max_uses

        else:
            super()._kill()

    def reset(self) -> None:
        """reset the item"""
        self._uses_left = self._max_uses

    # endregion
