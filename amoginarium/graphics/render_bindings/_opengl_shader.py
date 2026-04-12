"""
amoginarium/render_bindings/_opengl_shader.py

Project: amoginarium
Created: 07.04.2026
Authors: LukasKrah
"""
from OpenGL.GL import glTranslate, glMatrixMode, glLoadIdentity, glTexCoord2f
from OpenGL.GL import GL_PROJECTION, GL_SRC_ALPHA, GL_BLEND, GL_CLAMP_TO_EDGE
from OpenGL.GL import glBindTexture, glTexParameteri, glTexImage2D, glEnable
from OpenGL.GL import glGenTextures, glVertex2f, glColor3f, glColor4f, glEnd
from OpenGL.GL import GL_UNSIGNED_BYTE, GL_ONE_MINUS_SRC_ALPHA
from OpenGL.GL import GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT, GL_LINES
from OpenGL.GL import GL_TEXTURE_WRAP_T, GL_TEXTURE_MIN_FILTER, GL_POLYGON
from OpenGL.GL import glDisable, glBegin, glClearColor, GL_TRIANGLE_FAN
from OpenGL.GL import glBlendFunc, glRotated, GL_NEAREST, glUseProgram
from OpenGL.GL import GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_RGBA, glUniform1f
from OpenGL.GL import glTranslated, GL_TRIANGLE_STRIP, glStencilFunc, GL_KEEP
from OpenGL.GL import glStencilOp, glStencilMask, GL_STENCIL_TEST, GL_ALWAYS
from OpenGL.GL import GL_REPLACE, GL_EQUAL, glClear, GL_STENCIL_BUFFER_BIT
from OpenGL.GL import GL_ALPHA_TEST, GL_FALSE, glUniform4f
from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef
from OpenGL.GL import GL_QUADS
from OpenGL.GL import glEnableClientState, glDisableClientState, glVertexPointer, glDrawArrays
from OpenGL.GL import GL_VERTEX_ARRAY, GL_FLOAT
from OpenGL.GL import glAlphaFunc, GL_GREATER, glColorMask, GL_TRUE
from OpenGL.GLU import gluOrtho2D

from pygame.locals import DOUBLEBUF, OPENGL
from types import EllipsisType
from icecream import ic
from PIL import Image
import pygame as pg
import typing as tp
import numpy as np
import math as m

from amoginarium.shared.debugging import cum_timer
from amoginarium.shared.utility import Vec2, Color, convert_coord, normalize_angle, fade, coord_t, convert_color

from ._opengl import OpenGLRenderer
from .opengl_shaders import Shaders
from ._base_renderer import tColor
from .opengl_fonts import GLFont
from ... import pv

# define types

# noinspection DuplicatedCode
class OpenGLShaderRenderer(OpenGLRenderer):
    # region Init & Loading
    def init(self, title: str) -> None:
        """
        Initialize the renderer and global_vars
        :param title: Window title
        """
        super().init(title)

        Shaders.init_shaders()

    # endregion

    # region Circles
    @cum_timer.time_this
    def draw_dashed_circle(
            self,
            center: coord_t,
            radius: float,
            num_segments: int,
            color: Color | tColor,
            *,
            draw_len: int = 1,
            gap_len: int = 1,
            thickness: int = 1,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a dashed circle line with num_segments segments
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param num_segments: Number of segments. Every second segment is drawn
        :param color: Drawing color
        :param draw_len: Number of segments to draw before leaving a gap
        :param gap_len: Number of segments left out by a gap
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)
            thickness = pv.global_vars.translate_scale(thickness)

        outer: float = radius + thickness

        if offscreen_check and self._check_out_of_screen(
                (center_vec2.x - outer, center_vec2.y - outer),
                (outer * 2, outer * 2)
        ):
            return

        # Ensure color is safely unpacked to 4 floats
        if hasattr(color, 'rgba1'):
            r, g, b, a = color.rgba1
        else:
            r, g, b = color[:3]
            a = color[3] if len(color) == 4 else 1.0

        # --- FAST RENDER LOOP ---
        glUseProgram(Shaders.dash.program)

        # Push the exact geometry boundaries to the shader
        glUniform4f(Shaders.dash.u_color_loc, r, g, b, a)
        glUniform1f(Shaders.dash.u_inner_loc, radius)
        glUniform1f(Shaders.dash.u_outer_loc, outer)
        glUniform1f(Shaders.dash.u_num_seg_loc, float(num_segments))
        glUniform1f(Shaders.dash.u_draw_len_loc, float(draw_len))
        glUniform1f(Shaders.dash.u_gap_len_loc, float(gap_len))

        glPushMatrix()
        glTranslate(center_vec2.x, center_vec2.y, 0.0)

        # For exactly 4 vertices, glBegin is faster in Python than NumPy/ctypes overhead
        glBegin(GL_QUADS)
        glVertex2f(-outer, -outer)
        glVertex2f(outer, -outer)
        glVertex2f(outer, outer)
        glVertex2f(-outer, outer)
        glEnd()

        glPopMatrix()
        glUseProgram(0)

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(center_vec2, (radius * 2, radius * 2), centered=True)

    def test_shader(self) -> None:
        # 1. Use the shader program
        Shaders.test.use()

        # 2. Define a simple quad (2 triangles) covering the screen or a specific area
        # Format: x, y
        vertices = [
            -1.0, -1.0,  # Bottom Left
            1.0, -1.0,  # Bottom Right
            1.0, 1.0,  # Top Right
            -1.0, 1.0  # Top Left
        ]

        # 3. Enable Vertex Arrays and send the data
        # In a real engine, you'd use a VBO/VAO, but for a "simple" test:
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)

        # 4. Draw the 4 vertices as a fan (rectangle)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # 5. Cleanup
        glDisableClientState(GL_VERTEX_ARRAY)
        glUseProgram(0)

    # endregion
