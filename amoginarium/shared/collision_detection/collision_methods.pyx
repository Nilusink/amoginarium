# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libcpp.vector cimport vector

cdef inline double c_max(double a, double b) noexcept: return a if a > b else b
cdef inline double c_min(double a, double b) noexcept: return a if a < b else b

cdef inline void project_poly(const vector[double]& vx, const vector[double]& vy, double nx, double ny,
                              double * out_min, double * out_max) noexcept:
    cdef const double * vx_ptr = vx.data()
    cdef const double * vy_ptr = vy.data()
    cdef size_t sz = vx.size()
    cdef double min_p = vx_ptr[0] * nx + vy_ptr[0] * ny
    cdef double max_p = min_p
    cdef double p
    cdef size_t i
    for i in range(1, sz):
        p = vx_ptr[i] * nx + vy_ptr[i] * ny
        if p < min_p:
            min_p = p
        elif p > max_p:
            max_p = p
    out_min[0] = min_p
    out_max[0] = max_p

cdef bint aabb_aabb_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx, double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_sx, double b_sy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x = (a_px_n - a_px_o) - (b_px_n - b_px_o)
    cdef double v_rel_y = (a_py_n - a_py_o) - (b_py_n - b_py_o)

    cdef double a_min_x = c_min(a_px_o, a_px_n)
    cdef double a_max_x = c_max(a_px_o + a_sx, a_px_n + a_sx)
    cdef double b_min_x = c_min(b_px_o, b_px_n)
    cdef double b_max_x = c_max(b_px_o + b_sx, b_px_n + b_sx)
    cdef double swept_overlap_x = c_min(a_max_x, b_max_x) - c_max(a_min_x, b_min_x)

    cdef double a_min_y = c_min(a_py_o, a_py_n)
    cdef double a_max_y = c_max(a_py_o + a_sy, a_py_n + a_sy)
    cdef double b_min_y = c_min(b_py_o, b_py_n)
    cdef double b_max_y = c_max(b_py_o + b_sy, b_py_n + b_sy)
    cdef double swept_overlap_y = c_min(a_max_y, b_max_y) - c_max(a_min_y, b_min_y)

    if not is_active:
        if swept_overlap_x <= 1e-4 or swept_overlap_y <= 1e-4:
            return False
    else:
        if swept_overlap_x < -1e-4 or swept_overlap_y < -1e-4:
            return False

    cdef double min_x = b_px_o - a_sx
    cdef double max_x = b_px_o + b_sx
    cdef double min_y = b_py_o - a_sy
    cdef double max_y = b_py_o + b_sy

    cdef double t_near_x = -1e300, t_far_x = 1e300
    cdef double t_near_y = -1e300, t_far_y = 1e300
    cdef double t_hit_near, t_hit_far
    cdef double dist_left, dist_right, dist_top, dist_bottom, min_dist_x, min_dist_y

    if min_x > max_x or min_y > max_y:
        return False

    if v_rel_x != 0.0:
        t_near_x = (min_x - a_px_o) / v_rel_x
        t_far_x = (max_x - a_px_o) / v_rel_x
        if t_near_x > t_far_x: t_near_x, t_far_x = t_far_x, t_near_x
    else:
        if not (min_x <= a_px_o <= max_x): return False

    if v_rel_y != 0.0:
        t_near_y = (min_y - a_py_o) / v_rel_y
        t_far_y = (max_y - a_py_o) / v_rel_y
        if t_near_y > t_far_y: t_near_y, t_far_y = t_far_y, t_near_y
    else:
        if not (min_y <= a_py_o <= max_y): return False

    t_hit_near = c_max(t_near_x, t_near_y)
    t_hit_far = c_min(t_far_x, t_far_y)

    if t_hit_near > t_hit_far or t_hit_far <= 0.0 or t_hit_near >= 1.0:
        return False

    if t_hit_near <= 0.0:
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
        if t_near_x > t_near_y:
            out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
            out_norm_y[0] = 0.0
        elif t_near_y > t_near_x:
            out_norm_x[0] = 0.0
            out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0
        else:
            out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
            out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0:
        return False

    out_t[0] = c_max(0.0, t_hit_near)
    return True

cdef bint swept_sat_generic(
        const vector[double]& a_vx_o, const vector[double]& a_vy_o, const vector[double]& a_vx_n,
        const vector[double]& a_vy_n, const vector[double]& a_ax, const vector[double]& a_ay, double a_dx, double a_dy,
        const vector[double]& b_vx_o, const vector[double]& b_vy_o, const vector[double]& b_vx_n,
        const vector[double]& b_vy_n, const vector[double]& b_ax, const vector[double]& b_ay, double b_dx, double b_dy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x = a_dx - b_dx
    cdef double v_rel_y = a_dy - b_dy

    cdef double t_enter = -1e300
    cdef double t_exit = 1e300
    cdef double best_nx = 0.0
    cdef double best_ny = 0.0

    cdef double min_overlap = 1e300
    cdef double overlap, mtv_nx = 0.0, mtv_ny = 0.0

    cdef size_t i
    cdef double nx, ny, minA_o, maxA_o, minB_o, maxB_o, minA_n, maxA_n, minB_n, maxB_n
    cdef double a_min_sw, a_max_sw, b_min_sw, b_max_sw, swept_overlap, v_proj, t0, t1, inv_v

    for i in range(a_ax.size()):
        nx = a_ax[i]
        ny = a_ay[i]

        project_poly(a_vx_o, a_vy_o, nx, ny, &minA_o, &maxA_o)
        project_poly(a_vx_n, a_vy_n, nx, ny, &minA_n, &maxA_n)
        project_poly(b_vx_o, b_vy_o, nx, ny, &minB_o, &maxB_o)
        project_poly(b_vx_n, b_vy_n, nx, ny, &minB_n, &maxB_n)

        # Swept overlap test
        a_min_sw = c_min(minA_o, minA_n)
        a_max_sw = c_max(maxA_o, maxA_n)
        b_min_sw = c_min(minB_o, minB_n)
        b_max_sw = c_max(maxB_o, maxB_n)
        swept_overlap = c_min(a_max_sw, b_max_sw) - c_max(a_min_sw, b_min_sw)

        if not is_active:
            if swept_overlap <= 1e-4: return False
        else:
            if swept_overlap < -1e-4: return False

        overlap = (maxB_o - minA_o) if (maxB_o - minA_o) < (maxA_o - minB_o) else (maxA_o - minB_o)
        if overlap < min_overlap:
            min_overlap = overlap
            if (maxA_o + minA_o) > (maxB_o + minB_o):
                mtv_nx = nx
                mtv_ny = ny
            else:
                mtv_nx = -nx
                mtv_ny = -ny

        v_proj = v_rel_x * nx + v_rel_y * ny
        if v_proj == 0.0:
            if minA_o >= maxB_o or maxA_o <= minB_o: return False
        else:
            inv_v = 1.0 / v_proj
            t0 = (minB_o - maxA_o) * inv_v
            t1 = (maxB_o - minA_o) * inv_v
            if inv_v < 0.0: t0, t1 = t1, t0
            if t0 > t_enter:
                t_enter = t0
                best_nx = -nx if v_proj > 0 else nx
                best_ny = -ny if v_proj > 0 else ny
            if t1 < t_exit: t_exit = t1
            if t_enter > t_exit: return False

    for i in range(b_ax.size()):
        nx = b_ax[i]
        ny = b_ay[i]

        project_poly(a_vx_o, a_vy_o, nx, ny, &minA_o, &maxA_o)
        project_poly(a_vx_n, a_vy_n, nx, ny, &minA_n, &maxA_n)
        project_poly(b_vx_o, b_vy_o, nx, ny, &minB_o, &maxB_o)
        project_poly(b_vx_n, b_vy_n, nx, ny, &minB_n, &maxB_n)

        # Swept overlap test
        a_min_sw = c_min(minA_o, minA_n)
        a_max_sw = c_max(maxA_o, maxA_n)
        b_min_sw = c_min(minB_o, minB_n)
        b_max_sw = c_max(maxB_o, maxB_n)
        swept_overlap = c_min(a_max_sw, b_max_sw) - c_max(a_min_sw, b_min_sw)

        if not is_active:
            if swept_overlap <= 1e-4: return False
        else:
            if swept_overlap < -1e-4: return False

        overlap = (maxB_o - minA_o) if (maxB_o - minA_o) < (maxA_o - minB_o) else (maxA_o - minB_o)
        if overlap < min_overlap:
            min_overlap = overlap
            if (maxA_o + minA_o) > (maxB_o + minB_o):
                mtv_nx = nx
                mtv_ny = ny
            else:
                mtv_nx = -nx
                mtv_ny = -ny

        v_proj = v_rel_x * nx + v_rel_y * ny
        if v_proj == 0.0:
            if minA_o >= maxB_o or maxA_o <= minB_o: return False
        else:
            inv_v = 1.0 / v_proj
            t0 = (minB_o - maxA_o) * inv_v
            t1 = (maxB_o - minA_o) * inv_v
            if inv_v < 0.0: t0, t1 = t1, t0
            if t0 > t_enter:
                t_enter = t0
                best_nx = -nx if v_proj > 0 else nx
                best_ny = -ny if v_proj > 0 else ny
            if t1 < t_exit: t_exit = t1
            if t_enter > t_exit: return False

    if t_enter >= 1.0 or t_exit <= 0.0: return False

    if t_enter <= 0.0:
        out_norm_x[0] = mtv_nx
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    out_t[0] = c_max(0.0, t_enter)
    return True