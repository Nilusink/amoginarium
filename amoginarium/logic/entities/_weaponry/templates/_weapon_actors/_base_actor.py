"""
Base weapon actor (sensor, fuze, ...).

| ``Path``: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/_base_actor.py
| ``Project``: amoginarium
| ``Created``: 08.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.utility import convert_coord, get_default, Vec2

from ...._base import DebugCircleEntity

if tp.TYPE_CHECKING:
    from types import EllipsisType

    from amoginarium.shared import MurderViable

    from .._bullets import Bullet


class BaseActor:
    """Detonates a bullet."""

    __slots__ = ("_parent", "_arm_delay", "_offset", "_position", "_last_pos", "_dbe")

    # region ClassVars
    _DEBUG: tp.Final[bool] = False
    # endregion

    # region InstanceVars
    _parent: Bullet
    _arm_delay: float
    _offset: Vec2
    _position: Vec2
    _last_pos: Vec2

    _dbe: DebugCircleEntity | None
    # endregion

    def __init__(
        self,
        parent: Bullet,
        *,
        offset: tuple[float, float] | Vec2 | EllipsisType = ...,
        function_delay: float = 0,
    ) -> None:
        """
        Create a Base weapon actor.

        :param parent: Parent bullet
        :param offset: Offset relative to bullet
        :param function_delay: Delays actors function
        """
        self._parent = parent
        self._arm_delay = function_delay

        # calculate offset
        offset_: Vec2 | tuple[int, int] = get_default(offset, Vec2())
        self._offset: Vec2 = convert_coord(offset_, Vec2)

        self._position = Vec2()
        self._last_pos = Vec2()

        # calculate position with offset
        if self._DEBUG:
            self._dbe = DebugCircleEntity(
                self.parent.runtime_buffer, self._position, 4, centered=True
            )

        else:
            self._dbe = None

        self._update_position()

        # set first "last_pos" to current position
        self._last_pos.xy = self._position.xy

    @property
    def parent(self) -> Bullet:
        """Bullets parent."""
        return self._parent

    def kill(self, killed_by: MurderViable | EllipsisType) -> None:
        """
        Kills this actor.

        :param killed_by: Who killed this actor
        """
        if self._dbe is not None:
            self._dbe.kill(killed_by=killed_by)

    def _update_position(self) -> None:
        """Update fuze position."""
        self._last_pos.xy = self._position.xy

        # add offset with rotation
        self._position.xy = (
            self._parent.position + self._offset.rotate_by(self._parent.facing)
        ).xy

        # update debug entity if set
        if self._dbe:
            self._dbe.position = self._position.copy()

    def _update(self) -> None:
        """Update the fuze."""

    @tp.final
    def update(self) -> None:
        """Update the fuze."""
        self._update_position()

        if self._parent.lifetime >= self._arm_delay:
            self._update()
