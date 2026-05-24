"""
Base track class.

Path: amoginarium/shared/utility/_tracks/_base_track.pyx
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from libc.math cimport sqrt

from .._cvectors cimport Vec2

from ._track_enums import TRACK_HALF_TIME, TrackQuality, TrackState


cdef class BaseTrack:
    @property
    def state(self) -> TrackState:
        if (
            self.last_update >= TRACK_HALF_TIME * 3
            or self._track_state == TrackState.DEAD.value
        ):
            return TrackState.DEAD

        elif self.last_update >= TRACK_HALF_TIME * 2:
            return TrackState.LOST

        elif self.last_update >= TRACK_HALF_TIME:
            return TrackState.DEGRADED

        return TrackState(self._track_state)

    @property
    def quality(self) -> TrackQuality:
        return TrackQuality(self._track_quality)

    @property
    def time_since_last_update(self) -> float:
        return self.last_update

    def __cinit__(self):
        self._track_state = TrackState.NEW.value
        self._track_quality = TrackQuality.NONE.value
        self.last_update = 0

    cpdef increment_time(self, double dt):
        self.last_update += dt
        self.predict(dt)

    cpdef reset(self):
        pass

    cpdef initialize(self, double x, double y, double vx, double vy):
        self._track_quality = TrackQuality.POS_ONLY.value
        self.last_update = 0

    cdef predict(self, double dt):
        pass

    cdef update(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        self.last_update = 0

        # update track state
        if self._track_state == TrackState.NEW.value:
            self._track_state = TrackState.TENTATIVE.value

        else:
            # doesn't matter what last state was, if updated and not new it is not confirmed
            self._track_state = TrackState.CONFIRMED.value

    cpdef step(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        """
        Full filter step.
        """
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

    cpdef kill(self):
        self._track_state = TrackState.DEAD.value
