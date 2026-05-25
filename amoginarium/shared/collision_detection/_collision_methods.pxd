# cython: language_level=3
from libcpp.vector cimport vector


cdef bint aabb_aabb_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx, double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_sx, double b_sy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept

cdef bint aabb_circle_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_sx, double a_sy,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept

cdef bint circle_circle_swept(
        double a_px_o, double a_py_o, double a_px_n, double a_py_n, double a_radius,
        double b_px_o, double b_py_o, double b_px_n, double b_py_n, double b_radius,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept

cdef bint poly_poly_swept(
        const double* a_vx_o, const double* a_vy_o, size_t a_sz,
        const double* a_ax_x, const double* a_ax_y, size_t a_ax_sz, double a_dx, double a_dy,
        const double* b_vx_o, const double* b_vy_o, size_t b_sz,
        const double* b_ax_x, const double* b_ax_y, size_t b_ax_sz, double b_dx, double b_dy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept

cdef bint circle_poly_swept(
        double c_px_o, double c_py_o, double c_px_n, double c_py_n, double c_radius,
        const double* p_vx_o, const double* p_vy_o, const double* p_vx_n, const double* p_vy_n, size_t p_sz,
        const double* p_ax_x, const double* p_ax_y, size_t p_ax_sz, double p_dx, double p_dy,
        bint is_active,
        double * out_norm_x, double * out_norm_y, double * out_t
) noexcept