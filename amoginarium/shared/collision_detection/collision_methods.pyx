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

    cdef double margin = 0.0001 if not is_active else -0.0001

    cdef double ex_min_x = b_px_o - a_sx
    cdef double ex_max_x = b_px_o + b_sx
    cdef double ex_min_y = b_py_o - a_sy
    cdef double ex_max_y = b_py_o + b_sy

    cdef double m_min_x = ex_min_x + margin
    cdef double m_max_x = ex_max_x - margin
    cdef double m_min_y = ex_min_y + margin
    cdef double m_max_y = ex_max_y - margin

    cdef double ex_t_near_x = -1e300, ex_t_far_x = 1e300
    cdef double ex_t_near_y = -1e300, ex_t_far_y = 1e300
    cdef double m_t_near_x = -1e300, m_t_far_x = 1e300
    cdef double m_t_near_y = -1e300, m_t_far_y = 1e300

    cdef double ex_t_hit_near, ex_t_hit_far, m_t_hit_near, m_t_hit_far
    cdef double dist_left, dist_right, dist_top, dist_bottom, min_dist_x, min_dist_y

    if ex_min_x > ex_max_x or ex_min_y > ex_max_y:
        return False

    if v_rel_x != 0.0:
        ex_t_near_x = (ex_min_x - a_px_o) / v_rel_x
        ex_t_far_x = (ex_max_x - a_px_o) / v_rel_x
        if ex_t_near_x > ex_t_far_x: ex_t_near_x, ex_t_far_x = ex_t_far_x, ex_t_near_x

        m_t_near_x = (m_min_x - a_px_o) / v_rel_x
        m_t_far_x = (m_max_x - a_px_o) / v_rel_x
        if m_t_near_x > m_t_far_x: m_t_near_x, m_t_far_x = m_t_far_x, m_t_near_x
    else:
        if not (ex_min_x <= a_px_o <= ex_max_x): return False
        if not (m_min_x <= a_px_o <= m_max_x): return False

    if v_rel_y != 0.0:
        ex_t_near_y = (ex_min_y - a_py_o) / v_rel_y
        ex_t_far_y = (ex_max_y - a_py_o) / v_rel_y
        if ex_t_near_y > ex_t_far_y: ex_t_near_y, ex_t_far_y = ex_t_far_y, ex_t_near_y

        m_t_near_y = (m_min_y - a_py_o) / v_rel_y
        m_t_far_y = (m_max_y - a_py_o) / v_rel_y
        if m_t_near_y > m_t_far_y: m_t_near_y, m_t_far_y = m_t_far_y, m_t_near_y
    else:
        if not (ex_min_y <= a_py_o <= ex_max_y): return False
        if not (m_min_y <= a_py_o <= m_max_y): return False

    ex_t_hit_near = c_max(ex_t_near_x, ex_t_near_y)
    ex_t_hit_far = c_min(ex_t_far_x, ex_t_far_y)

    m_t_hit_near = c_max(m_t_near_x, m_t_near_y)
    m_t_hit_far = c_min(m_t_far_x, m_t_far_y)

    # EXACT bounds validate impact
    if ex_t_hit_near > ex_t_hit_far or ex_t_hit_far <= 0.0 or ex_t_hit_near >= 1.0:
        return False

    # MARGIN bounds validate flush sliding
    if m_t_hit_near > m_t_hit_far or m_t_hit_far <= 0.0 or m_t_hit_near >= 1.0:
        return False

    # Extract normals exactly
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

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0:
        return False

    out_t[0] = c_max(0.0, ex_t_hit_near)
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

    cdef double ex_t_enter = -1e300
    cdef double ex_t_exit = 1e300
    cdef double m_t_enter = -1e300
    cdef double m_t_exit = 1e300
    cdef double best_nx = 0.0
    cdef double best_ny = 0.0

    cdef double min_overlap = 1e300
    cdef double overlap, mtv_nx = 0.0, mtv_ny = 0.0

    cdef double margin = 0.0001 if not is_active else -0.0001

    cdef size_t i
    cdef double nx, ny, minA, maxA, minB, maxB, v_proj, ex_t0, ex_t1, m_t0, m_t1, inv_v

    for i in range(a_ax.size()):
        nx = a_ax[i]
        ny = a_ay[i]

        project_poly(a_vx_o, a_vy_o, nx, ny, &minA, &maxA)
        project_poly(b_vx_o, b_vy_o, nx, ny, &minB, &maxB)

        # EXACT evaluation
        if minA > maxB or maxA < minB:
            overlap = -1.0
        else:
            overlap = (maxB - minA) if (maxB - minA) < (maxA - minB) else (maxA - minB)
            if overlap < min_overlap:
                min_overlap = overlap
                if (maxA + minA) > (maxB + minB):
                    mtv_nx = nx
                    mtv_ny = ny
                else:
                    mtv_nx = -nx
                    mtv_ny = -ny

        v_proj = v_rel_x * nx + v_rel_y * ny
        if v_proj == 0.0:
            if minA >= maxB or maxA <= minB: return False
            if minA >= maxB - margin or maxA <= minB + margin: return False
        else:
            inv_v = 1.0 / v_proj

            ex_t0 = (minB - maxA) * inv_v
            ex_t1 = (maxB - minA) * inv_v
            if inv_v < 0.0: ex_t0, ex_t1 = ex_t1, ex_t0
            if ex_t0 > ex_t_enter:
                ex_t_enter = ex_t0
                best_nx = -nx if v_proj > 0 else nx
                best_ny = -ny if v_proj > 0 else ny
            if ex_t1 < ex_t_exit: ex_t_exit = ex_t1

            m_t0 = (minB + margin - maxA) * inv_v
            m_t1 = (maxB - margin - minA) * inv_v
            if inv_v < 0.0: m_t0, m_t1 = m_t1, m_t0
            if m_t0 > m_t_enter: m_t_enter = m_t0
            if m_t1 < m_t_exit: m_t_exit = m_t1

            if ex_t_enter > ex_t_exit: return False
            if m_t_enter > m_t_exit: return False

    for i in range(b_ax.size()):
        nx = b_ax[i]
        ny = b_ay[i]

        project_poly(a_vx_o, a_vy_o, nx, ny, &minA, &maxA)
        project_poly(b_vx_o, b_vy_o, nx, ny, &minB, &maxB)

        # EXACT evaluation
        if minA > maxB or maxA < minB:
            overlap = -1.0
        else:
            overlap = (maxB - minA) if (maxB - minA) < (maxA - minB) else (maxA - minB)
            if overlap < min_overlap:
                min_overlap = overlap
                if (maxA + minA) > (maxB + minB):
                    mtv_nx = nx
                    mtv_ny = ny
                else:
                    mtv_nx = -nx
                    mtv_ny = -ny

        v_proj = v_rel_x * nx + v_rel_y * ny
        if v_proj == 0.0:
            if minA >= maxB or maxA <= minB: return False
            if minA >= maxB - margin or maxA <= minB + margin: return False
        else:
            inv_v = 1.0 / v_proj

            ex_t0 = (minB - maxA) * inv_v
            ex_t1 = (maxB - minA) * inv_v
            if inv_v < 0.0: ex_t0, ex_t1 = ex_t1, ex_t0
            if ex_t0 > ex_t_enter:
                ex_t_enter = ex_t0
                best_nx = -nx if v_proj > 0 else nx
                best_ny = -ny if v_proj > 0 else ny
            if ex_t1 < ex_t_exit: ex_t_exit = ex_t1

            m_t0 = (minB + margin - maxA) * inv_v
            m_t1 = (maxB - margin - minA) * inv_v
            if inv_v < 0.0: m_t0, m_t1 = m_t1, m_t0
            if m_t0 > m_t_enter: m_t_enter = m_t0
            if m_t1 < m_t_exit: m_t_exit = m_t1

            if ex_t_enter > ex_t_exit: return False
            if m_t_enter > m_t_exit: return False

    if ex_t_enter >= 1.0 or ex_t_exit <= 0.0: return False
    if m_t_enter >= 1.0 or m_t_exit <= 0.0: return False

    if ex_t_enter <= 0.0:
        out_norm_x[0] = mtv_nx
        out_norm_y[0] = mtv_ny
    else:
        out_norm_x[0] = best_nx
        out_norm_y[0] = best_ny

    if (v_rel_x * out_norm_x[0]) + (v_rel_y * out_norm_y[0]) > 0.0: return False

    out_t[0] = c_max(0.0, ex_t_enter)
    return True