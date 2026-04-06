"""
_opengl.py
21. March 2024

a few functions for rendering

Author:
Nilusink
"""
from OpenGL.GL import glTranslate, glMatrixMode, glLoadIdentity, glTexCoord2f
from OpenGL.GL import GL_PROJECTION, GL_SRC_ALPHA, GL_BLEND, GL_CLAMP_TO_EDGE
from OpenGL.GL import glBindTexture, glTexParameteri, glTexImage2D, glEnable
from OpenGL.GL import glGenTextures, glVertex2f, glColor3f, glColor4f, glEnd
from OpenGL.GL import GL_UNSIGNED_BYTE, GL_MODELVIEW, GL_ONE_MINUS_SRC_ALPHA
from OpenGL.GL import GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT, GL_LINES
from OpenGL.GL import GL_TEXTURE_WRAP_T, GL_TEXTURE_MIN_FILTER, GL_POLYGON
from OpenGL.GL import glDisable, glBegin, glVertex, glFlush, glClearColor
from OpenGL.GL import glBlendFunc, glWindowPos2d, glDrawPixels, glRotated
from OpenGL.GL import GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_RGBA, GL_QUADS
from OpenGL.GL import glTranslated, GL_TRIANGLE_STRIP, glStencilFunc, GL_KEEP
from OpenGL.GL import glStencilOp, glStencilMask, GL_STENCIL_TEST, GL_ALWAYS
from OpenGL.GL import GL_REPLACE, GL_EQUAL, glClear, GL_STENCIL_BUFFER_BIT
from OpenGL.GL import glGetIntegerv, GL_STENCIL_BITS, GL_ALPHA_TEST, GL_FALSE
from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glDeleteTextures
from OpenGL.GL import glEnableClientState, glDisableClientState, glVertexPointer, glDrawArrays
from OpenGL.GL import GL_VERTEX_ARRAY, GL_QUADS, GL_FLOAT
from OpenGL.GL import glEnableClientState, glDisableClientState, glVertexPointer, glDrawArrays
from OpenGL.GL import GL_VERTEX_ARRAY, GL_FLOAT
from OpenGL.GL import glAlphaFunc, GL_GREATER, glColorMask, GL_TRUE
from OpenGL.GLU import gluOrtho2D
from pygame.locals import DOUBLEBUF, OPENGL
from time import perf_counter_ns
from types import EllipsisType
from icecream import ic
from PIL import Image
import pygame as pg
import typing as tp
import numpy as np
import math as m
import random

from amoginarium.debugging import cum_timer, get_caller_name

from ..logic import Vec2, Color, convert_coord, normalize_angle, coord_t
from ._base_renderer import BaseRenderer, tColor
from ..shared import global_vars
from ._opengl_fonts import GLFont

# define types
type TextureID = int


class OpenGLRenderer(BaseRenderer):
    __fonts: dict[tuple[str, int, bool, bool], GLFont]
    __surf_cache: dict
    _fonts: dict

    @cum_timer.time_this
    def get_font(
            self,
            size: int,
            family: str,
            bold: bool = False,
            italic: bool = False
    ) -> pg.font.Font:
        # check if font exists
        if size in self._fonts:
            for font in self._fonts[size]:  # TODO: fix
                if all([
                    font.name == family,
                    font.bold == bold,
                    font.italic == italic
                ]):
                    return font

        else:
            self._fonts[size] = []

        # no font found, create new
        new_font = pg.font.SysFont(family, int(size), bold, italic)
        self._fonts[size].append(new_font)

        return new_font

    @cum_timer.time_this
    def init(self, title: str) -> None:
        ic("using OpenGL backend")

        pg.font.init()

        self.__fonts = {}
        self.__surf_cache = {}

        self._fonts = {
            32: [
                pg.font.SysFont('arial', 32)
            ],
            64: [
                pg.font.SysFont('arial', 64)
            ]
        }

        # get screen size
        screen_info = pg.display.Info()
        window_size = 1920, 1080  # (screen_info.current_w, screen_info.current_h)  # TODO: sizing

        # set global screen size and ppm
        global_vars.screen_size = Vec2().from_cartesian(*window_size)
        global_vars.screen_size_real = Vec2().from_cartesian(
            screen_info.current_w,
            screen_info.current_h
        )
        ic(global_vars.screen_size_real.xy)
        global_vars.resolution = Vec2().from_cartesian(*window_size)
        global_vars.screen_size_fac_x = 1
        global_vars.screen_size_offset_x = 0
        global_vars.screen_size_fac_y = 1
        global_vars.screen_size_offset_y = 0
        global_vars.pixel_per_meter = 1

        # set max fps to monitor refresh rate
        global_vars.max_fps = 500

        pg.display.gl_set_attribute(pg.GL_STENCIL_SIZE, 8)
        pg.display.set_mode(
            global_vars.screen_size.xy,
            DOUBLEBUF | OPENGL | pg.RESIZABLE | pg.HIDDEN
        )
        # self.font = pg.font.SysFont(None, 24)
        # request stencil buffer
        pg.display.set_caption(title)

        # initialize OpenGL stuff
        glClearColor(*(0, 0, 0, 255))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, *global_vars.screen_size.xy, 0)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    @staticmethod
    def __set_color(color: Color | tColor) -> Color:
        """
        set gColor
        """
        # color as Color class
        if isinstance(color, Color):

            glColor4f(*color.rgba1)

            return color

        # color as tuple
        else:
            if len(color) == 3:
                glColor3f(*color)

            elif len(color) == 4:
                glColor4f(*color)

            else:
                raise ValueError("Invalid color: ", color)

            return Color().from_1(*color)

    @cum_timer.time_this
    def check_out_of_screen(
            self,
            pos,
            size,
    ) -> bool:
        """
        check if a rect is on the screen
        """
        return False
        pos = convert_coord(pos)
        size = convert_coord(size)

        # return False
        # 200 for buffering
        return (
                pos[0] + size[0] < 0
                or pos[0] > global_vars.resolution.x
                or pos[1] + size[1] < 0
                or pos[1] > global_vars.resolution.y
        )

        # return any([
        #     pos.x > global_vars.screen_size.x + 200,
        #     pos.x + size.x < -200
        # ])

    @cum_timer.time_this
    def load_texture(
            self,
            image: Image.Image,
            size: coord_t | None = None,
            mirror: tp.Literal["x", "y", "xy", "yx", ""] = ""
    ) -> tuple[TextureID, tuple[int, int]]:
        if size is not None:
            if image.size != (target_size := convert_coord(size, int)):
                image = image.resize(target_size, resample=Image.Resampling.NEAREST)

        if mirror == "":
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        elif mirror == "x":
            image = image.transpose(Image.Transpose.ROTATE_180)
        elif mirror in ("xy", "yx"):
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        width, height = image.size[0], image.size[1]
        img_data = image.tobytes("raw", "RGBA", 0, -1)

        # noinspection PyArgumentList
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, width, height,
            0, GL_RGBA, GL_UNSIGNED_BYTE, img_data
        )

        return texture_id, (width, height)

    @cum_timer.time_this
    def draw_textured_quad(
            self,
            texture_id: TextureID,
            pos: coord_t,
            size: coord_t,
            convert_global: bool = True,
            rotate_angle: float = 0,
            rotate_anchor: Vec2 | tuple[float, float] | EllipsisType = ...,
            offscreen_check: bool = True
    ) -> None:
        pos: Vec2 = convert_coord(pos, Vec2)
        size: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            size = global_vars.translate_scale(size)

        if offscreen_check and self.check_out_of_screen(pos, size):
            return

        # reset color
        glColor3f(1.0, 1.0, 1.0)

        glPushMatrix()
        glTranslate(pos.x, pos.y, 0.0)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # rotate
        if rotate_angle != 0.0:
            if isinstance(rotate_anchor, EllipsisType):
                rx, ry = size.x / 2.0, size.y / 2.0
            else:
                anchor: Vec2 = convert_coord(rotate_anchor, Vec2)
                if convert_global:
                    anchor = global_vars.translate_scale(anchor)
                rx, ry = anchor.x, anchor.y

            glTranslated(rx, ry, 0.0)
            glRotated(rotate_angle, 0.0, 0.0, 1.0)
            glTranslated(-rx, -ry, 0.0)

        glBegin(GL_QUADS)

        # draw rectangle and texture
        glTexCoord2f(1.0, 0.0)
        glVertex2f(0.0, 0.0)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(size.x, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(size.x, size.y)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(0.0, size.y)

        glEnd()
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

        # self.draw_circle(pos + rotate_anchor, 4, 4, (1, .5, 0))

    @cum_timer.time_this
    def apply_stencil[**A](
            self,
            stencil_func: tp.Callable[A, tp.Any],
            show_stencil=False,
            *args: A.args,
            **kwargs: A.kwargs
    ) -> None:
        self.start_stencil(show_stencil)

        stencil_func(*args, **kwargs)

        self.enable_stencil(show_stencil)

    @cum_timer.time_this
    def start_stencil(self, show_stencil=False):
        """
        call this, then draw stencil, then draw enable_stencil
        """
        glEnable(GL_STENCIL_TEST)
        glClear(GL_STENCIL_BUFFER_BIT)

        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        glStencilMask(0xFF)

        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.01)

        if not show_stencil:
            glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)  # if mask invis

    @cum_timer.time_this
    def enable_stencil(self, show_stencil=False):
        """
        start_stencil must be called first
        """
        if not show_stencil:
            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

        glStencilMask(0x00)
        glStencilFunc(GL_EQUAL, 1, 0xFF)

    @cum_timer.time_this
    def disable_stencil(self) -> None:
        glDisable(GL_STENCIL_TEST)
        glStencilMask(0xFF)
        glStencilFunc(GL_ALWAYS, 0, 0xFF)

    @cum_timer.time_this
    def draw_polygon(
            self,
            vertices,
            color,
            center=None,
            convert_global=True
    ):
        vertices: list[Vec2] = [convert_coord(v, Vec2) for v in vertices]

        if convert_global:
            if center:
                vertices = [
                    global_vars.translate_scale(v) for v in vertices
                ]

            else:
                vertices = [
                    global_vars.translate_screen_coord(v) for v in vertices
                ]

        glPushMatrix()
        if center is not None:
            center = convert_coord(center, Vec2)
            if convert_global:
                center = global_vars.translate_screen_coord(center)

            glTranslate(center.x, center.y, 0)

        self.__set_color(color)

        glBegin(GL_POLYGON)

        for vertice in vertices:
            glVertex2f(*vertice.xy)

        glEnd()
        glPopMatrix()

    @cum_timer.time_this
    def draw_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            convert_global=True,
    ):
        center: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        if self.check_out_of_screen((center.x - radius, center.y - radius), (radius * 2, radius * 2)):
            return

        glPushMatrix()
        glTranslate(center.x, center.y, 0.0)

        self.__set_color(color)

        glBegin(GL_POLYGON)

        v2f = glVertex2f
        step = 6.283185307179586 / num_segments

        [v2f(radius * m.cos(i * step), radius * m.sin(i * step)) for i in range(num_segments)]

        glEnd()
        glPopMatrix()

    @cum_timer.time_this
    def draw_line_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            thickness=1.0,
            convert_global=True,
    ):
        center: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)
            thickness = global_vars.translate_scale(thickness)

        outer = radius + thickness
        if self.check_out_of_screen((center.x - outer, center.y - outer), (outer * 2, outer * 2)):
            return

        glPushMatrix()
        glTranslate(center.x, center.y, 0.0)

        self.__set_color(color)

        glBegin(GL_TRIANGLE_STRIP)

        inner = radius
        v2f = glVertex2f
        step = 6.283185307179586 / num_segments

        [
            (v2f(outer * c, outer * s), v2f(inner * c, inner * s))
            for i in range(num_segments + 1)
            for c in (m.cos(i * step),)
            for s in (m.sin(i * step),)
        ]

        glEnd()
        glPopMatrix()

    @cum_timer.time_this
    def draw_partial_circle(
            self,
            center,
            radius,
            angle_start,
            angle_end,
            num_segments,
            color,
            convert_global=True
    ):
        center: Vec2 = convert_coord(center, Vec2)
        angle_start: Vec2 = convert_coord(angle_start, Vec2)
        angle_end: Vec2 = convert_coord(angle_end, Vec2)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        if self.check_out_of_screen((center.x - radius, center.y - radius), (radius * 2, radius * 2)):
            return

        angle_delta = normalize_angle(angle_end.angle) - normalize_angle(angle_start.angle)

        glPushMatrix()
        glTranslate(center.x, center.y, 0.0)

        self.__set_color(color)

        glBegin(GL_POLYGON)

        v2f = glVertex2f
        v2f(0.0, 0.0)

        start_ang = angle_start.angle
        step = angle_delta / num_segments

        [v2f(radius * m.cos(start_ang + i * step), radius * m.sin(start_ang + i * step)) for i in
         range(num_segments + 1)]

        glEnd()
        glPopMatrix()

    @cum_timer.time_this
    def draw_rect(
            self,
            start,
            size,
            color,
            convert_global=True
    ):
        start: Vec2 = convert_coord(start, Vec2)
        size: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        if self.check_out_of_screen(start, size):
            return

        glPushMatrix()
        glTranslate(start.x, start.y, 0.0)

        self.__set_color(color)

        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(size.x, 0.0)
        glVertex2f(size.x, size.y)
        glVertex2f(0.0, size.y)
        glEnd()
        glPopMatrix()

    @cum_timer.time_this
    def draw_dashed_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            thickness=1.0,
            convert_global=True
    ):
        center = convert_coord(center, Vec2)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)
            thickness = global_vars.translate_scale(thickness)

        outer = radius + thickness

        if self.check_out_of_screen((center.x - outer, center.y - outer), (outer * 2, outer * 2)):
            return

        glPushMatrix()
        glTranslate(center.x, center.y, 0.0)

        self.__set_color(color)

        step = 6.283185307179586 / num_segments
        indices = np.arange(num_segments, dtype=np.float32)

        angles1 = indices * (2 * step)
        angles2 = angles1 + step

        c1 = np.cos(angles1)
        s1 = np.sin(angles1)
        c2 = np.cos(angles2)
        s2 = np.sin(angles2)

        vertices = np.empty((num_segments, 4, 2), dtype=np.float32)

        vertices[:, 0, 0] = radius * c1
        vertices[:, 0, 1] = radius * s1

        vertices[:, 1, 0] = outer * c1
        vertices[:, 1, 1] = outer * s1

        vertices[:, 2, 0] = outer * c2
        vertices[:, 2, 1] = outer * s2

        vertices[:, 3, 0] = radius * c2
        vertices[:, 3, 1] = radius * s2

        # 3. Send to GPU in ONE single call
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glDrawArrays(GL_QUADS, 0, num_segments * 4)
        glDisableClientState(GL_VERTEX_ARRAY)

        glPopMatrix()

    @cum_timer.time_this
    def draw_partial_dashed_circle(
            self,
            center,
            radius,
            angle_start,
            angle_end,
            num_segments,
            color,
            thickness=1.0,
            convert_global=True
    ):
        center: Vec2 = convert_coord(center, Vec2)
        angle_start: Vec2 = convert_coord(angle_start, Vec2)
        angle_end: Vec2 = convert_coord(angle_end, Vec2)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)
            thickness = global_vars.translate_scale(thickness)  # Fixed bug

        outer = radius + thickness

        if self.check_out_of_screen((center.x - outer, center.y - outer),
                                    (outer * 2, outer * 2)):
            return

        glPushMatrix()
        glTranslate(center.x, center.y, 0.0)

        self.__set_color(color)

        # 1. Vectorized NumPy Math
        # Extract the raw float angles
        start_ang = angle_start.angle

        # Matches your original math
        angle_delta = normalize_angle(angle_end.angle - start_ang) / 2.0

        indices = np.arange(num_segments, dtype=np.float32)

        # Calculate all start and end angles for the dashes at once
        angles1 = start_ang + ((indices * 2) / num_segments) * angle_delta
        angles2 = start_ang + ((indices * 2 + 1) / num_segments) * angle_delta

        # Compute all sines and cosines simultaneously
        c1 = np.cos(angles1)
        s1 = np.sin(angles1)
        c2 = np.cos(angles2)
        s2 = np.sin(angles2)

        # 2. Build the memory array (num_segments, 4 vertices per quad, 2 coordinates)
        vertices = np.empty((num_segments, 4, 2), dtype=np.float32)

        vertices[:, 0, 0] = radius * c1
        vertices[:, 0, 1] = radius * s1

        vertices[:, 1, 0] = outer * c1
        vertices[:, 1, 1] = outer * s1

        vertices[:, 2, 0] = outer * c2
        vertices[:, 2, 1] = outer * s2

        vertices[:, 3, 0] = radius * c2
        vertices[:, 3, 1] = radius * s2

        # 3. Send to GPU
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glDrawArrays(GL_QUADS, 0, num_segments * 4)
        glDisableClientState(GL_VERTEX_ARRAY)

        glPopMatrix()

    @cum_timer.time_this
    def draw_line(
            self,
            start,
            end,
            color,
            global_position=True,
            convert_global=True
    ):
        """
        draw a simple line
        """
        start: Vec2 = convert_coord(start, Vec2)
        end: Vec2 = convert_coord(end, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            end = global_vars.translate_screen_coord(end)

        # only draw if on screen
        if self.check_out_of_screen(start, end - start):
            print("SKIP LINE", get_caller_name(True))
            return

        if global_position:
            glPushMatrix()  # reset previous glTranslate statements

        self.__set_color(color)

        glBegin(GL_LINES)
        glVertex2f(start.x, start.y)
        glVertex2f(end.x, end.y)
        glEnd()

        if global_position:
            glPopMatrix()

    @cum_timer.time_this
    def draw_thick_line(
            self,
            start,
            end,
            color,
            thickness=1.0,
            global_position=True,
            convert_global=True
    ):
        start: Vec2 = convert_coord(start, Vec2)
        end: Vec2 = convert_coord(end, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            end = global_vars.translate_screen_coord(end)
            thickness = global_vars.translate_scale(thickness)

        sx = start.x
        sy = start.y
        ex = end.x
        ey = end.y

        dx = ex - sx
        dy = ey - sy

        if self.check_out_of_screen((sx, sy), (dx, dy)):
            return

        length = m.hypot(dx, dy)
        if length == 0.0:
            return

        self.__set_color(color)

        if global_position:
            glPushMatrix()

        half_thick = thickness * 0.5
        off_x = (-dy / length) * half_thick
        off_y = (dx / length) * half_thick

        glBegin(GL_QUADS)
        glVertex2f(sx + off_x, sy + off_y)
        glVertex2f(sx - off_x, sy - off_y)
        glVertex2f(ex - off_x, ey - off_y)
        glVertex2f(ex + off_x, ey + off_y)
        glEnd()

        if global_position:
            glPopMatrix()

    @cum_timer.time_this
    def draw_rounded_rect(
            self,
            start,
            size,
            color,
            radius,
            convert_global=True
    ) -> None:
        start_vec: Vec2 = convert_coord(start, Vec2)
        size_vec: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start_vec = global_vars.translate_screen_coord(start_vec)
            size_vec = global_vars.translate_scale(size_vec)
            radius = global_vars.translate_scale(radius)

        sx = size_vec.x
        sy = size_vec.y

        if self.check_out_of_screen(start_vec, size_vec):
            return

        glPushMatrix()
        glTranslate(start_vec.x, start_vec.y, 0.0)
        self.__set_color(color)

        rad = min(radius, sx / 2.0, sy / 2.0)
        segments = max(4, int(rad / 2.0))

        # Calculate the base arc (0 to 90 degrees) EXACTLY once
        step = 1.5707963267948966 / segments  # pi / 2
        base_arc = [
            (m.cos(i * step) * rad, m.sin(i * step) * rad)
            for i in range(segments + 1)
        ]

        glBegin(GL_POLYGON)
        v2f = glVertex2f

        [v2f(rad - x, rad - y) for x, y in base_arc]
        [v2f(sx - rad + y, rad - x) for x, y in base_arc]
        [v2f(sx - rad + x, sy - rad + y) for x, y in base_arc]
        [v2f(rad - y, sy - rad + x) for x, y in base_arc]

        glEnd()
        glPopMatrix()

    # noinspection DuplicatedCode
    @cum_timer.time_this
    def draw_rounded_border(
            self,
            start,
            size,
            color,
            radius,
            border_width,
            convert_global=True
    ) -> None:
        start: Vec2 = convert_coord(start, Vec2)
        size: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)
            radius = global_vars.translate_scale(radius)
            border_width = global_vars.translate_scale(border_width)

        if self.check_out_of_screen(start, size):
            return

        glPushMatrix()
        glTranslate(start.x, start.y, 0.0)
        self.__set_color(color)

        rad = min(radius, size.x / 2.0, size.y / 2.0)
        inner_rad = max(0.0, rad - border_width)
        segments = max(4, int(rad / 2.0))

        glBegin(GL_TRIANGLE_STRIP)

        v2f = glVertex2f
        cos = m.cos
        sin = m.sin

        step = 1.5707963267948966 / segments

        cx, cy = rad, rad
        start_a = m.pi
        for i in range(segments + 1):
            a = start_a + i * step
            c = cos(a)
            s = sin(a)
            v2f(cx + c * rad, cy + s * rad)
            v2f(cx + c * inner_rad, cy + s * inner_rad)

        cx = size.x - rad
        start_a = 4.71238898038469
        for i in range(segments + 1):
            a = start_a + i * step
            c = cos(a)
            s = sin(a)
            v2f(cx + c * rad, cy + s * rad)
            v2f(cx + c * inner_rad, cy + s * inner_rad)

        cy = size.y - rad
        for i in range(segments + 1):
            a = i * step
            c = cos(a)
            s = sin(a)
            v2f(cx + c * rad, cy + s * rad)
            v2f(cx + c * inner_rad, cy + s * inner_rad)

        cx = rad
        start_a = 1.5707963267948966
        for i in range(segments + 1):
            a = start_a + i * step
            c = cos(a)
            s = sin(a)
            v2f(cx + c * rad, cy + s * rad)
            v2f(cx + c * inner_rad, cy + s * inner_rad)

        v2f(0.0, rad)
        v2f(rad - inner_rad, rad)

        glEnd()
        glPopMatrix()

    @cum_timer.time_this
    def draw_border(
            self,
            start,
            size,
            color,
            border_width,
            convert_global=True
    ) -> None:
        start_vec = convert_coord(start, Vec2)
        size_vec = convert_coord(size, Vec2)

        if convert_global:
            start_vec = global_vars.translate_screen_coord(start_vec)
            size_vec = global_vars.translate_scale(size_vec)
            border_width = global_vars.translate_scale(border_width)

        sx = size_vec.x
        sy = size_vec.y

        if self.check_out_of_screen(start_vec, size_vec):
            return

        glPushMatrix()
        glTranslate(start_vec.x, start_vec.y, 0.0)
        self.__set_color(color)

        bw = border_width

        # Pre-calculate the inner boundaries
        ix = sx - bw
        iy = sy - bw

        glBegin(GL_TRIANGLE_STRIP)

        # Localize function for faster lookup
        v2f = glVertex2f

        # Trace the hollow frame (Outer vertex, Inner vertex)
        v2f(0.0, 0.0)
        v2f(bw, bw)

        v2f(sx, 0.0)
        v2f(ix, bw)

        v2f(sx, sy)
        v2f(ix, iy)

        v2f(0.0, sy)
        v2f(bw, iy)

        # Close the loop
        v2f(0.0, 0.0)
        v2f(bw, bw)

        glEnd()

        glPopMatrix()

    @cum_timer.time_this
    def draw_text(
            self,
            pos,
            text,
            color=(255, 255, 255),
            bg_color=(0, 0, 0, 0),
            centered=False,
            font_size=64,
            font_family="arial",
            bold=False,
            italic=False,
            convert_global=True
    ):
        if not isinstance(bg_color, Color):
            bg_color = self.__set_color(bg_color)
        if not isinstance(color, Color):
            color = self.__set_color(color)

        pos: Vec2 = convert_coord(pos, Vec2)

        # 1. Handle scaling natively via OpenGL to save memory
        scale = 1.0
        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            scale = global_vars.translate_scale(1.0)

        font_key = (font_family, font_size, bold, italic)

        if font_key not in self.__fonts:
            self.__fonts[font_key] = GLFont(font_family, font_size, bold, italic)

        font = self.__fonts[font_key]

        text_width, text_height = font.get_dimensions(text, scale)

        if centered:
            pos.x -= text_width / 2
            pos.y -= text_height / 2

        if bg_color.a255 > 0:
            self.draw_rect(pos.xy, (text_width, text_height), bg_color, convert_global)

        glPushMatrix()
        font.draw(text, pos.x, pos.y, scale, color.rgba255)
        glPopMatrix()

        return text_width, text_height

    @cum_timer.time_this
    def generate_pg_surf_text(
            self,
            text,
            color,
            bg_color,
            font_size=64,
            font_family="arial",
            bold=False,
            italic=False,
            convert_global=True
    ):
        return self.get_font(
            font_size,
            font_family,
            bold,
            italic
        ).render(
            text,
            True,
            color.rgba255,
            bg_color.rgba255 if bg_color.a255 > 125 else None
        )

    @cum_timer.time_this
    def draw_pg_surf(
            self,
            pos,
            surface: pg.Surface,
            centered=False,
            scale=1.0,
            convert_global=True,
            is_dynamic=False
    ):
        pos: Vec2 = convert_coord(pos, Vec2)
        w, h = surface.get_size()

        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            scale = global_vars.translate_scale(scale)

        scaled_w = w * scale
        scaled_h = h * scale

        px = pos.x
        py = pos.y

        if centered:
            px -= scaled_w * 0.5
            py -= scaled_h * 0.5

        if self.check_out_of_screen((px, py), (scaled_w, scaled_h)):
            return

        surf_id = id(surface)

        if not is_dynamic and surf_id in self.__surf_cache:
            tex_id = self.__surf_cache[surf_id]
        else:
            text_data = pg.image.tobytes(surface, "RGBA", False)
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

            if not is_dynamic:
                self.__surf_cache[surf_id] = tex_id

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, tex_id)

        glPushMatrix()
        glTranslatef(px, py, 0.0)
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(0.0, 0.0)

        glTexCoord2f(0.0, 1.0)
        glVertex2f(0.0, scaled_h)

        glTexCoord2f(1.0, 1.0)
        glVertex2f(scaled_w, scaled_h)

        glTexCoord2f(1.0, 0.0)
        glVertex2f(scaled_w, 0.0)
        glEnd()

        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

        if is_dynamic:
            glDeleteTextures(1, [tex_id])
