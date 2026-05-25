"""
OpenGL renderer implementation using shaders.

| ``Path``: amoginarium/graphics/render_bindings/_opengl_shader.py
| ``Project``: amoginarium
| ``Created``: 08.04.2026
| ``Authors``: LukasKrah
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic
from OpenGL.GL import GL_FLOAT, GL_QUADS, GL_TRIANGLE_FAN, GL_VERTEX_ARRAY, glBegin
from OpenGL.GL import glDisableClientState, glDrawArrays, glEnableClientState
from OpenGL.GL import glEnd, glPopMatrix, glPushMatrix, glTranslate, glUniform1f
from OpenGL.GL import glUniform4f, glUseProgram, glVertex2f, glVertexPointer

from amoginarium.shared.debugging import cum_timer
from amoginarium.shared.utility import convert_coord, Vec2

from ... import pv
from ._opengl import OpenGLRenderer
from .opengl_shaders import Shaders

if TYPE_CHECKING:
    from amoginarium.shared.utility import Color, coord_t

    from ._base_renderer import tColor

# define types


# noinspection DuplicatedCode
class OpenGLShaderRenderer(OpenGLRenderer):
    # region Init & Loading
    def init(self, title: str) -> None:
        """
        Initialize the renderer and global_vars
        :param title: Window title.
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
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a dashed circle line with point_num_segments segments
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param num_segments: Number of segments. Every second segment is drawn
        :param color: Drawing color
        :param draw_len: Number of segments to draw before leaving a gap
        :param gap_len: Number of segments left out by a gap
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)
            thickness = pv.global_vars.translate_scale(thickness)

        outer: float = radius + thickness

        if offscreen_check and self._check_out_of_screen(
            (center_vec2.x - outer, center_vec2.y - outer), (outer * 2, outer * 2)
        ):
            return

        # Ensure color is safely unpacked to 4 floats
        if hasattr(color, "rgba1"):
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
            self._draw_debug_bounds(
                center_vec2, (radius * 2, radius * 2), centered=True
            )

    def test_shader(self) -> None:
        # 1. Use the shader program
        Shaders.test.use()

        # 2. Define a simple quad (2 triangles) covering the screen or a specific area
        # Format: x, y
        vertices = [
            -1.0,
            -1.0,  # Bottom Left
            1.0,
            -1.0,  # Bottom Right
            1.0,
            1.0,  # Top Right
            -1.0,
            1.0,  # Top Left
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
