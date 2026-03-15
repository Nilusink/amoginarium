cdef class Vec2:
    cdef public double x
    cdef public double y

    cpdef double get_length(self)

    cpdef double get_angle(self)

    cpdef tuple get_polar(self)

    cpdef set_length(self, double length)

    cpdef set_angle(self, double angle)

    cpdef set_polar(self, double angle, double length)

    # maths
    cpdef double dot(self, Vec2 other)

    cpdef copy(self)

    cpdef tuple split_vector(self, Vec2 direction)

    cpdef Vec2 normalize(self)

    cpdef Vec2 mirror(self, Vec2 mirror_by)

    # magic stuff
    cdef Vec2 add_vec2(self, Vec2 other)

    cdef Vec2 add_double(self, double other)

    cdef Vec2 sub_vec2(self, Vec2 other)

    cdef Vec2 sub_double(self, double other)

    cdef Vec2 mul_vec2(self, Vec2 other)

    cdef Vec2 mul_double(self, double other)

    cdef Vec2 div(self, double other)

    # constructors
    cpdef Vec2 from_cartesian(self, double x, double y)

    cpdef Vec2 from_polar(self, double angle, double length)

cpdef double normalize_angle(double value)
