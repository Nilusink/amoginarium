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
    cpdef double dot(self, object other)

    cpdef copy(self)

    cpdef tuple split_vector(self, object direction)

    cpdef object normalize(self)

    cpdef object mirror(self, object mirror_by)

    cpdef object rotate_by(self, object other)

    # magic stuff
    cdef object add_vec2(self, object other)

    cdef object add_double(self, double other)

    cdef object sub_vec2(self, object other)

    cdef object sub_double(self, double other)

    cdef object mul_vec2(self, object other)

    cdef object mul_double(self, double other)

    cdef object div(self, double other)

    # constructors
    cpdef object from_cartesian(self, double x, double y)

    cpdef object from_polar(self, double angle, double length)

cpdef double normalize_angle(double value)
