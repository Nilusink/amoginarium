# fast_vec2.pyx
"""
Vec2 class and vec2 related functions.

| ``Path``: amoginarium/shared/utility/_cvectors.pyx
| ``Project``: amoginarium
| ``Created``: 11.03.2026
| ``Authors``: Nilusink
"""

cimport cython
from libc.math cimport atan2, cos, fmod, pi, sin, sqrt
from struct import pack, unpack


cdef class Vec2:
    def __cinit__(self, double x=0, double y=0):
        self.x = x
        self.y = y

    # Vector length
    @property
    def xy(self):
        return self.x, self.y

    @xy.setter
    def xy(self, value):
        self.x = value[0]
        self.y = value[1]

    @property
    def angle(self) -> float:
        return self.get_angle()

    @angle.setter
    def angle(self, value: float) -> None:
        self.set_angle(value)

    @property
    def length(self) -> float:
        return self.get_length()

    @length.setter
    def length(self, value: float) -> None:
        self.set_length(value)

    @property
    def polar(self):
        return self.get_polar()

    @polar.setter
    def polar(self, value):
        self.set_polar(value[0], value[1])

    cpdef double get_length(self):
        return sqrt(self.x * self.x + self.y * self.y)

    cpdef double get_angle(self):
        return atan2(self.y, self.x)

    cpdef tuple get_polar(self):
        return (
            atan2(self.y, self.x),
            sqrt(self.x * self.x + self.y * self.y)
        )

    cpdef set_length(self, double length):
        cdef double a = self.get_angle()
        self.x = cos(a) * length
        self.y = sin(a) * length

    cpdef set_angle(self, double angle):
        cdef double l = self.get_length()
        self.x = cos(angle) * l
        self.y = sin(angle) * l

    cpdef set_polar(self, double angle, double length):
        self.x = cos(angle) * length
        self.y = sin(angle) * length

    # maths
    cpdef double dot(self, Vec2 other):
        return self.x * other.x + self.y * other.y

    cpdef copy(self):
        cdef Vec2 v = Vec2()
        v.x = self.x
        v.y = self.y
        return v

    cpdef tuple split_vector(self, Vec2 direction):
        cdef double inv_len = 1.0 / sqrt(direction.x*direction.x + direction.y*direction.y)
        cdef double dx = direction.x * inv_len
        cdef double dy = direction.y * inv_len

        cdef double dot = self.x * dx + self.y * dy

        # parallel component
        cdef Vec2 facing = Vec2(dot * dx, dot * dy)

        # perpendicular component
        cdef Vec2 other = Vec2(self.x - facing.x, self.y - facing.y)

        return facing, other

    cpdef object normalize(self):
        self.set_length(1)
        return self

    cpdef Vec2 mirror(self, Vec2 mirror_by):
        cdef double inv_len = 1.0 / sqrt(
            mirror_by.x*mirror_by.x + mirror_by.y*mirror_by.y
        )
        cdef double nx = mirror_by.x * inv_len
        cdef double ny = mirror_by.y * inv_len

        cdef double dot = self.x * nx + self.y * ny

        return Vec2(
            2.0 * dot * nx - self.x,
            2.0 * dot * ny - self.y
        )

    cpdef object rotate_by(self, object angle):
        if isinstance(angle, Vec2):
            return self.rotate_by_vec2(angle)

        return self.rotate_by_angle(angle)

    cdef inline object rotate_by_angle(self, double angle):
        return Vec2().from_polar(self.angle + angle, self.length)

    cdef inline Vec2 rotate_by_vec2(Vec2 self, Vec2 other):
        cdef double inv_len = 1.0 / sqrt(other.x*other.x + other.y*other.y)

        cdef double ox = other.x * inv_len
        cdef double oy = other.y * inv_len

        return Vec2().from_cartesian(
            self.x * ox - self.y * oy,
            self.x * oy + self.y * ox
        )

    # magic stuff
    cdef inline Vec2 add_vec2(self, Vec2 other):
        return Vec2().from_cartesian(self.x + other.x, self.y + other.y)

    cdef inline Vec2 add_double(self, double other):
        return Vec2().from_cartesian(self.x + other, self.y + other)

    def __add__(self, other):
        if hasattr(other, "y"):
            return self.add_vec2(other)

        else:
            return self.add_double(other)

    cdef inline Vec2 sub_vec2(self, Vec2 other):
        return Vec2().from_cartesian(self.x - other.x, self.y - other.y)

    cdef inline Vec2 sub_double(self, double other):
        return Vec2().from_cartesian(self.x - other, self.y - other)

    def __sub__(self, other):
        if hasattr(other, "y"):
            return self.sub_vec2(other)

        else:
            return self.sub_double(other)

    cdef inline Vec2 mul_vec2(self, Vec2 other):
        return Vec2().from_polar(
            self.get_angle() * other.get_angle(),
            self.get_length() * other.get_length()
        )

    cdef inline Vec2 mul_double(self, double other):
        return Vec2().from_cartesian(self.x * other, self.y * other)

    def __mul__(self, other):
        if hasattr(other, "y"):
            return self.mul_vec2(other)

        else:
            return self.mul_double(other)

    cdef inline Vec2 div(self, double other):
        return Vec2().from_cartesian(self.x / other, self.y / other)

    def __truediv__(self, double other):
        return self.div(other)

    def __abs__(self):
        return self.get_length()

    def __reduce__(self):
        return Vec2, (self.x, self.y)

    def __repr__(self) -> str:
        return f"<Vec2; {self.x}, {self.y}>"

    def __bytes__(self) -> bytes:
        return pack("<dd", self.x, self.y)

    # constructors
    cpdef object from_cartesian(self, double x, double y):
        v = self
        v.x = x
        v.y = y
    
        return v

    cpdef object from_polar(self, double angle, double length):
        v = self
        v.set_polar(angle, length)
    
        return v

    cpdef object from_bytes(self, object b):
        self.x, self.y = unpack("<dd", b)
        return self


cpdef double normalize_angle(double value):
    cdef double a = value
    cdef double b = pi * 2

    cdef double r = fmod(a, b)
    if r < 0:
        r += b
    return r


cpdef double normalize_angle_neg(double value):
    return normalize_angle(value + pi) - pi


cpdef double clamp_angle(double angle, double center, double max_delta):
    diff = normalize_angle_neg(angle - center)

    diff = max(-max_delta, min(max_delta, diff))

    return normalize_angle(center + diff)


cpdef double max_angle(double center, double[:] angles):
    cdef:
        Py_ssize_t i
        double best = angles[0]

    for i in range(1, angles.shape[0]):
        if abs(angles[i] - center) > abs(best - center):
            best = angles[i]

    return best


cpdef double min_angle(double center, double[:] angles):
    cdef:
        Py_ssize_t i
        double best = angles[0]

    for i in range(1, angles.shape[0]):
        if abs(angles[i] - center) < abs(best - center):
            best = angles[i]

    return best
