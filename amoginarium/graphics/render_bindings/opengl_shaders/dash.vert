#version 120

// Pass the raw X/Y coordinates directly to the fragment shader
varying vec2 v_pos;

void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    v_pos = gl_Vertex.xy;
}