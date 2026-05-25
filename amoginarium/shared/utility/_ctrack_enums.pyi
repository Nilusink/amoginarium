"""
Cython stuff for track enums.

| ``Path``: amoginarium/shared/utility/_ctrack_enums.pyi
| ``Project``: amoginarium
| ``Created``: 25.05.2026
| ``Authors``: Nilusink
"""

from enum import Enum

class MotionTrackType(Enum):
    """Motion track types."""

class BallisticTrackClass(Enum):
    """
    Ballistic track class.

    Includes tracks where a ~= gravity.
    """

class ManeuveringTrackClass(Enum):
    """
    Maneuvering track class.

    Includes tracks capable of sustained turning.
    """

class OrbitalTrackClass(Enum):
    """
    Orbital track class.

    Includes very fast tracks where altitude is high.
    """

class SurfaceTrackClass(Enum):
    """
    Surface track class.

    Includes tracks where ay ~= 0.
    """

class UnknownTrackClass(Enum):
    """
    Unknown track class.

    Includes tracks that don't fit in any other group.
    """

type track_type_t = (  # noqa: PYI042
    BallisticTrackClass
    | ManeuveringTrackClass
    | OrbitalTrackClass
    | SurfaceTrackClass
    | UnknownTrackClass
)

class TrackClassification:
    def get_motion_enum(self) -> MotionTrackType:
        """Get a motion track type enum."""

    def get_type_enum(self) -> track_type_t:
        """Get a track type enum."""
