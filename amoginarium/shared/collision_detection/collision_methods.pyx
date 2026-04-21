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
    cdef const double * vx_ptr = vx.data()
    cdef const double * vy_ptr = vy.data()
    cdef size_t i

    if h_type == 5 or h_type == 4:
        p = vx_ptr[0] * nx + vy_ptr[0] * ny
        out_min[0] = p - radius
        out_max[0] = p + radius
    else:
        min_p = vx_ptr[0] * nx + vy_ptr[0] * ny
        max_p = min_p
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

    out_t[0] = c_max(0.0, ex_t_hit_near)
    return True

cdef bint aabb_circle_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx, double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x = (a_px_n - a_px_o) - (b_px_n - b_px_o)
    cdef double v_rel_y = (a_py_n - a_py_o) - (b_py_n - b_py_o)

    cdef double ax_x[4]
    cdef double ax_y[4]
    cdef int num_axes = 2
    ax_x[0] = 1.0;
    ax_y[0] = 0.0
    ax_x[1] = 0.0;
    ax_y[1] = 1.0

    cdef double clamp_x, clamp_y, dx, dy, ln
    clamp_x = c_max(a_px_o, c_min(a_px_o + a_sx, b_px_o))
    clamp_y = c_max(a_py_o, c_min(a_py_o + a_sy, b_py_o))
    dx = b_px_o - clamp_x;
    dy = b_py_o - clamp_y;
    ln = sqrt(dx * dx + dy * dy)
    if ln > 1e-6:
        ax_x[num_axes] = dx / ln;
        ax_y[num_axes] = dy / ln;
        num_axes += 1

    clamp_x = c_max(a_px_n, c_min(a_px_n + a_sx, b_px_n))
    clamp_y = c_max(a_py_n, c_min(a_py_n + a_sy, b_py_n))
    dx = b_px_n - clamp_x;
    dy = b_py_n - clamp_y;
    ln = sqrt(dx * dx + dy * dy)
    if ln > 1e-6:
        ax_x[num_axes] = dx / ln;
        ax_y[num_axes] = dy / ln;
        num_axes += 1

    cdef double t_enter = -1e300, t_exit = 1e300
    cdef double best_nx = 0.0, best_ny = 0.0
    cdef double min_overlap = 1e300, mtv_nx = 0.0, mtv_ny = 0.0

    cdef double minA_o_arr[4]
    cdef double maxA_o_arr[4]
    cdef double minA_n_arr[4]
    cdef double maxA_n_arr[4]
    cdef double minB_o_arr[4]
    cdef double maxB_o_arr[4]
    cdef double minB_n_arr[4]
    cdef double maxB_n_arr[4]

    cdef size_t i
    cdef double nx, ny, C_A, E_A, C_B, minA_o, maxA_o, minB_o, maxB_o, overlap, v_proj, inv_v, t0, t1

    for i in range(num_axes):
        nx = ax_x[i];
        ny = ax_y[i]

        C_A = (a_px_o + a_sx * 0.5) * nx + (a_py_o + a_sy * 0.5) * ny
        E_A = (a_sx * 0.5) * (nx if nx > 0 else -nx) + (a_sy * 0.5) * (ny if ny > 0 else -ny)
        minA_o = C_A - E_A;
        maxA_o = C_A + E_A

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

        C_A = (a_px_n + a_sx * 0.5) * nx + (a_py_n + a_sy * 0.5) * ny
        minA_n_arr[i] = C_A - E_A;
        maxA_n_arr[i] = C_A + E_A
        C_B = b_px_n * nx + b_py_n * ny
        minB_n_arr[i] = C_B - b_radius;
        maxB_n_arr[i] = C_B + b_radius

    if t_enter >= 1.0 or t_exit <= 0.0: return False
    if t_enter <= 0.0:
        out_norm_x[0] = mtv_nx;
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx;
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    cdef double t_mid = (c_max(0.0, t_enter) + c_min(1.0, t_exit)) * 0.5
    cdef double required_overlap = 1e-4 if not is_active else -1e-4
    cdef double minA_mid, maxA_mid, minB_mid, maxB_mid, mid_overlap

    for i in range(num_axes):
        minA_mid = minA_o_arr[i] + (minA_n_arr[i] - minA_o_arr[i]) * t_mid
        maxA_mid = maxA_o_arr[i] + (maxA_n_arr[i] - maxA_o_arr[i]) * t_mid
        minB_mid = minB_o_arr[i] + (minB_n_arr[i] - minB_o_arr[i]) * t_mid
        maxB_mid = maxB_o_arr[i] + (maxB_n_arr[i] - maxB_o_arr[i]) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = c_max(0.0, t_enter)
    return True

cdef bint circle_circle_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_radius,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept:
    cdef double v_rel_x = (a_px_n - a_px_o) - (b_px_n - b_px_o)
    cdef double v_rel_y = (a_py_n - a_py_o) - (b_py_n - b_py_o)

    cdef double ax_x[2]
    cdef double ax_y[2]
    cdef int num_axes = 0

    cdef double dx, dy, ln
    dx = b_px_o - a_px_o;
    dy = b_py_o - a_py_o;
    ln = sqrt(dx * dx + dy * dy)
    if ln > 1e-6:
        ax_x[num_axes] = dx / ln;
        ax_y[num_axes] = dy / ln;
        num_axes += 1
    else:
        ax_x[num_axes] = 1.0;
        ax_y[num_axes] = 0.0;
        num_axes += 1

    dx = b_px_n - a_px_n;
    dy = b_py_n - a_py_n;
    ln = sqrt(dx * dx + dy * dy)
    if ln > 1e-6:
        ax_x[num_axes] = dx / ln;
        ax_y[num_axes] = dy / ln;
        num_axes += 1

    cdef double t_enter = -1e300, t_exit = 1e300
    cdef double best_nx = 0.0, best_ny = 0.0
    cdef double min_overlap = 1e300, mtv_nx = 0.0, mtv_ny = 0.0

    cdef double minA_o_arr[2]
    cdef double maxA_o_arr[2]
    cdef double minA_n_arr[2]
    cdef double maxA_n_arr[2]
    cdef double minB_o_arr[2]
    cdef double maxB_o_arr[2]
    cdef double minB_n_arr[2]
    cdef double maxB_n_arr[2]

    cdef size_t i
    cdef double nx, ny, C_A, C_B, minA_o, maxA_o, minB_o, maxB_o, overlap, v_proj, inv_v, t0, t1

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

        C_A = a_px_n * nx + a_py_n * ny
        minA_n_arr[i] = C_A - a_radius;
        maxA_n_arr[i] = C_A + a_radius
        C_B = b_px_n * nx + b_py_n * ny
        minB_n_arr[i] = C_B - b_radius;
        maxB_n_arr[i] = C_B + b_radius

    if t_enter >= 1.0 or t_exit <= 0.0: return False
    if t_enter <= 0.0:
        out_norm_x[0] = mtv_nx;
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx;
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    cdef double t_mid = (c_max(0.0, t_enter) + c_min(1.0, t_exit)) * 0.5
    cdef double required_overlap = 1e-4 if not is_active else -1e-4
    cdef double minA_mid, maxA_mid, minB_mid, maxB_mid, mid_overlap

    for i in range(num_axes):
        minA_mid = minA_o_arr[i] + (minA_n_arr[i] - minA_o_arr[i]) * t_mid
        maxA_mid = maxA_o_arr[i] + (maxA_n_arr[i] - maxA_o_arr[i]) * t_mid
        minB_mid = minB_o_arr[i] + (minB_n_arr[i] - minB_o_arr[i]) * t_mid
        maxB_mid = maxB_o_arr[i] + (maxB_n_arr[i] - maxB_o_arr[i]) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = c_max(0.0, t_enter)
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

    cdef double ax_x[64]
    cdef double ax_y[64]
    cdef int num_axes = 0

    cdef double minA_o_arr[64]
    cdef double maxA_o_arr[64]
    cdef double minA_n_arr[64]
    cdef double maxA_n_arr[64]
    cdef double minB_o_arr[64]
    cdef double maxB_o_arr[64]
    cdef double minB_n_arr[64]
    cdef double maxB_n_arr[64]

    cdef const double * a_vx_o_ptr = a_vx_o.data()
    cdef const double * a_vy_o_ptr = a_vy_o.data()
    cdef const double * a_vx_n_ptr = a_vx_n.data()
    cdef const double * a_vy_n_ptr = a_vy_n.data()
    cdef const double * b_vx_o_ptr = b_vx_o.data()
    cdef const double * b_vy_o_ptr = b_vy_o.data()
    cdef const double * b_vx_n_ptr = b_vx_n.data()
    cdef const double * b_vy_n_ptr = b_vy_n.data()

    cdef size_t a_ax_sz = a_ax.size()
    cdef size_t b_ax_sz = b_ax.size()

    for i in range(a_ax_sz):
        ax_x[num_axes] = a_ax[i]
        ax_y[num_axes] = a_ay[i]
        num_axes += 1
    for i in range(b_ax_sz):
        ax_x[num_axes] = b_ax[i]
        ax_y[num_axes] = b_ay[i]
        num_axes += 1

    cdef double dx, dy, ln, inv_ln
    cdef size_t b_vx_sz, a_vx_sz
    if a_type == 5 or a_type == 4:
        if b_type == 5 or b_type == 4:
            pass  # handled entirely by circle_circle_swept
        else:
            b_vx_sz = b_vx_o.size()
            for i in range(b_vx_sz):
                dx = b_vx_o_ptr[i] - a_vx_o_ptr[0];
                dy = b_vy_o_ptr[i] - a_vy_o_ptr[0]
                ln = sqrt(dx * dx + dy * dy)
                if ln > 1e-6:
                    inv_ln = 1.0 / ln
                    ax_x[num_axes] = dx * inv_ln;
                    ax_y[num_axes] = dy * inv_ln
                    num_axes += 1
                dx = b_vx_n_ptr[i] - a_vx_n_ptr[0];
                dy = b_vy_n_ptr[i] - a_vy_n_ptr[0]
                ln = sqrt(dx * dx + dy * dy)
                if ln > 1e-6:
                    inv_ln = 1.0 / ln
                    ax_x[num_axes] = dx * inv_ln;
                    ax_y[num_axes] = dy * inv_ln
                    num_axes += 1
    elif b_type == 5 or b_type == 4:
        a_vx_sz = a_vx_o.size()
        for i in range(a_vx_sz):
            dx = b_vx_o_ptr[0] - a_vx_o_ptr[i];
            dy = b_vy_o_ptr[0] - a_vy_o_ptr[i]
            ln = sqrt(dx * dx + dy * dy)
            if ln > 1e-6:
                inv_ln = 1.0 / ln
                ax_x[num_axes] = dx * inv_ln;
                ax_y[num_axes] = dy * inv_ln
                num_axes += 1
            dx = b_vx_n_ptr[0] - a_vx_n_ptr[i];
            dy = b_vy_n_ptr[0] - a_vy_n_ptr[i]
            ln = sqrt(dx * dx + dy * dy)
            if ln > 1e-6:
                inv_ln = 1.0 / ln
                ax_x[num_axes] = dx * inv_ln;
                ax_y[num_axes] = dy * inv_ln
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

        project_shape(a_type, a_vx_o, a_vy_o, a_radius, nx, ny, &minA_o, &maxA_o)
        project_shape(b_type, b_vx_o, b_vy_o, b_radius, nx, ny, &minB_o, &maxB_o)

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

        project_shape(a_type, a_vx_n, a_vy_n, a_radius, nx, ny, &minA_n_arr[i], &maxA_n_arr[i])
        project_shape(b_type, b_vx_n, b_vy_n, b_radius, nx, ny, &minB_n_arr[i], &maxB_n_arr[i])

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

    for i in range(num_axes):
        minA_mid = minA_o_arr[i] + (minA_n_arr[i] - minA_o_arr[i]) * t_mid
        maxA_mid = maxA_o_arr[i] + (maxA_n_arr[i] - maxA_o_arr[i]) * t_mid
        minB_mid = minB_o_arr[i] + (minB_n_arr[i] - minB_o_arr[i]) * t_mid
        maxB_mid = maxB_o_arr[i] + (maxB_n_arr[i] - maxB_o_arr[i]) * t_mid

        mid_overlap = c_min(maxA_mid - minB_mid, maxB_mid - minA_mid)
        if mid_overlap <= required_overlap:
            return False

    out_t[0] = c_max(0.0, t_enter)
    return True