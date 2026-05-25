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

    cpdef object normalize(self)

    cpdef Vec2 mirror(self, Vec2 mirror_by)

    cpdef object rotate_by(self, object angle)

    cdef inline object rotate_by_angle(self, double angle)

    cdef inline Vec2 rotate_by_vec2(self, Vec2 other)

    # magic stuff
    cdef inline Vec2 add_vec2(self, Vec2 other)

    cdef inline Vec2 add_double(self, double other)

    cdef inline Vec2 sub_vec2(self, Vec2 other)

    cdef inline Vec2 sub_double(self, double other)

    cdef inline Vec2 mul_vec2(self, Vec2 other)

    cdef inline Vec2 mul_double(self, double other)

    cdef inline Vec2 div(self, double other)

    # constructors
    cpdef object from_cartesian(self, double x, double y)

    cpdef object from_polar(self, double angle, double length)


cpdef double normalize_angle(double value)


cpdef double normalize_angle_neg(double value)


cpdef double clamp_angle(double angle, double center, double max_delta)


cpdef double max_angle(double center, double[:] angles)


cpdef double min_angle(double center, double[:] angles)