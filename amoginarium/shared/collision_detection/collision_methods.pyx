# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libcpp.vector cimport vector
from libc.math cimport sqrt

cdef inline double c_max(double a, double b) noexcept: return a if a > b else b
cdef inline double c_min(double a, double b) noexcept: return a if a < b else b

cdef inline void project_shape(int h_type, const vector[double]& vx, const vector[double]& vy, double radius, double nx,
                               double ny,
                               double * out_min, double * out_max) noexcept:
    cdef double min_p, max_p, p
    cdef size_t sz = vx.size()
    cdef size_t i

    if h_type == 5:
        p = vx[0] * nx + vy[0] * ny
        out_min[0] = p - radius
        out_max[0] = p + radius
    else:
        min_p = vx[0] * nx + vy[0] * ny
        max_p = min_p
        for i in range(1, sz):
            p = vx[i] * nx + vy[i] * ny
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
    cdef double v_rel_x, v_rel_y, min_x, max_x, min_y, max_y
    cdef double t_near_x, t_far_x, t_near_y, t_far_y, t_hit_near, t_hit_far
    cdef double dist_left, dist_right, dist_top, dist_bottom, min_dist_x, min_dist_y
    cdef double t_start, t_end, t_mid, a_mid_px, a_mid_py, b_mid_px, b_mid_py
    cdef double mid_overlap_x, mid_overlap_y, required_overlap

    v_rel_x = (a_px_n - a_px_o) - (b_px_n - b_px_o)
    v_rel_y = (a_py_n - a_py_o) - (b_py_n - b_py_o)

    min_x = b_px_o - a_sx
    max_x = b_px_o + b_sx
    min_y = b_py_o - a_sy
    max_y = b_py_o + b_sy

    t_near_x = -1e300
    t_far_x = 1e300
    t_near_y = -1e300
    t_far_y = 1e300

    if min_x > max_x + 1e-6 or min_y > max_y + 1e-6:
        return False

    if v_rel_x != 0.0:
        t_near_x = (min_x - a_px_o) / v_rel_x
        t_far_x = (max_x - a_px_o) / v_rel_x
        if t_near_x > t_far_x: t_near_x, t_far_x = t_far_x, t_near_x
    else:
        if a_px_o < min_x - 1e-6 or a_px_o > max_x + 1e-6: return False

    if v_rel_y != 0.0:
        t_near_y = (min_y - a_py_o) / v_rel_y
        t_far_y = (max_y - a_py_o) / v_rel_y
        if t_near_y > t_far_y: t_near_y, t_far_y = t_far_y, t_near_y
    else:
        if a_py_o < min_y - 1e-6 or a_py_o > max_y + 1e-6: return False

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

    t_start = c_max(0.0, t_hit_near)
    t_end = c_min(1.0, t_hit_far)
    t_mid = (t_start + t_end) * 0.5

    a_mid_px = a_px_o + (a_px_n - a_px_o) * t_mid
    a_mid_py = a_py_o + (a_py_n - a_py_o) * t_mid
    b_mid_px = b_px_o + (b_px_n - b_px_o) * t_mid
    b_mid_py = b_py_o + (b_py_n - b_py_o) * t_mid

    mid_overlap_x = c_min((a_mid_px + a_sx) - b_mid_px, (b_mid_px + b_sx) - a_mid_px)
    mid_overlap_y = c_min((a_mid_py + a_sy) - b_mid_py, (b_mid_py + b_sy) - a_mid_py)

    required_overlap = 1e-4 if not is_active else -1e-4

    if mid_overlap_x <= required_overlap or mid_overlap_y <= required_overlap:
        return False

    out_t[0] = c_max(0.0, t_hit_near)
    return True

cdef bint swept_sat_generic(
        int a_type, const vector[double]& a_vx_o, const vector[double]& a_vy_o, const vector[double]& a_vx_n,
        const vector[double]& a_vy_n, const vector[double]& a_ax, const vector[double]& a_ay, double a_dx, double a_dy,
        double a_radius,
        int b_type, const vector[double]& b_vx_o, const vector[double]& b_vy_o, const vector[double]& b_vx_n,
        const vector[double]& b_vy_n, const vector[double]& b_ax, const vector[double]& b_ay, double b_dx, double b_dy,
        double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x, v_rel_y, t_enter, t_exit, best_nx, best_ny
    cdef double min_overlap, overlap, mtv_nx, mtv_ny
    cdef size_t i
    cdef double nx, ny, minA_o, maxA_o, minB_o, maxB_o, minA_n, maxA_n, minB_n, maxB_n, v_proj, t0, t1, inv_v
    cdef double t_start, t_end, t_mid, required_overlap, minA_mid, maxA_mid, minB_mid, maxB_mid, mid_overlap

    cdef vector[double] all_ax_x
    cdef vector[double] all_ax_y
    all_ax_x.reserve(a_ax.size() + b_ax.size() + 16)
    all_ax_y.reserve(a_ay.size() + b_ay.size() + 16)

    for i in range(a_ax.size()):
        all_ax_x.push_back(a_ax[i])
        all_ax_y.push_back(a_ay[i])
    for i in range(b_ax.size()):
        all_ax_x.push_back(b_ax[i])
        all_ax_y.push_back(b_ay[i])

    cdef double dx, dy, ln
    if a_type == 5:
        if b_type == 5:
            dx = b_vx_o[0] - a_vx_o[0];
            dy = b_vy_o[0] - a_vy_o[0]
            ln = sqrt(dx * dx + dy * dy)
            if ln > 1e-6:
                all_ax_x.push_back(dx / ln);
                all_ax_y.push_back(dy / ln)
            dx = b_vx_n[0] - a_vx_n[0];
            dy = b_vy_n[0] - a_vy_n[0]
            ln = sqrt(dx * dx + dy * dy)
            if ln > 1e-6:
                all_ax_x.push_back(dx / ln);
                all_ax_y.push_back(dy / ln)
        else:
            for i in range(b_vx_o.size()):
                dx = b_vx_o[i] - a_vx_o[0];
                dy = b_vy_o[i] - a_vy_o[0]
                ln = sqrt(dx * dx + dy * dy)
                if ln > 1e-6:
                    all_ax_x.push_back(dx / ln);
                    all_ax_y.push_back(dy / ln)
                dx = b_vx_n[i] - a_vx_n[0];
                dy = b_vy_n[i] - a_vy_n[0]
                ln = sqrt(dx * dx + dy * dy)
                if ln > 1e-6:
                    all_ax_x.push_back(dx / ln);
                    all_ax_y.push_back(dy / ln)
    elif b_type == 5:
        for i in range(a_vx_o.size()):
            dx = b_vx_o[0] - a_vx_o[i];
            dy = b_vy_o[0] - a_vy_o[i]
            ln = sqrt(dx * dx + dy * dy)
            if ln > 1e-6:
                all_ax_x.push_back(dx / ln);
                all_ax_y.push_back(dy / ln)
            dx = b_vx_n[0] - a_vx_n[i];
            dy = b_vy_n[0] - a_vy_n[i]
            ln = sqrt(dx * dx + dy * dy)
            if ln > 1e-6:
                all_ax_x.push_back(dx / ln);
                all_ax_y.push_back(dy / ln)

    v_rel_x = a_dx - b_dx
    v_rel_y = a_dy - b_dy
    t_enter = -1e300
    t_exit = 1e300
    best_nx = 0.0
    best_ny = 0.0
    min_overlap = 1e300
    mtv_nx = 0.0
    mtv_ny = 0.0

    for i in range(all_ax_x.size()):
        nx = all_ax_x[i]
        ny = all_ax_y[i]

        project_shape(a_type, a_vx_o, a_vy_o, a_radius, nx, ny, &minA_o, &maxA_o)
        project_shape(b_type, b_vx_o, b_vy_o, b_radius, nx, ny, &minB_o, &maxB_o)

        overlap = c_min(maxA_o - minB_o, maxB_o - minA_o)
        if overlap < min_overlap:
            min_overlap = overlap
            if (maxA_o + minA_o) > (maxB_o + minB_o):
                mtv_nx = nx;
                mtv_ny = ny
            else:
                mtv_nx = -nx;
                mtv_ny = -ny

        v_proj = v_rel_x * nx + v_rel_y * ny
        if v_proj == 0.0:
            if minA_o > maxB_o + 1e-6 or maxA_o < minB_o - 1e-6: return False
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

    t_start = c_max(0.0, t_enter)
    t_end = c_min(1.0, t_exit)
    t_mid = (t_start + t_end) * 0.5
    required_overlap = 1e-4 if not is_active else -1e-4

    for i in range(all_ax_x.size()):
        nx = all_ax_x[i]
        ny = all_ax_y[i]

        project_shape(a_type, a_vx_o, a_vy_o, a_radius, nx, ny, &minA_o, &maxA_o)
        project_shape(a_type, a_vx_n, a_vy_n, a_radius, nx, ny, &minA_n, &maxA_n)
        project_shape(b_type, b_vx_o, b_vy_o, b_radius, nx, ny, &minB_o, &maxB_o)
        project_shape(b_type, b_vx_n, b_vy_n, b_radius, nx, ny, &minB_n, &maxB_n)

        minA_mid = minA_o + (minA_n - minA_o) * t_mid
        maxA_mid = maxA_o + (maxA_n - maxA_o) * t_mid
        minB_mid = minB_o + (minB_n - minB_o) * t_mid
        maxB_mid = maxB_o + (maxB_n - maxB_o) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = c_max(0.0, t_enter)
    return True