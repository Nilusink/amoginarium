# fast_vec2.pyx
cimport cython
from libc.math cimport sqrt, atan2, cos, sin, pi, fmod


cdef class Vec2:
    def __cinit__(self):
        self.x = 0.0
        self.y = 0.0

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
        a = (direction.get_angle() - self.get_angle())
        facing = self.from_polar(
            angle=direction.get_angle(),
            length=self.get_length() * cos(a)
        )
        other = self.from_polar(
            angle=direction.get_angle() - pi / 2,
            length=self.get_length() * sin(a)
        )

        return facing, other

    cpdef Vec2 normalize(self):
        self.set_length(1)
        return self

    cpdef Vec2 mirror(self, Vec2 mirror_by):
        mirror_by = mirror_by.copy().normalize()
        ang_d = mirror_by.get_angle() - self.get_angle()
        self.set_angle(mirror_by.get_angle() + 2 * ang_d)
        return self

    # magic stuff
    cdef Vec2 add_vec2(self, Vec2 other):
        return self.from_cartesian(self.x + other.x, self.y + other.y)

    cdef Vec2 add_double(self, double other):
        return self.from_cartesian(self.x + other, self.y + other)

    def __add__(self, other):
        if hasattr(other, "y"):
            return self.add_vec2(other)

        else:
            return self.add_double(other)

    cdef Vec2 sub_vec2(self, Vec2 other):
        return self.from_cartesian(self.x - other.x, self.y - other.y)

    cdef Vec2 sub_double(self, double other):
        return self.from_cartesian(self.x - other, self.y - other)

    def __sub__(self, other):
        if hasattr(other, "y"):
            return self.sub_vec2(other)

        else:
            return self.sub_double(other)

    cdef Vec2 mul_vec2(self, Vec2 other):
        return self.from_polar(
            self.get_angle() * other.get_angle(),
            self.get_length() * other.get_length()
        )

    cdef Vec2 mul_double(self, double other):
        return self.from_cartesian(self.x * other, self.y * other)

    def __mul__(self, other):
        if hasattr(other, "y"):
            return self.mul_vec2(other)

        else:
            return self.mul_double(other)

    cdef Vec2 div(self, double other):
        return self.from_cartesian(self.x / other, self.y / other)

    def __truediv__(self, double other):
        return self.div(other)

    def __abs__(self):
        return self.get_length()

    def __repr__(self) -> str:
        return f"<Vec2; {self.x}, {self.y}>"


    # constructors
    cpdef Vec2 from_cartesian(self, double x, double y):
        v = Vec2()
        v.x = x
        v.y = y
    
        return v

    cpdef Vec2 from_polar(self, double angle, double length):
        v = Vec2()
        v.set_polar(angle, length)
    
        return v

cpdef double normalize_angle(double value):
    cdef double a = value
    cdef double b = pi * 2

    cdef double r = fmod(a, b)
    if r < 0:
        r += b
    return r
