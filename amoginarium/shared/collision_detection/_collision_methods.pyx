# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""
Collision Methods.

| ``Path``: amoginarium/shared/collision_detection/collision_methods.pyx
| ``Project``: amoginarium
| ``Created``: 17.04.2026
| ``Authors``: LukasKrah
"""

from libc.math cimport sqrt
from libcpp.vector cimport vector


cdef inline double c_max(double a, double b) noexcept: return a if a > b else b
cdef inline double c_min(double a, double b) noexcept: return a if a < b else b

cdef inline void project_poly(const double * vx, const double * vy, size_t sz,
                              double nx, double ny, double * out_min,
                              double * out_max) noexcept:
    cdef double min_p, max_p, p0, p1, p2, p3, min1, max1, min2, max2
    cdef size_t i
    if sz == 4:
        p0 = vx[0] * nx + vy[0] * ny
        p1 = vx[1] * nx + vy[1] * ny
        p2 = vx[2] * nx + vy[2] * ny
        p3 = vx[3] * nx + vy[3] * ny
        min1 = p0 if p0 < p1 else p1
        max1 = p0 if p0 > p1 else p1
        min2 = p2 if p2 < p3 else p3
        max2 = p2 if p2 > p3 else p3
        out_min[0] = min1 if min1 < min2 else min2
        out_max[0] = max1 if max1 > max2 else max2
    elif sz == 3:
        p0 = vx[0] * nx + vy[0] * ny
        p1 = vx[1] * nx + vy[1] * ny
        p2 = vx[2] * nx + vy[2] * ny
        min1 = p0 if p0 < p1 else p1
        max1 = p0 if p0 > p1 else p1
        out_min[0] = min1 if min1 < p2 else p2
        out_max[0] = max1 if max1 > p2 else p2
    elif sz == 1:
        p0 = vx[0] * nx + vy[0] * ny
        out_min[0] = p0
        out_max[0] = p0
    else:
        min_p = vx[0] * nx + vy[0] * ny
        max_p = min_p
        for i in range(1, sz):
            p0 = vx[i] * nx + vy[i] * ny
            if p0 < min_p:
                min_p = p0
            elif p0 > max_p:
                max_p = p0
        out_min[0] = min_p
        out_max[0] = max_p

cdef bint aabb_aabb_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx,
        double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_sx,
        double b_sy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x, v_rel_y, min_x, max_x, min_y, max_y, inv_v_x, inv_v_y
    cdef double ex_min_x, ex_max_x, ex_min_y, ex_max_y, m_min_x, m_max_x, m_min_y, m_max_y
    cdef double ex_t_near_x, ex_t_far_x, ex_t_near_y, ex_t_far_y, m_t_near_x, m_t_far_x, m_t_near_y, m_t_far_y
    cdef double ex_t_hit_near, ex_t_hit_far, m_t_hit_near, m_t_hit_far
    cdef double dist_left, dist_right, dist_top, dist_bottom, min_dist_x, min_dist_y
    cdef double margin

    v_rel_x = (a_px_n - a_px_o) - (b_px_n - b_px_o)
    v_rel_y = (a_py_n - a_py_o) - (b_py_n - b_py_o)

    margin = 0.0001 if not is_active else -0.0001

    ex_min_x = b_px_o - a_sx
    ex_max_x = b_px_o + b_sx
    ex_min_y = b_py_o - a_sy
    ex_max_y = b_py_o + b_sy

    m_min_x = ex_min_x + margin
    m_max_x = ex_max_x - margin
    m_min_y = ex_min_y + margin
    m_max_y = ex_max_y - margin

    ex_t_near_x = -1e300;
    ex_t_far_x = 1e300
    ex_t_near_y = -1e300;
    ex_t_far_y = 1e300
    m_t_near_x = -1e300;
    m_t_far_x = 1e300
    m_t_near_y = -1e300;
    m_t_far_y = 1e300

    if ex_min_x > ex_max_x or ex_min_y > ex_max_y: return False

    if v_rel_x != 0.0:
        inv_v_x = 1.0 / v_rel_x
        ex_t_near_x = (ex_min_x - a_px_o) * inv_v_x
        ex_t_far_x = (ex_max_x - a_px_o) * inv_v_x
        if ex_t_near_x > ex_t_far_x: ex_t_near_x, ex_t_far_x = ex_t_far_x, ex_t_near_x

        m_t_near_x = (m_min_x - a_px_o) * inv_v_x
        m_t_far_x = (m_max_x - a_px_o) * inv_v_x
        if m_t_near_x > m_t_far_x: m_t_near_x, m_t_far_x = m_t_far_x, m_t_near_x
    else:
        if not (ex_min_x <= a_px_o <= ex_max_x): return False
        if not (m_min_x <= a_px_o <= m_max_x): return False

    if v_rel_y != 0.0:
        inv_v_y = 1.0 / v_rel_y
        ex_t_near_y = (ex_min_y - a_py_o) * inv_v_y
        ex_t_far_y = (ex_max_y - a_py_o) * inv_v_y
        if ex_t_near_y > ex_t_far_y: ex_t_near_y, ex_t_far_y = ex_t_far_y, ex_t_near_y

        m_t_near_y = (m_min_y - a_py_o) * inv_v_y
        m_t_far_y = (m_max_y - a_py_o) * inv_v_y
        if m_t_near_y > m_t_far_y: m_t_near_y, m_t_far_y = m_t_far_y, m_t_near_y
    else:
        if not (ex_min_y <= a_py_o <= ex_max_y): return False
        if not (m_min_y <= a_py_o <= m_max_y): return False

    ex_t_hit_near = c_max(ex_t_near_x, ex_t_near_y)
    ex_t_hit_far = c_min(ex_t_far_x, ex_t_far_y)

    m_t_hit_near = c_max(m_t_near_x, m_t_near_y)
    m_t_hit_far = c_min(m_t_far_x, m_t_far_y)

    if ex_t_hit_near > ex_t_hit_far or ex_t_hit_far <= 0.0 or ex_t_hit_near >= 1.0: return False
    if m_t_hit_near > m_t_hit_far or m_t_hit_far <= 0.0 or m_t_hit_near >= 1.0: return False

    if ex_t_hit_near <= 0.0:
        dist_left = a_px_o - ex_min_x
        dist_right = ex_max_x - a_px_o
        dist_top = a_py_o - ex_min_y
        dist_bottom = ex_max_y - a_py_o
        min_dist_x = dist_left if dist_left < dist_right else dist_right
        min_dist_y = dist_top if dist_top < dist_bottom else dist_bottom

        if min_dist_x < min_dist_y:
            out_norm_x[0] = -1.0 if dist_left < dist_right else 1.0
            out_norm_y[0] = 0.0
        else:
            out_norm_x[0] = 0.0
            out_norm_y[0] = -1.0 if dist_top < dist_bottom else 1.0
    else:
        if ex_t_near_x > ex_t_near_y:
            out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
            out_norm_y[0] = 0.0
        elif ex_t_near_y > ex_t_near_x:
            out_norm_x[0] = 0.0
            out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0
        else:
            out_norm_x[0] = -1.0 if v_rel_x > 0.0 else 1.0
            out_norm_y[0] = -1.0 if v_rel_y > 0.0 else 1.0

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    out_t[0] = ex_t_hit_near
    return True

cdef bint aabb_circle_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx,
        double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x, v_rel_y, a_dx, a_dy, b_dx, b_dy
    cdef double clamp_x, clamp_y, dx, dy, ln_sq, inv_ln
    cdef double t_enter, t_exit, best_nx, best_ny, min_overlap, mtv_nx, mtv_ny
    cdef size_t i
    cdef double nx, ny, C_A, E_A, C_B, minA_o, maxA_o, minB_o, maxB_o, overlap, v_proj, inv_v, t0, t1
    cdef double t_mid, required_overlap, minA_mid, maxA_mid, minB_mid, maxB_mid, mid_overlap

    cdef double ax_x[4]
    cdef double ax_y[4]
    cdef int num_axes = 2
    cdef int static_axes = 2
    cdef int curr_axis = 0
    cdef bint dynamic_generated = False

    cdef double minA_o_arr[4]
    cdef double maxA_o_arr[4]
    cdef double minB_o_arr[4]
    cdef double maxB_o_arr[4]

    a_dx = a_px_n - a_px_o;
    a_dy = a_py_n - a_py_o
    b_dx = b_px_n - b_px_o;
    b_dy = b_py_n - b_py_o
    v_rel_x = a_dx - b_dx;
    v_rel_y = a_dy - b_dy

    ax_x[0] = 1.0;
    ax_y[0] = 0.0
    ax_x[1] = 0.0;
    ax_y[1] = 1.0

    t_enter = -1e300;
    t_exit = 1e300
    best_nx = 0.0;
    best_ny = 0.0
    min_overlap = 1e300;
    mtv_nx = 0.0;
    mtv_ny = 0.0

    while curr_axis < num_axes:
        nx = ax_x[curr_axis];
        ny = ax_y[curr_axis]

        C_A = (a_px_o + a_sx * 0.5) * nx + (a_py_o + a_sy * 0.5) * ny
        E_A = (a_sx * 0.5) * (nx if nx > 0 else -nx) + (a_sy * 0.5) * (
            ny if ny > 0 else -ny)
        minA_o = C_A - E_A;
        maxA_o = C_A + E_A

        C_B = b_px_o * nx + b_py_o * ny
        minB_o = C_B - b_radius;
        maxB_o = C_B + b_radius

        minA_o_arr[curr_axis] = minA_o;
        maxA_o_arr[curr_axis] = maxA_o
        minB_o_arr[curr_axis] = minB_o;
        maxB_o_arr[curr_axis] = maxB_o

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

        curr_axis += 1

        if curr_axis == static_axes and not dynamic_generated:
            dynamic_generated = True

            clamp_x = c_max(a_px_o, c_min(a_px_o + a_sx, b_px_o))
            clamp_y = c_max(a_py_o, c_min(a_py_o + a_sy, b_py_o))
            dx = b_px_o - clamp_x;
            dy = b_py_o - clamp_y;
            ln_sq = dx * dx + dy * dy
            if ln_sq > 1e-12:
                inv_ln = 1.0 / sqrt(ln_sq)
                ax_x[num_axes] = dx * inv_ln;
                ax_y[num_axes] = dy * inv_ln;
                num_axes += 1

            clamp_x = c_max(a_px_n, c_min(a_px_n + a_sx, b_px_n))
            clamp_y = c_max(a_py_n, c_min(a_py_n + a_sy, b_py_n))
            dx = b_px_n - clamp_x;
            dy = b_py_n - clamp_y;
            ln_sq = dx * dx + dy * dy
            if ln_sq > 1e-12:
                inv_ln = 1.0 / sqrt(ln_sq)
                ax_x[num_axes] = dx * inv_ln;
                ax_y[num_axes] = dy * inv_ln;
                num_axes += 1

    if t_enter >= 1.0 or t_exit <= 0.0: return False
    if t_enter <= 0.0:
        out_norm_x[0] = mtv_nx;
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx;
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    t_mid = (c_max(0.0, t_enter) + c_min(1.0, t_exit)) * 0.5
    required_overlap = 1e-4 if not is_active else -1e-4

    for i in range(num_axes):
        nx = ax_x[i];
        ny = ax_y[i]
        minA_mid = minA_o_arr[i] + (a_dx * nx + a_dy * ny) * t_mid
        maxA_mid = maxA_o_arr[i] + (a_dx * nx + a_dy * ny) * t_mid
        minB_mid = minB_o_arr[i] + (b_dx * nx + b_dy * ny) * t_mid
        maxB_mid = maxB_o_arr[i] + (b_dx * nx + b_dy * ny) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = t_enter
    return True

cdef bint circle_circle_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_radius,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x, v_rel_y, a_dx, a_dy, b_dx, b_dy
    cdef double dx, dy, ln_sq, inv_ln
    cdef double t_enter, t_exit, best_nx, best_ny, min_overlap, mtv_nx, mtv_ny
    cdef size_t i
    cdef double nx, ny, C_A, C_B, minA_o, maxA_o, minB_o, maxB_o, overlap, v_proj, inv_v, t0, t1
    cdef double t_mid, required_overlap, minA_mid, maxA_mid, minB_mid, maxB_mid, mid_overlap

    cdef double ax_x[2]
    cdef double ax_y[2]
    cdef int num_axes = 0
    cdef double minA_o_arr[2]
    cdef double maxA_o_arr[2]
    cdef double minB_o_arr[2]
    cdef double maxB_o_arr[2]

    a_dx = a_px_n - a_px_o;
    a_dy = a_py_n - a_py_o
    b_dx = b_px_n - b_px_o;
    b_dy = b_py_n - b_py_o
    v_rel_x = a_dx - b_dx;
    v_rel_y = a_dy - b_dy

    dx = b_px_o - a_px_o;
    dy = b_py_o - a_py_o;
    ln_sq = dx * dx + dy * dy
    if ln_sq > 1e-12:
        inv_ln = 1.0 / sqrt(ln_sq)
        ax_x[num_axes] = dx * inv_ln;
        ax_y[num_axes] = dy * inv_ln;
        num_axes += 1
    else:
        ax_x[num_axes] = 1.0;
        ax_y[num_axes] = 0.0;
        num_axes += 1

    dx = b_px_n - a_px_n;
    dy = b_py_n - a_py_n;
    ln_sq = dx * dx + dy * dy
    if ln_sq > 1e-12:
        inv_ln = 1.0 / sqrt(ln_sq)
        ax_x[num_axes] = dx * inv_ln;
        ax_y[num_axes] = dy * inv_ln;
        num_axes += 1

    t_enter = -1e300;
    t_exit = 1e300
    best_nx = 0.0;
    best_ny = 0.0
    min_overlap = 1e300;
    mtv_nx = 0.0;
    mtv_ny = 0.0

    for i in range(num_axes):
        nx = ax_x[i];
        ny = ax_y[i]

        C_A = a_px_o * nx + a_py_o * ny
        minA_o = C_A - a_radius;
        maxA_o = C_A + a_radius

        C_B = b_px_o * nx + b_py_o * ny
        minB_o = C_B - b_radius;
        maxB_o = C_B + b_radius

        minA_o_arr[i] = minA_o;
        maxA_o_arr[i] = maxA_o
        minB_o_arr[i] = minB_o;
        maxB_o_arr[i] = maxB_o

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
        out_norm_x[0] = mtv_nx;
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx;
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    t_mid = (c_max(0.0, t_enter) + c_min(1.0, t_exit)) * 0.5
    required_overlap = 1e-4 if not is_active else -1e-4

    for i in range(num_axes):
        nx = ax_x[i];
        ny = ax_y[i]
        minA_mid = minA_o_arr[i] + (a_dx * nx + a_dy * ny) * t_mid
        maxA_mid = maxA_o_arr[i] + (a_dx * nx + a_dy * ny) * t_mid
        minB_mid = minB_o_arr[i] + (b_dx * nx + b_dy * ny) * t_mid
        maxB_mid = maxB_o_arr[i] + (b_dx * nx + b_dy * ny) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = t_enter
    return True

cdef bint poly_poly_swept(
        const double * a_vx_o, const double * a_vy_o, size_t a_sz,
        const double * a_ax_x, const double * a_ax_y, size_t a_ax_sz, double a_dx,
        double a_dy,
        const double * b_vx_o, const double * b_vy_o, size_t b_sz,
        const double * b_ax_x, const double * b_ax_y, size_t b_ax_sz, double b_dx,
        double b_dy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x, v_rel_y, t_enter, t_exit, best_nx, best_ny
    cdef double min_overlap, overlap, mtv_nx, mtv_ny
    cdef size_t i
    cdef double nx, ny, minA_o, maxA_o, minB_o, maxB_o, v_proj, t0, t1, inv_v
    cdef double t_mid, required_overlap, minA_mid, maxA_mid, minB_mid, maxB_mid, mid_overlap

    cdef double ax_x[64]
    cdef double ax_y[64]
    cdef int num_axes = 0

    cdef double minA_o_arr[64]
    cdef double maxA_o_arr[64]
    cdef double minB_o_arr[64]
    cdef double maxB_o_arr[64]

    for i in range(a_ax_sz):
        ax_x[num_axes] = a_ax_x[i]
        ax_y[num_axes] = a_ax_y[i]
        num_axes += 1

    for i in range(b_ax_sz):
        ax_x[num_axes] = b_ax_x[i]
        ax_y[num_axes] = b_ax_y[i]
        num_axes += 1

    v_rel_x = a_dx - b_dx
    v_rel_y = a_dy - b_dy
    t_enter = -1e300
    t_exit = 1e300
    best_nx = 0.0
    best_ny = 0.0
    min_overlap = 1e300
    mtv_nx = 0.0
    mtv_ny = 0.0

    for i in range(num_axes):
        nx = ax_x[i]
        ny = ax_y[i]

        project_poly(a_vx_o, a_vy_o, a_sz, nx, ny, &minA_o, &maxA_o)
        project_poly(b_vx_o, b_vy_o, b_sz, nx, ny, &minB_o, &maxB_o)

        minA_o_arr[i] = minA_o;
        maxA_o_arr[i] = maxA_o
        minB_o_arr[i] = minB_o;
        maxB_o_arr[i] = maxB_o

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

    t_mid = (c_max(0.0, t_enter) + c_min(1.0, t_exit)) * 0.5
    required_overlap = 1e-4 if not is_active else -1e-4

    for i in range(num_axes):
        nx = ax_x[i]
        ny = ax_y[i]

        minA_mid = minA_o_arr[i] + (a_dx * nx + a_dy * ny) * t_mid
        maxA_mid = maxA_o_arr[i] + (a_dx * nx + a_dy * ny) * t_mid
        minB_mid = minB_o_arr[i] + (b_dx * nx + b_dy * ny) * t_mid
        maxB_mid = maxB_o_arr[i] + (b_dx * nx + b_dy * ny) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = t_enter
    return True

cdef bint circle_poly_swept(
        double c_px_o, double c_py_o, double c_px_n, double c_py_n, double c_radius,
        const double * p_vx_o, const double * p_vy_o, const double * p_vx_n,
        const double * p_vy_n, size_t p_sz,
        const double * p_ax_x, const double * p_ax_y, size_t p_ax_sz, double p_dx,
        double p_dy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x, v_rel_y, t_enter, t_exit, best_nx, best_ny
    cdef double min_overlap, overlap, mtv_nx, mtv_ny
    cdef size_t i, closest_o, closest_n
    cdef double nx, ny, minC_o, maxC_o, minP_o, maxP_o, v_proj, t0, t1, inv_v
    cdef double t_mid, required_overlap, minC_mid, maxC_mid, minP_mid, maxP_mid, mid_overlap
    cdef double c_dx, c_dy, dx, dy, ln_sq, inv_ln, min_dist_sq_o, min_dist_sq_n

    cdef double ax_x[32]
    cdef double ax_y[32]
    cdef int num_axes = 0
    cdef int static_axes = 0
    cdef int curr_axis = 0
    cdef bint dynamic_generated = False

    cdef double minC_o_arr[32]
    cdef double maxC_o_arr[32]
    cdef double minP_o_arr[32]
    cdef double maxP_o_arr[32]

    c_dx = c_px_n - c_px_o
    c_dy = c_py_n - c_py_o

    for i in range(p_ax_sz):
        ax_x[num_axes] = p_ax_x[i]
        ax_y[num_axes] = p_ax_y[i]
        num_axes += 1

    static_axes = num_axes

    v_rel_x = c_dx - p_dx
    v_rel_y = c_dy - p_dy
    t_enter = -1e300
    t_exit = 1e300
    best_nx = 0.0
    best_ny = 0.0
    min_overlap = 1e300
    mtv_nx = 0.0
    mtv_ny = 0.0

    while curr_axis < num_axes:
        nx = ax_x[curr_axis]
        ny = ax_y[curr_axis]

        minC_o = (c_px_o * nx + c_py_o * ny) - c_radius
        maxC_o = (c_px_o * nx + c_py_o * ny) + c_radius

        project_poly(p_vx_o, p_vy_o, p_sz, nx, ny, &minP_o, &maxP_o)

        minC_o_arr[curr_axis] = minC_o;
        maxC_o_arr[curr_axis] = maxC_o
        minP_o_arr[curr_axis] = minP_o;
        maxP_o_arr[curr_axis] = maxP_o

        overlap = c_min(maxC_o - minP_o, maxP_o - minC_o)
        if overlap < min_overlap:
            min_overlap = overlap
            if (maxC_o + minC_o) > (maxP_o + minP_o):
                mtv_nx = nx;
                mtv_ny = ny
            else:
                mtv_nx = -nx;
                mtv_ny = -ny

        v_proj = v_rel_x * nx + v_rel_y * ny
        if v_proj == 0.0:
            if minC_o > maxP_o + 1e-6 or maxC_o < minP_o - 1e-6: return False
        else:
            inv_v = 1.0 / v_proj
            t0 = (minP_o - maxC_o) * inv_v
            t1 = (maxP_o - minC_o) * inv_v
            if inv_v < 0.0: t0, t1 = t1, t0
            if t0 > t_enter:
                t_enter = t0
                best_nx = -nx if v_proj > 0 else nx
                best_ny = -ny if v_proj > 0 else ny
            if t1 < t_exit: t_exit = t1
            if t_enter > t_exit: return False

        curr_axis += 1

        if curr_axis == static_axes and not dynamic_generated:
            dynamic_generated = True
            min_dist_sq_o = 1e300
            min_dist_sq_n = 1e300
            closest_o = 0
            closest_n = 0

            for i in range(p_sz):
                dx = p_vx_o[i] - c_px_o
                dy = p_vy_o[i] - c_py_o
                ln_sq = dx * dx + dy * dy
                if ln_sq < min_dist_sq_o:
                    min_dist_sq_o = ln_sq
                    closest_o = i

                dx = p_vx_n[i] - c_px_n
                dy = p_vy_n[i] - c_py_n
                ln_sq = dx * dx + dy * dy
                if ln_sq < min_dist_sq_n:
                    min_dist_sq_n = ln_sq
                    closest_n = i

            dx = p_vx_o[closest_o] - c_px_o
            dy = p_vy_o[closest_o] - c_py_o
            if min_dist_sq_o > 1e-12:
                inv_ln = 1.0 / sqrt(min_dist_sq_o)
                ax_x[num_axes] = dx * inv_ln;
                ax_y[num_axes] = dy * inv_ln
                num_axes += 1

            dx = p_vx_n[closest_n] - c_px_n
            dy = p_vy_n[closest_n] - c_py_n
            if min_dist_sq_n > 1e-12:
                inv_ln = 1.0 / sqrt(min_dist_sq_n)
                ax_x[num_axes] = dx * inv_ln;
                ax_y[num_axes] = dy * inv_ln
                num_axes += 1

    if t_enter >= 1.0 or t_exit <= 0.0: return False

    if t_enter <= 0.0:
        out_norm_x[0] = mtv_nx;
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx;
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    t_mid = (c_max(0.0, t_enter) + c_min(1.0, t_exit)) * 0.5
    required_overlap = 1e-4 if not is_active else -1e-4

    for i in range(num_axes):
        nx = ax_x[i]
        ny = ax_y[i]

        minC_mid = minC_o_arr[i] + (c_dx * nx + c_dy * ny) * t_mid
        maxC_mid = maxC_o_arr[i] + (c_dx * nx + c_dy * ny) * t_mid
        minP_mid = minP_o_arr[i] + (p_dx * nx + p_dy * ny) * t_mid
        maxP_mid = maxP_o_arr[i] + (p_dx * nx + p_dy * ny) * t_mid

        mid_overlap = c_min(maxC_mid - minP_mid, maxP_mid - minC_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = t_enter
    return True
