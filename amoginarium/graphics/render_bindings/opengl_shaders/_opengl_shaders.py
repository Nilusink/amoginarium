"""
Loads, compiles, and manages OpenGL shader programs and uniforms.

Path: amoginarium/graphics/render_bindings/opengl_shaders/_opengl_shaders.py
Project: amoginarium
Created: 07.04.2026
Authors: LukasKrah
"""

import os
import typing as tp

from OpenGL.GL import *
from OpenGL.GL import shaders


class BaseShader:
    """Base class responsible for loading and compiling shaders."""

    def __init__(self, *path: str, name: str):
        self.path = path
        self.name = name
        self.program = None
        self._compile_shader()
        self._init_uniforms()

    def _compile_shader(self):
        # Assumes the 'opengl_shaders' folder is in the same directory as this file
        base_dir = os.path.dirname(__file__)
        vert_path = os.path.join(base_dir, *self.path, f"{self.name}.vert")
        frag_path = os.path.join(base_dir, *self.path, f"{self.name}.frag")

        with open(vert_path, "r") as f:
            vert_code = f.read()
        with open(frag_path, "r") as f:
            frag_code = f.read()

        v_shader = shaders.compileShader(vert_code, GL_VERTEX_SHADER)
        f_shader = shaders.compileShader(frag_code, GL_FRAGMENT_SHADER)
        self.program = shaders.compileProgram(v_shader, f_shader)

    def _init_uniforms(self):
        """Override this in subclasses to cache specific uniform locations."""
        pass

    def use(self):
        """Convenience method to activate the shader."""
        glUseProgram(self.program)


class DashShader(BaseShader):
    """Subclass specifically for the dash shader."""

    def __init__(self):
        super().__init__(name="dash")

    def _init_uniforms(self):
        # Cache specific locations for the dash shader
        self.u_color_loc = glGetUniformLocation(self.program, "u_color")
        self.u_inner_loc = glGetUniformLocation(self.program, "u_inner")
        self.u_outer_loc = glGetUniformLocation(self.program, "u_outer")
        self.u_num_seg_loc = glGetUniformLocation(self.program, "u_num_segments")
        self.u_draw_len_loc = glGetUniformLocation(self.program, "u_draw_len")
        self.u_gap_len_loc = glGetUniformLocation(self.program, "u_gap_len")


class TestShader(BaseShader):
    def __init__(self):
        super().__init__(name="dash")


class Shaders:
    dash: tp.ClassVar[DashShader]
    test: tp.ClassVar[TestShader]

    @staticmethod
    def init_shaders() -> None:
        Shaders.dash = DashShader()
        Shaders.test = TestShader()
