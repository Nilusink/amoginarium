"""
_base_actor.py
10.05.2026

base weapon actor (sensor, fuze, ...)

Author:
Nilusink
"""

from types import EllipsisType
import typing as tp

from amoginarium.shared.utility import Vec2, get_default, convert_coord

from ...._base import DebugCircleEntity

if tp.TYPE_CHECKING:
    from .._bullets import Bullet


class BaseActor:
    """detonates a bullet"""

    # region ClassVars
    _DEBUG: tp.ClassVar[bool] = False
    # endregion

    def __init__(
        self,
        parent: "Bullet",
        *,
        offset: tuple[float, float] | Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        base weapon actor

        :param parent: parent bullet
        :param offset: offset relative to bullet
        :param function_delay: delays actors function
        """
        self._parent = parent
        self._arm_delay = function_delay

        # calculate offset
        _offset: Vec2 | tuple[int, int] = get_default(offset, Vec2())
        self._offset: Vec2 = convert_coord(_offset, Vec2)  # type: ignore

        self._position = Vec2()
        self._last_pos = Vec2()

        # calculate position with offset
        if self._DEBUG:
            self._dbe = DebugCircleEntity(
                self.parent.runtime_buffer,
                self._position,
                4,
                centered=True
            )

        else:
            self._dbe = None

        self._update_position()

        # set first "last_pos" to current position
        self._last_pos.xy = self._position.xy

    @property
    def parent(self) -> "Bullet":
        """bullets parent"""
        return self._parent

    def kill(self, killed_by) -> None:
        """kills actor"""
        if self._dbe is not None:
            self._dbe.kill(killed_by)

    def _update_position(self) -> None:
        """update fuze position"""
        self._last_pos.xy = self._position.xy

        # add offset with rotation
        self._position.xy = (
            self._parent.position + self._offset.rotate_by(self._parent.facing)
        ).xy

        # update debug entity if set
        if self._dbe:
            self._dbe.position = self._position.copy()

    def _update(self) -> None:
        """updates the fuze"""

    @tp.final
    def update(self) -> None:
        """updates the fuze"""
        self._update_position()

        if self._parent.lifetime >= self._arm_delay:
            self._update()
