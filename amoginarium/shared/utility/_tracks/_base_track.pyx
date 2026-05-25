"""
Base track class.

Path: amoginarium/shared/utility/_tracks/_base_track.pyx
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from libc.math cimport sqrt

from .._cvectors cimport Vec2
from ._ctrack_enums cimport ballistic_track_class, maneuvering_track_class
from ._ctrack_enums cimport motion_track_type, orbital_track_class
from ._ctrack_enums cimport surface_track_class, unknown_track_class

from ._track_enums import TRACK_HALF_TIME, TrackQuality, TrackState


cdef const double CLASSIFICATION_TOLERANCE = 16.0
cdef const double CLASSIFICATION_MANEUVER_TOLERANCE = 0.2
cdef const double CLASSIFICATION_THRUST_TOLERANCE = 64.0
cdef const double CLASSIFICATION_VEHICLE_MINSIZE = 256.0  # (x + y)
cdef const double CLASSIFICATION_MUNITION_MAX_SIZE = 96.0  # (x + y)
cdef const double CLASSIFICATION_BULLET_MAX_SIZE = 32  # (x + y)
cdef const double CLASSIFICATION_ORBITAL_MIN_ALTITUDE = -32_768.0  # (inverted cuz pygame)
cdef const double CLASSIFICATION_ORBITAL_MIN_SPEED = 8192.0
cdef const double CLASSIFICATION_ORBITAL_MAX_ALT_VEL = 256.0
cdef const double CLASSIFICATION_BALLISTIC_MISSILE_MIN_ALTITUDE = -2048.0
cdef const double CLASSIFICATION_ARTILLERY_MIN_SPEED = 1400.0
cdef const double CLASSIFICATION_HOVER_MAX_SPEED = 512.0


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
        self.track_classification = TrackClassification()
        self._track_state = TrackState.NEW.value
        self._track_quality = TrackQuality.NONE.value
        self.last_update = 0
        self.sx = 0
        self.sy = 0
        self.vel = Vec2()
        self.acc = Vec2()

    cpdef increment_time(self, double dt):
        self.last_update += dt
        self.predict(dt)

    cpdef reset(self):
        pass

    cpdef set_size(self, double x, double y):
        self.sx = x
        self.sy = y

    cpdef initialize(self, double x, double y, double vx, double vy, double g):
        self._track_quality = TrackQuality.POS_ONLY.value
        self.last_update = 0
        self.g = g

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

    cdef inline update_classification(self):
        cdef:
            double r, ax2, px2
            double abs_vel

            Vec2 own_accel
            Vec2 axial_accel
            Vec2 perp_accel

        # print(self.acc.xy, self.vel.xy)

        # surface (tracks where ay ~= 0.)
        if -CLASSIFICATION_TOLERANCE < self.acc.y < CLASSIFICATION_TOLERANCE:
            self.track_classification.powered = self.acc.x > CLASSIFICATION_THRUST_TOLERANCE
            self.track_classification.motion = motion_track_type.MOTION_SURFACE

            # type classification
            if -CLASSIFICATION_TOLERANCE < self.acc.x < CLASSIFICATION_TOLERANCE:
                self.track_classification.type = surface_track_class.STATIC

            elif self.sx + self.sy > CLASSIFICATION_VEHICLE_MINSIZE:
                self.track_classification.type = surface_track_class.VEHICLE

            else:
                self.track_classification.type = surface_track_class.PERSON

            # print(self.track_classification.motion, self.track_classification.type)
            return

        # calculate own acceleration (no gravity)
        own_acceleration = self.acc - Vec2().from_cartesian(0, self.g)
        abs_vel = self.vel.get_length()

        # split acceleration into axial and perpendicular
        axial_accel, perp_accel = own_acceleration.split_vector(self.vel)
        ax2 = axial_accel.x*axial_accel.x + axial_accel.y*axial_accel.y
        px2 = perp_accel.x*perp_accel.x + perp_accel.y*perp_accel.y

        r = px2 / (ax2 + px2 + 1e-12)

        self.track_classification.powered = (
            sqrt(ax2) >= CLASSIFICATION_THRUST_TOLERANCE
        )
        # print(sqrt(ax2), self.track_classification.powered)

        # print(own_acceleration.xy, axial_accel.xy, perp_accel.xy, r)

        # ballistic (tracks where a ~= gravity + lateral acceleration)
        # orbital (very fast tracks where altitude is high)
        if (
            self.y < CLASSIFICATION_ORBITAL_MIN_ALTITUDE  # inverted cuz pygame
            and abs_vel >= CLASSIFICATION_ORBITAL_MIN_SPEED
        ):
            self.track_classification.motion = motion_track_type.MOTION_ORBITAL

            # type classification
            if (
                -CLASSIFICATION_ORBITAL_MAX_ALT_VEL
                <= self.vel.y
                <= CLASSIFICATION_ORBITAL_MAX_ALT_VEL
            ):  # altitude stays almost the same
                if self.sx + self.sy > CLASSIFICATION_VEHICLE_MINSIZE:
                    self.track_classification.type = orbital_track_class.SATELLITE

                else:
                    self.track_classification.type = orbital_track_class.ORBITAL_WARHEAD

            else:  # altitude changes dramatically
                if r > CLASSIFICATION_MANEUVER_TOLERANCE:
                    self.track_classification.type = orbital_track_class.EXO_INTERCEPTOR

                else:
                    self.track_classification.type = orbital_track_class.ICBM

            return

        if r < CLASSIFICATION_MANEUVER_TOLERANCE:
            self.track_classification.motion = motion_track_type.MOTION_BALLISTIC

            # type classification
            if abs_vel >= CLASSIFICATION_ARTILLERY_MIN_SPEED:
                if (
                    self.track_classification.powered
                    or self.y < CLASSIFICATION_BALLISTIC_MISSILE_MIN_ALTITUDE
                ):
                    self.track_classification.type = ballistic_track_class.BALLISTIC_MISSILE

                else:
                    if self.sx + self.sy <= CLASSIFICATION_BULLET_MAX_SIZE:
                        self.track_classification.type = ballistic_track_class.BULLET

                    else:
                        self.track_classification.type = ballistic_track_class.ARTILLERY

                return

            elif (
                not self.track_classification.powered
                and self.sx + self.sy <= CLASSIFICATION_MUNITION_MAX_SIZE
            ):
                if self.sx + self.sy <= CLASSIFICATION_BULLET_MAX_SIZE:
                    self.track_classification.type = ballistic_track_class.BULLET

                else:
                    self.track_classification.type = ballistic_track_class.MORTAR

                return

        # maneuvering (tracks capable of sustained turning)
        if r >= CLASSIFICATION_MANEUVER_TOLERANCE:
            self.track_classification.motion = motion_track_type.MOTION_MANEUVERING

            # type classification
            if abs_vel <= CLASSIFICATION_HOVER_MAX_SPEED:  # slow targets
                if self.sx + self.sy > CLASSIFICATION_VEHICLE_MINSIZE:
                    self.track_classification.type = maneuvering_track_class.HELICOPTER

                else:
                    self.track_classification.type = maneuvering_track_class.DRONE

            else:  # fast targets
                if self.track_classification.powered:
                    if self.sx + self.sy > CLASSIFICATION_VEHICLE_MINSIZE:
                        self.track_classification.type = maneuvering_track_class.AIRCRAFT

                    else:
                        self.track_classification.type = maneuvering_track_class.CRUISE_MISSILE

                else:
                    self.track_classification.type = maneuvering_track_class.GLIDE_VEHICLE

            return

        # unknown (tracks that don't fit in any other group)
        self.track_classification.motion = motion_track_type.MOTION_UNKNOWN

        # type classification
        if self.sx + self.sy > CLASSIFICATION_MUNITION_MAX_SIZE:
            if abs_vel >= CLASSIFICATION_ARTILLERY_MIN_SPEED:
                self.track_classification.type = unknown_track_class.BIG_FAST

            else:
                self.track_classification.type = unknown_track_class.BIG_SLOW

        else:
            if abs_vel >= CLASSIFICATION_ARTILLERY_MIN_SPEED:
                self.track_classification.type = unknown_track_class.SMALL_FAST

            else:
                self.track_classification.type = unknown_track_class.SMALL_SLOW

        # print(self.track_classification.motion, self.track_classification.type)

    cpdef step(
        self,
        double mx, double my,
        double mvx, double mvy,
        double dt
    ):
        self.update(mx, my, mvx, mvy, dt)
        self.update_classification()

    cpdef Vec2 get_position(self):
        return Vec2().from_cartesian(self.x, self.y)

    cpdef Vec2 get_velocity(self):
        return self.vel.copy()

    cpdef Vec2 get_acceleration(self):
        return self.acc.copy()

    cpdef Vec2 predict_future_position(self, double t):
        """
        Predict target position t seconds into future.
        """

        cdef double t2 = 0.5 * t * t

        return Vec2().from_cartesian(
            self.x + self.vel.x * t + self.acc.x * t2,
            self.y + self.vel.y * t + self.acc.y * t2
        )

    cpdef double get_speed(self):
        return sqrt(self.vel.x * self.vel.x + self.vy * self.vy)

    cpdef kill(self):
        self._track_state = TrackState.DEAD.value
