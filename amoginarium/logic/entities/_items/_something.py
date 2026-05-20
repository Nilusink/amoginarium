"""
IDK what this is. Definitely something.

Path: amoginarium/logic/entities/_items/_something.py
Project: amoginarium
Created: 18.04.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from ._item import Item

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t, MurderViable
    from amoginarium.shared.utility import Vec2

    from .._base import LogicGameEntity


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
        """Max amount of uses."""
        return self._max_uses

    @property
    def uses_left(self) -> int:
        """Uses left."""
        return self._uses_left

    # endregion

    def add_used_callback(self, callback: tp.Callable[[int], bool]) -> None:
        """Gets called when item is used up."""
        self._used_callback = callback

    def _update(self, delta: float, *, keep_position: bool = False) -> None:
        super()._update(delta, keep_position=keep_position)
        self._runtime_buffer[self.id].param1, _ = self.get_mag_state(1)

    # region interface
    def get_mag_state(self, max_out: float) -> tuple[float, int] | tuple[float, float]:
        """
        Returns the current uses (rising when reloading)
        naming borrowed from BaseWeapon for compatability.

        :param max_out: output size
        :returns: x out of max_out, value of current state
        """
        return self._uses_left * (max_out / self._max_uses), self._uses_left

    def use(self) -> None:
        """Use the item."""
        raise NotImplementedError

    def stop_use(self) -> None:
        """Stop using the item."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop ... again?"""
        self.stop_use()
        self._set_bit("flags", 14, False)  # set use to false


    def _after_kill(
        self,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
        killed: bool = True,
    ) -> None:
        ...

    @tp.override
    def _before_kill(
        self,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> bool:
        """
        If the item is used up but gets reused, it will be reset instead of killed
        :param killed_by: who killed this entity
        :param kill_children: whether to kill children as well recursively
        :return: False if the item gets reused
        """
        if self._used_callback and self._used_callback(1):
            self.reset()
            return False
        return True

    def reset(self) -> None:
        """Reset the item."""
        self._uses_left = self._max_uses

    # endregion
