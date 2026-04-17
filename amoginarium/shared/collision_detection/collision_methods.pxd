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

    # THE FIX: "Skin Radius" Epsilon
    # We shrink the target area by 0.001 pixels.
    # If objects are perfectly flush (0 distance), they will mathematically MISS.
    # They MUST actively overlap to trigger a hit.
    cdef double epsilon = 0.001
    cdef double min_x = (b_px_o - a_sx) + epsilon
    cdef double max_x = (b_px_o + b_sx) - epsilon
    cdef double min_y = (b_py_o - a_sy) + epsilon
    cdef double max_y = (b_py_o + b_sy) - epsilon

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

    if t_hit_near > t_hit_far or t_hit_far < 0.0 or t_hit_near >= 1.0:
        return False

    # Calculate Normal vector
    if t_near_x > t_near_y:
        out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
        out_norm_y[0] = 0.0
    elif t_near_y > t_near_x:
        out_norm_x[0] = 0.0
        out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0
    else:
        out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
        out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0

    # Separating Velocity Rejection
    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) >= 0.0:
        return False

    out_t[0] = c_max(0.0, t_hit_near)
    return True