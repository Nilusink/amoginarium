"""
_base.py
08.05.2026

base fuze

Author:
Nilusink
"""

from types import EllipsisType
import typing as tp

from amoginarium.shared.utility import Vec2, get_default, convert_coord

if tp.TYPE_CHECKING:
    from .._bullets import Bullet


class BaseFuze:
    """detonates a bullet"""

    def __init__(
            self,
            parent: "Bullet",
            *,
            offset: tuple[float, float] | Vec2 | EllipsisType = ...,
            function_delay: float = 0,
    ) -> None:
        self._parent = parent
        self._arm_delay = function_delay

        # calculate offset
        _offset: Vec2 | tuple[int, int] = get_default(offset, Vec2())
        self._offset: Vec2 = convert_coord(_offset, Vec2)  # type: ignore

        self._position = Vec2()
        self._last_pos = Vec2()

        # calculate position with offset
        self._update_position()

        # set first "last_pos" to current position
        self._last_pos.xy = self._position.xy

    @property
    def parent(self) -> "Bullet":
        """bullets parent"""
        return self._parent

    def _update_position(self) -> None:
        """update fuze position"""
        self._last_pos.xy = self._position.xy

        # add offset with rotation
        self._position.xy = (
            self._parent.position + self._offset.rotate_by(self._parent.facing)
        ).xy

    def _update(self) -> None:
        """updates the fuze"""
        self._update_position()

    @tp.final
    def update(self) -> None:
        """updates the fuze"""
        if self._parent.lifetime >= self._arm_delay:
            self._update()
