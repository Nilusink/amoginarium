# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

cdef inline double c_max(double a, double b) noexcept: return a if a > b else b
cdef inline double c_min(double a, double b) noexcept: return a if a < b else b

cdef inline bint aabb_aabb_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx, double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_sx, double b_sy,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x = (a_px_n - a_px_o) - (b_px_n - b_px_o)
    cdef double v_rel_y = (a_py_n - a_py_o) - (b_py_n - b_py_o)

    # NO PIXEL HACKS: Exact, mathematically flush boundary detection
    cdef double min_x = b_px_o - a_sx
    cdef double max_x = b_px_o + b_sx
    cdef double min_y = b_py_o - a_sy
    cdef double max_y = b_py_o + b_sy

    cdef double t_near_x = -1e300, t_far_x = 1e300
    if v_rel_x != 0.0:
        t_near_x = (min_x - a_px_o) / v_rel_x
        t_far_x = (max_x - a_px_o) / v_rel_x
        if t_near_x > t_far_x: t_near_x, t_far_x = t_far_x, t_near_x
    elif not (min_x <= a_px_o <= max_x):
        return False

    cdef double t_near_y = -1e300, t_far_y = 1e300
    if v_rel_y != 0.0:
        t_near_y = (min_y - a_py_o) / v_rel_y
        t_far_y = (max_y - a_py_o) / v_rel_y
        if t_near_y > t_far_y: t_near_y, t_far_y = t_far_y, t_near_y
    elif not (min_y <= a_py_o <= max_y):
        return False

    cdef double t_hit_near = c_max(t_near_x, t_near_y)
    cdef double t_hit_far = c_min(t_far_x, t_far_y)

    if t_hit_near > t_hit_far or t_hit_far <= 0.0 or t_hit_near >= 1.0:
        return False

    # Normal Calculation
    if t_hit_near <= 0.0:
        # Resting Contact: We are perfectly flush or overlapping. Find shortest distance.
        dist_left = a_px_o - min_x
        dist_right = max_x - a_px_o
        dist_top = a_py_o - min_y
        dist_bottom = max_y - a_py_o

        min_dist_x = dist_left if dist_left < dist_right else dist_right
        min_dist_y = dist_top if dist_top < dist_bottom else dist_bottom

        if min_dist_x < min_dist_y:
            out_norm_x[0] = -1.0 if dist_left < dist_right else 1.0
            out_norm_y[0] = 0.0
        else:
            out_norm_x[0] = 0.0
            out_norm_y[0] = -1.0 if dist_top < dist_bottom else 1.0
    else:
        # Dynamic Impact
        if t_near_x > t_near_y:
            out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
            out_norm_y[0] = 0.0
        elif t_near_y > t_near_x:
            out_norm_x[0] = 0.0
            out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0
        else:
            out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
            out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0

    # STRICT Separation Rejection: strictly > 0 means moving AWAY.
    # If == 0, it allows continuous resting contact!
    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0:
        return False

    out_t[0] = c_max(0.0, t_hit_near)
    return True