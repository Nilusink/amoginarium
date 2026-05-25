"""
Cython stuff for track enums.

| ``Path``: amoginarium/shared/utility/_tracks/_ctrack_enums.pyd
| ``Project``: amoginarium
| ``Created``: 25.05.2026
| ``Authors``: Nilusink
"""

ctypedef unsigned char motion_t
ctypedef unsigned char type_t
ctypedef bint powered_t


cdef enum motion_track_type:
    MOTION_BALLISTIC = 0
    MOTION_MANEUVERING = 10
    MOTION_ORBITAL = 20
    MOTION_SURFACE = 30
    MOTION_UNKNOWN = 40


# fmt: off
# region track types
cdef enum ballistic_track_class:
    BALLISTIC_MISSILE = 0  # fast, high altitude OR powered
    ARTILLERY = 1          # fast munitions
    MORTAR = 2             # slow, high arc, unpowered
    BULLET = 3             # unpowered, small
    BOMB = 4               # similar to mortar but dropped (currently not implemented)


cdef enum maneuvering_track_class:
    AIRCRAFT = 10        # large, fast, thrust + maneuver
    CRUISE_MISSILE = 11  # small, fast, thrust + maneuver
    GLIDE_VEHICLE = 12   # small, fast, no thrust, maneuver
    DRONE = 13           # small, hover-ish
    HELICOPTER = 14      # large, hover-ish


cdef enum orbital_track_class:
    ICBM = 20             # small, fast altitude changes, ballistic
    EXO_INTERCEPTOR = 21  # small, fast altitude changes, maneuvering
    SATELLITE = 22        # large, altitude stays similar
    ORBITAL_WARHEAD = 23  # small, altitude stays similar


cdef enum surface_track_class:
    STATIC = 30   # a == 0
    VEHICLE = 31  # big, moving
    PERSON = 32   # small, moving


cdef enum unknown_track_class:
    UNKNOWN = 40
    SMALL_FAST = 41
    BIG_FAST = 42
    SMALL_SLOW = 43
    BIG_SLOW = 44

# endregion
# fmt: on

cdef class TrackClassification:
    cdef public motion_t motion
    cdef public type_t type
    cdef public powered_t powered
