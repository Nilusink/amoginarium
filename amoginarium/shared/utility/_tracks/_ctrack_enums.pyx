"""
Cython stuff for track enums.

| ``Path``: amoginarium/shared/utility/_tracks/_ctrack_enums.pyx
| ``Project``: amoginarium
| ``Created``: 25.05.2026
| ``Authors``: Nilusink
"""

from enum import Enum


# fmt: off
# region track types
class MotionTrackType(Enum):
    """Motion track types."""

    MOTION_BALLISTIC = motion_track_type.MOTION_BALLISTIC
    MOTION_MANEUVERING = motion_track_type.MOTION_MANEUVERING
    MOTION_ORBITAL = motion_track_type.MOTION_ORBITAL
    MOTION_SURFACE = motion_track_type.MOTION_SURFACE
    MOTION_UNKNOWN = motion_track_type.MOTION_UNKNOWN


class BallisticTrackClass(Enum):
    """
    Ballistic track class.

    Includes tracks where a ~= gravity.
    """

    BALLISTIC_MISSILE = ballistic_track_class.BALLISTIC_MISSILE  # high altitude
    ARTILLERY = ballistic_track_class.ARTILLERY                  # large, fast munitions
    MORTAR = ballistic_track_class.MORTAR                        # slow, high arc
    BULLET = ballistic_track_class.BULLET                        # small
    BOMB = ballistic_track_class.BOMB                            # similar to mortar but dropped


class ManeuveringTrackClass(Enum):
    """
    Maneuvering track class.

    Includes tracks capable of sustained turning.
    """

    AIRCRAFT = maneuvering_track_class.AIRCRAFT              # large, thrust + maneuver
    CRUISE_MISSILE = maneuvering_track_class.CRUISE_MISSILE  # small, thrust + maneuver
    GLIDE_VEHICLE = maneuvering_track_class.GLIDE_VEHICLE    # small, no thrust, maneuver
    DRONE = maneuvering_track_class.DRONE                    # small, hover
    HELICOPTER = maneuvering_track_class.HELICOPTER          # large, hover


class OrbitalTrackClass(Enum):
    """
    Orbital track class.

    Includes very fast tracks where altitude is high.
    """

    ICBM = orbital_track_class.ICBM                        # small, fast altitude changes, ballistic
    EXO_INTERCEPTOR = orbital_track_class.EXO_INTERCEPTOR  # small, fast altitude changes, maneuvering
    SATELLITE = orbital_track_class.SATELLITE              # large, altitude stays similar
    ORBITAL_WARHEAD = orbital_track_class.ORBITAL_WARHEAD  # small, altitude stays similar


class SurfaceTrackClass(Enum):
    """
    Surface track class.

    Includes tracks where ay ~= 0.
    """

    STATIC = surface_track_class.STATIC    # a == 0
    VEHICLE = surface_track_class.VEHICLE  # big, moving
    PERSON = surface_track_class.PERSON    # small, moving


class UnknownTrackClass(Enum):
    """
    Unknown track class.

    Includes tracks that don't fit in any other group.
    """

    UNKNOWN = unknown_track_class.UNKNOWN
    SMALL_FAST = unknown_track_class.SMALL_FAST
    BIG_FAST = unknown_track_class.BIG_FAST
    SMALL_SLOW = unknown_track_class.SMALL_SLOW
    BIG_SLOW = unknown_track_class.BIG_SLOW

# endregion
# fmt: on


cdef class TrackClassification:
    def __cinit__(
        self,
        *,
        motion: int | None = None,
        track_type: int | None = None,
        powered: bool | None = None
    ) -> None:
        if motion:
            self.motion = motion

        if track_type:
            self.type = track_type

        if powered:
            self.powered = powered

    def __cinit__(self):
        self.motion = motion_track_type.MOTION_UNKNOWN
        self.type = UNKNOWN = unknown_track_class.UNKNOWN
        self.powered = False

    def get_motion_enum(self) -> MotionTrackType:
        return MotionTrackType(self.motion)

    def get_type_enum(self):
        if self.motion == motion_track_type.MOTION_BALLISTIC:
            return BallisticTrackClass(self.type)

        elif self.motion == motion_track_type.MOTION_SURFACE:
            return SurfaceTrackClass(self.type)

        elif self.motion == motion_track_type.MOTION_MANEUVERING:
            return ManeuveringTrackClass(self.type)

        elif self.motion == motion_track_type.MOTION_ORBITAL:
            return OrbitalTrackClass(self.type)

        elif self.motion == motion_track_type.MOTION_UNKNOWN:
            return UnknownTrackClass(self.type)

        return UnknownTrackClass.UNKNOWN

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}: "
            f"{self.get_motion_enum().name}, "
            f"{self.get_type_enum().name}>"
        )
