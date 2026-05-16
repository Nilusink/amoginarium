"""
amoginarium/logic/entities/_items/_jet_bag.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from ctypes import Array

from amoginarium.shared.utility import Vec2
from amoginarium.shared import base_entity_t, ItemCIDs
from amoginarium import pv

from amoginarium.shared.audio import RocketSound
from ._something import Something
from .._base import GameCollisions


class JetBag(Something):
    """makes you flyyyyyy"""

    _CID = ItemCIDs.jetbag
    _reload_per_second: float = 0.5
    _acceleration = 19
    _max_uses: int = 5

    __slots__ = ("_in_use", "_facing", "_size_fac", "_sound")

    def __init__(
        self,
        runtime_buffer: Array[base_entity_t],
        parent_position_offset: Vec2,
    ) -> None:
        super().__init__(
            runtime_buffer,
            Vec2().from_cartesian(32, 64),
            parent_position_offset=parent_position_offset,
        )

        self._sound = RocketSound()
        self._in_use = False
        self._facing = True
        self._size_fac = 1

    def use(self) -> None:
        self._in_use = True

    def stop_use(self) -> None:
        self._in_use = False
        if self._sound.playing:
            self._sound.stop()

    def _update(self, delta: float, **_) -> None:
        if not self.parent:
            self._set_bit("flags", 14, False)  # set use to false
            super()._update(delta)
            return

        # set in use
        self._set_bit("flags", 14, self._in_use)

        # adjust position
        self.facing.angle = self.parent.facing.angle

        if self.facing.x > 0:
            self.position = self.parent.position + self._parent_position_offset
            self.position -= self.size / 2

        else:
            self.position = self.parent.position - self._parent_position_offset
            self.position -= self.size / 2

        if self._in_use:
            if self._uses_left > 0:
                self._uses_left -= delta

                if self._uses_left > 2 * delta:
                    if not self._sound.playing:
                        self._sound.play(pos=self.position)

                if self._sound.playing:
                    self._sound.update_position(self.position)

                if hasattr(self.parent, "_impulse_resistance_factor"):
                    # noinspection PyProtectedMember
                    recoil = Vec2().from_cartesian(
                        0, -self.parent._impulse_resistance_factor
                    )
                    recoil.length *= (
                        self._acceleration * pv.global_vars.get_acceleration_factor()
                    )
                    self.parent.add_acceleration(recoil)

            else:
                if self._sound.playing:
                    self._sound.stop()

                self._set_bit("flags", 14, False)  # set use to false

        elif GameCollisions.collision_group_islands in self.parent._active_normals:
            for normal in self.parent._active_normals[
                GameCollisions.collision_group_islands
            ]:
                if normal.y < -0.5:
                    if self._uses_left < self._max_uses:
                        self._uses_left = min(
                            self._uses_left + self._reload_per_second * delta,
                            self._max_uses,
                        )
                    continue

        super()._update(delta, keep_position=True)
