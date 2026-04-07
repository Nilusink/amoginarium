#version 120

varying vec2 v_pos;

uniform vec4 u_color;
uniform float u_inner;
uniform float u_outer;
uniform float u_num_segments;
uniform float u_draw_len;
uniform float u_gap_len;

void main() {
    // 1. Get the angle of the current pixel (0.0 to 2*PI)
    float angle = atan(v_pos.y, v_pos.x);
    if (angle < 0.0) {
        angle += 6.283185307179586;
    }

    // 2. Identify the segment index
    float step_angle = 6.283185307179586 / u_num_segments;
    float current_segment = floor(angle / step_angle);

    // 3. Dash Visibility Check
    float cycle_pos = mod(current_segment, u_draw_len + u_gap_len);
    if (cycle_pos >= u_draw_len) {
        discard; // Pixel is in a gap, instantly abort
    }

    // 4. Polygonal Distance Math
    // Instead of raw circular distance, we project the distance onto the center of the segment slice.
    // This creates the exact "flat" quad edges your original NumPy code had.
    float local_angle = mod(angle, step_angle) - (step_angle / 2.0);
    float poly_dist = length(v_pos) * cos(local_angle);

    // 5. Hard Boundary Check (Matches standard GL_QUADS aliasing)
    if (poly_dist < u_inner || poly_dist > u_outer) {
        discard;
    }

    gl_FragColor = u_color;
}