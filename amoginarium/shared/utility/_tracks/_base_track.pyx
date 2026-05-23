"""
Base track class.

Path: amoginarium/shared/utility/_tracks/_base_track.pyx
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from libc.math cimport sqrt

from .._cvectors cimport Vec2
from ._track_enums import TrackQuality, TrackState


cdef class BaseTrack:
    @property
    def state(self) -> TrackState:
        return TrackState(self._track_state)

    @state.setter
    def state(self, new_state: TrackState) -> None:
        self._track_state = new_state.value

    @property
    def quality(self) -> TrackQuality:
        return TrackQuality(self._track_quality)

    def __cinit__(self):
        self._track_state = TrackState.NEW.value
        self._track_quality = TrackQuality.NONE.value

    cpdef reset(self):
        pass

    cpdef initialize(self, double x, double y, double vx, double vy):
        self._track_quality = TrackQuality.POS_ONLY.value

    cdef predict(self, double dt):
        pass

    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        pass

    cpdef step(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        """
        Full filter step.
        """
        self.predict(dt)
        self.update(mx, my, mvx, mvy, dt)

    cpdef Vec2 get_position(self):
        return Vec2().from_cartesian(self.x, self.y)

    cpdef Vec2 get_velocity(self):
        return Vec2().from_cartesian(self.vx, self.vy)

    cpdef Vec2 get_acceleration(self):
        return Vec2().from_cartesian(self.ax, self.ay)

    cpdef Vec2 predict_future_position(self, double t):
        """
        Predict target position t seconds into future.
        """

        cdef double t2 = 0.5 * t * t

        return Vec2().from_cartesian(
            self.x + self.vx * t + self.ax * t2,
            self.y + self.vy * t + self.ay * t2
        )

    cpdef double get_speed(self):
        return sqrt(self.vx * self.vx + self.vy * self.vy)
