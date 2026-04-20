# cython: language_level=3
from libcpp.vector cimport vector

cdef bint aabb_aabb_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx, double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_sx, double b_sy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept

cdef bint swept_sat_generic(
        const vector[double]& a_vx_o, const vector[double]& a_vy_o, const vector[double]& a_vx_n,
        const vector[double]& a_vy_n, const vector[double]& a_ax, const vector[double]& a_ay, double a_dx, double a_dy,
        const vector[double]& b_vx_o, const vector[double]& b_vy_o, const vector[double]& b_vx_n,
        const vector[double]& b_vy_n, const vector[double]& b_ax, const vector[double]& b_ay, double b_dx, double b_dy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept