"""
Target tracks.

Documents target position, velocity & acceleration over time.

Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_ctarget_track.pyx
Project: amoginarium
Created: 21.05.2026
Authors: Nilusink
"""

from __future__ import annotations

import typing as tp
from enum import Enum

from amoginarium.shared.utility cimport Vec2


class TrackState(Enum):
    """Track state."""

    NEW = 0
    TENTATIVE = 1
    CONFIRMED = 2
    DEGRADED = 3
    LOST = 4
    DEAD = -1


class TrackQuality(Enum):
    """Specify target track quality."""

    NONE = -1
    POS_ONLY = 0
    POS_AND_VEL = 1
    POS_VEL_ACC = 2


cdef struct simple_vec2:
    double x
    double y
    double dt


cdef class TargetTrack:
    def __cinit__(self) -> None:
        self._track_quality = -1
        self._track_state = 0

        self.position = Vec2()
        self.velocity = Vec2()
        self.acceleration = Vec2()

    # region properties
    @property
    def state(self) -> TrackState:
        """Target track state."""
        return TrackState(self._track_state)

    @property
    def quality(self) -> TrackQuality:
        """Track quality."""
        return TrackQuality(self._track_quality)

    # endregion

    cpdef add_point(self, Vec2 position, double dt):
        cdef size_t n, i_vel
        cdef double dist
        cdef simple_vec2 tmp_sv2
        cdef Vec2 p1, delta

        # append point to position history
        self.position = position.copy()
        self.pos_history.push_back(simple_vec2(
            x=position.x,
            y=position.y,
            dt=dt
        ))
        n = self.pos_history.size()

        # calculate velocity from last two points
        if n > 1:
            tmp_sv2 = self.pos_history.at(n - 2)
            print(tmp_sv2)
            p1 = Vec2().from_cartesian(tmp_sv2.x, tmp_sv2.y)

            print(p1)

            # calculate position delta
            delta = position.sub_vec2(p1)
            dist = delta.get_length()

            print(delta)
            print(dist)

            # calculate velocity
            self.velocity.set_length(dist / dt)
            self.velocity.set_angle(delta.get_angle())

            # add velocity to stack
            self.vel_history.push_back(simple_vec2(
                x=self.velocity.x,
                y=self.velocity.y,
                dt=dt
            ))

        # update track state
        if n > 2:
            self._track_state = TrackState.CONFIRMED.value

        elif n > 1:
            self._track_state = TrackState.TENTATIVE.value
