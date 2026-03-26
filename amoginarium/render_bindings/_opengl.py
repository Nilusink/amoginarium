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
from OpenGL.GL import glAlphaFunc, GL_GREATER, glColorMask, GL_TRUE
from OpenGL.GL import glPushMatrix, glPopMatrix
from OpenGL.GLU import gluOrtho2D
from pygame.locals import DOUBLEBUF, OPENGL
from icecream import ic
from PIL import Image
import pygame as pg
import typing as tp
import numpy as np
import math as m

from ..logic import Vec2, Color, convert_coord, normalize_angle
from ._base_renderer import BaseRenderer, tColor
from ..shared import global_vars

# define types
type TextureID = int


class OpenGLRenderer(BaseRenderer):
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

    def init(self, title):
        ic("using OpenGL backend")

        pg.font.init()

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
        global_vars.max_fps = max(pg.display.get_desktop_refresh_rates())

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
    def set_color(color: Color | tColor) -> Color:
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

    @staticmethod
    def check_out_of_screen(
            pos,
            size,
    ) -> bool:
        """
        check if a rect is on the screen
        """
        # pos = convert_coord(pos, Vec2)
        # size = convert_coord(size, Vec2)

        return False

        # 200 for buffering
        # return any([
        #     pos.x > global_vars.screen_size.x + 200,
        #     pos.x + size.x < -200
        # ])

    @staticmethod
    def load_texture(
            image,
            size=None,
            mirror=""
    ) -> tuple[TextureID, tuple[int, int]]:
        # for debugging
        if size is not None:
            image = image.resize(
                convert_coord(size, int),
                resample=Image.NEAREST
            )

        if "x" in mirror:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # Flip the image vertically (since OpenGL's origin is at bottom-left)
        if "y" not in mirror:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        width, height = image.size[0], image.size[1]
        img_data = image.convert("RGBA").tobytes("raw", "RGBA", 0, -1)

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data
        )
        glEnable(GL_TEXTURE_2D)

        return texture_id, (width, height)

    # @staticmethod
    def draw_textured_quad(
            self,
            texture_id: TextureID,
            pos,
            size,
            convert_global=True,
            rotate_angle=0,
            rotate_anchor: Vec2 | tuple[float, float] = ...
    ):
        """
        :param texture_id: texture id
        :param pos: position (top left)
        :param size: size (width, height)
        :param convert_global: whether to convert the texture to global coords
        :param rotate_angle: angle to rotate the image at
        :param rotate_anchor: at what pixel to rotate at
        """
        pos = convert_coord(pos, Vec2)
        size = convert_coord(size, Vec2)
        if rotate_anchor is ...:
            rotate_anchor = size / 2

        else:
            rotate_anchor = convert_coord(rotate_anchor, Vec2)

        # convert to screen relative coords and size
        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            size = global_vars.translate_scale(size)
            rotate_anchor = global_vars.translate_scale(rotate_anchor)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(pos, size):
            return

        # reset color
        glColor3f(1, 1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glTranslate(*pos.xy, 0)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # rotate
        if rotate_angle != 0:
            glTranslated(rotate_anchor.x, rotate_anchor.y, 0)
            glRotated(rotate_angle, 0, 0, 1)  # rotate around Z
            glTranslated(-rotate_anchor.x, -rotate_anchor.y, 0)

        glBegin(GL_QUADS)

        # draw rectangle and texture
        glVertex(0, 0, 0)
        glTexCoord2f(0, 0)
        glVertex(size.x, 0, 0)
        glTexCoord2f(0, 1)
        glVertex(size.x, size.y, 0)
        glTexCoord2f(1, 1)
        glVertex(0, size.y, 0)
        glTexCoord2f(1, 0)

        glEnd()
        glDisable(GL_TEXTURE_2D)
        glFlush()
        glPopMatrix()

        # self.draw_circle(pos + rotate_anchor, 4, 4, (1, .5, 0))

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

    @staticmethod
    def start_stencil(show_stencil=False):
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

    @staticmethod
    def enable_stencil(show_stencil=False):
        """
        start_stencil must be called first
        """
        if not show_stencil:
            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

        glStencilMask(0x00)
        glStencilFunc(GL_EQUAL, 1, 0xFF)

    def disable_stencil(self) -> None:
        glDisable(GL_STENCIL_TEST)
        glStencilMask(0xFF)
        glStencilFunc(GL_ALWAYS, 0, 0xFF)

    def draw_polygon(
            self,
            vertices,
            color,
            center=None,
            convert_global=True
    ):
        vertices = [convert_coord(v, Vec2) for v in vertices]

        if convert_global:
            if center:
                vertices = [
                    global_vars.translate_scale(v) for v in vertices
                ]

            else:
                vertices = [
                    global_vars.translate_screen_coord(v) for v in vertices
                ]

        glPushMatrix()  # reset previous glTranslate statements
        if center is not None:
            center = convert_coord(center, Vec2)
            if convert_global:
                center = global_vars.translate_screen_coord(center)

            glTranslate(center.x, center.y, 0)

        self.set_color(color)

        glBegin(GL_POLYGON)

        for vertice in vertices:
            glVertex2f(*vertice.xy)

        glEnd()
        glPopMatrix()

    def draw_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            convert_global=True,
    ):
        center = convert_coord(center, Vec2)

        # convert to screen realtive coords and size
        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius, 0)):
            return

        glPushMatrix()  # reset previous glTranslate statements
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        glBegin(GL_POLYGON)

        for i in range(num_segments):
            cosine = radius * np.cos(i * 2 * np.pi / num_segments)
            sine = radius * np.sin(i * 2 * np.pi / num_segments)
            glVertex2f(cosine, sine)

        glEnd()
        glPopMatrix()

    def draw_line_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            thickness=1,
            convert_global=True,
    ):
        center = convert_coord(center, Vec2)

        # convert to screen realtive coords and size
        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius, 0)):
            return

        glPushMatrix()  # reset previous glTranslate statements
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        glBegin(GL_TRIANGLE_STRIP)

        inner = radius
        outer = radius + thickness

        angle_step = 2 * np.pi / num_segments
        for i in range(num_segments + 1):
            angle = i * angle_step
            c = np.cos(angle)
            s = np.sin(angle)

            glVertex2f(outer * c, outer * s)
            glVertex2f(inner * c, inner * s)

        glEnd()
        glPopMatrix()

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
        center = convert_coord(center, Vec2)
        angle_start = convert_coord(angle_start, Vec2)
        angle_end = convert_coord(angle_end, Vec2)

        # convert to screen relative coords and size
        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius, 0)):
            return

        angle_delta = (
                normalize_angle(angle_end.angle)
                - normalize_angle(angle_start.angle)
        )

        glPushMatrix()  # reset previous glTranslate statements
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        glBegin(GL_POLYGON)
        glVertex2f(0, 0)

        for i in range(num_segments + 1):
            angle = angle_start.angle + (i / num_segments) * angle_delta
            pos = Vec2().from_polar(
                angle,
                radius
            )
            glVertex2f(*pos.xy)

        glEnd()
        glPopMatrix()

    def draw_rect(
            self,
            start,
            size,
            color,
            convert_global=True
    ):
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(start, size):
            return

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        glPushMatrix()  # reset previous glTranslate statements
        glTranslate(start.x, start.y, 0)

        self.set_color(color)

        glBegin(GL_POLYGON)
        glVertex2f(0, 0)
        glVertex2f(size.x, 0)
        glVertex2f(size.x, size.y)
        glVertex2f(0, size.y)
        glEnd()
        glPopMatrix()

    def draw_dashed_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            thickness=1,
            convert_global=True
    ):
        center = convert_coord(center, Vec2)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius + thickness, 0)):
            return

        glPushMatrix()
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        for i in range(num_segments):
            i1 = i * 2
            i2 = i1 + 1

            cosine1 = np.cos(i1 * 2 * np.pi / num_segments)
            sine1 = np.sin(i1 * 2 * np.pi / num_segments)

            cosine2 = np.cos(i2 * 2 * np.pi / num_segments)
            sine2 = np.sin(i2 * 2 * np.pi / num_segments)

            glBegin(GL_POLYGON)
            glVertex2f(cosine1 * radius, sine1 * radius)
            glVertex2f(
                cosine1 * (radius + thickness),
                sine1 * (radius + thickness)
            )
            glVertex2f(
                cosine2 * (radius + thickness),
                sine2 * (radius + thickness)
            )
            glVertex2f(cosine2 * radius, sine2 * radius)
            glEnd()

        glPopMatrix()

    def draw_partial_dashed_circle(
            self,
            center,
            radius,
            angle_start,
            angle_end,
            num_segments,
            color,
            thickness=1,
            convert_global=True
    ):
        center = convert_coord(center, Vec2)
        angle_start = convert_coord(angle_start, Vec2)
        angle_end = convert_coord(angle_end, Vec2)
        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius + thickness, 0)):
            return

        angle_delta = normalize_angle(
            angle_end.angle - angle_start.angle
        ) / 2

        glPushMatrix()
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        for i in range(num_segments):
            i1 = i * 2
            i2 = i1 + 1

            angle1 = angle_start.angle + (i1 / num_segments) * angle_delta
            angle2 = angle_start.angle + (i2 / num_segments) * angle_delta

            pos1 = Vec2().from_polar(
                angle1,
                1
            )
            pos2 = Vec2().from_polar(
                angle2,
                1
            )

            glBegin(GL_POLYGON)
            glVertex2f(*(pos1 * radius).xy)
            glVertex2f(*(pos1 * (radius + thickness)).xy)
            glVertex2f(*(pos2 * (radius + thickness)).xy)
            glVertex2f(*(pos2 * radius).xy)
            glEnd()

        glPopMatrix()

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
        start = convert_coord(start, Vec2)
        end = convert_coord(end, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            end = global_vars.translate_screen_coord(end)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(start, end - start):
            return

        if global_position:
            glPushMatrix()  # reset previous glTranslate statements

        self.set_color(color)

        glBegin(GL_LINES)
        glVertex2f(*start.xy)
        glVertex2f(*end.xy)
        glEnd()

        if global_position:
            glPopMatrix()

    def draw_thick_line(
            self,
            start,
            end,
            color,
            thickness=1.0,
            global_position=True,
            convert_global=True
    ):
        """
        draw a line with thickness using a quad
        """
        start = convert_coord(start, Vec2)
        end = convert_coord(end, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            end = global_vars.translate_screen_coord(end)

        direction = end - start

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(start, direction):
            return

        if global_position:
            glPushMatrix()

        self.set_color(color)

        # normalize perpendicular
        length = direction.length
        if length == 0:
            return

        dir_norm = direction / length

        # perpendicular vector (rotate 90°)
        perp = Vec2().from_cartesian(-dir_norm.y, dir_norm.x)

        # half thickness offset
        offset = perp * (thickness * 0.5)

        # quad corners
        v1 = start + offset
        v2 = start - offset
        v3 = end - offset
        v4 = end + offset

        glBegin(GL_QUADS)
        glVertex2f(*v1.xy)
        glVertex2f(*v2.xy)
        glVertex2f(*v3.xy)
        glVertex2f(*v4.xy)
        glEnd()

        if global_position:
            glPopMatrix()

    def draw_rounded_rect(
            self,
            start,
            size,
            color,
            radius,
            convert_global=True
    ) -> None:
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)

        if OpenGLRenderer.check_out_of_screen(start, size):
            return

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        glPushMatrix()
        glTranslate(start.x, start.y, 0)
        self.set_color(color)

        # Prevent radius from breaking if it is larger than the rect
        radius = min(radius, size.x / 2, size.y / 2)

        # Adjust smoothness based on the radius
        segments = max(4, int(radius / 2))

        glBegin(GL_POLYGON)

        # Top-Left Arc
        for i in range(segments + 1):
            angle = m.pi + (i / segments) * (m.pi / 2)
            glVertex2f(radius + m.cos(angle) * radius, radius + m.sin(angle) * radius)

        # Top-Right Arc
        for i in range(segments + 1):
            angle = 1.5 * m.pi + (i / segments) * (m.pi / 2)
            glVertex2f(size.x - radius + m.cos(angle) * radius, radius + m.sin(angle) * radius)

        # Bottom-Right Arc
        for i in range(segments + 1):
            angle = 0.0 + (i / segments) * (m.pi / 2)
            glVertex2f(size.x - radius + m.cos(angle) * radius, size.y - radius + m.sin(angle) * radius)

        # Bottom-Left Arc
        for i in range(segments + 1):
            angle = 0.5 * m.pi + (i / segments) * (m.pi / 2)
            glVertex2f(radius + m.cos(angle) * radius, size.y - radius + m.sin(angle) * radius)

        glEnd()

        glPopMatrix()

    def draw_rounded_border(
            self,
            start,
            size,
            color,
            radius,
            border_width,
            convert_global=True
    ) -> None:
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)

        if OpenGLRenderer.check_out_of_screen(start, size):
            return

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        glPushMatrix()
        glTranslate(start.x, start.y, 0)
        self.set_color(color)

        radius = min(radius, size.x / 2, size.y / 2)
        inner_radius = max(0, radius - border_width)
        segments = max(4, int(radius / 2))

        glBegin(GL_TRIANGLE_STRIP)

        # Helper to generate the outer and inner vertices for the ring
        def add_arc(cx, cy, start_angle, end_angle):
            for i in range(segments + 1):
                angle = start_angle + (i / segments) * (end_angle - start_angle)
                glVertex2f(cx + m.cos(angle) * radius, cy + m.sin(angle) * radius)             # Outer
                glVertex2f(cx + m.cos(angle) * inner_radius, cy + m.sin(angle) * inner_radius) # Inner

        # Trace the perimeter
        add_arc(radius, radius, m.pi, 1.5 * m.pi)                   # Top-Left
        add_arc(size.x - radius, radius, 1.5 * m.pi, 2.0 * m.pi)    # Top-Right
        add_arc(size.x - radius, size.y - radius, 0.0, 0.5 * m.pi)  # Bottom-Right
        add_arc(radius, size.y - radius, 0.5 * m.pi, m.pi)          # Bottom-Left

        # Connect back to the very first vertices to seal the loop seamlessly
        glVertex2f(radius + m.cos(m.pi) * radius, radius + m.sin(m.pi) * radius)
        glVertex2f(radius + m.cos(m.pi) * inner_radius, radius + m.sin(m.pi) * inner_radius)

        glEnd()

        glPopMatrix()

    def draw_border(
            self,
            start,
            size,
            color,
            border_width,
            convert_global=True
    ) -> None:
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)

        if OpenGLRenderer.check_out_of_screen(start, size):
            return

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        glPushMatrix()
        glTranslate(start.x, start.y, 0)
        self.set_color(color)

        bw = border_width

        glBegin(GL_TRIANGLE_STRIP)

        # Trace the hollow frame (Outer vertex, Inner vertex)
        glVertex2f(0, 0)
        glVertex2f(bw, bw)

        glVertex2f(size.x, 0)
        glVertex2f(size.x - bw, bw)

        glVertex2f(size.x, size.y)
        glVertex2f(size.x - bw, size.y - bw)

        glVertex2f(0, size.y)
        glVertex2f(bw, size.y - bw)

        # Close the loop
        glVertex2f(0, 0)
        glVertex2f(bw, bw)

        glEnd()

        glPopMatrix()

    def draw_text(
            self,
            pos,
            text,
            color,
            bg_color,
            centered=False,
            font_size=64,
            font_family="arial",
            bold=False,
            italic=False,
            convert_global=True
    ):
        if not isinstance(bg_color, Color):
            bg_color = self.set_color(bg_color)
        if not isinstance(color, Color):
            color = self.set_color(color)

        pos = convert_coord(pos, Vec2)

        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            font_size = global_vars.translate_scale(font_size)

        # weird conversion because pygame is ass
        text_surface: pg.Surface = self.generate_pg_surf_text(
            text, color, bg_color, font_size, font_family, bold, italic
        )
        # text_surface.set_alpha(color.a)

        # draw text
        self.draw_pg_surf(pos, text_surface, centered)

        return text_surface.get_size()

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

    def draw_pg_surf(self, pos, surface, centered=False, convert_global=True):
        pos = convert_coord(pos, Vec2)

        pos = convert_coord(pos, Vec2)

        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            # font_size = global_vars.translate_scale(font_size)

        text_data = pg.image.tostring(surface, "RGBA", True)
        text_size: tuple[int, int] = surface.get_size()

        pos.y = global_vars.screen_size.y - pos.y

        pos.x = (pos.x / global_vars.screen_size_fac_x) + global_vars.screen_size_offset_x
        pos.y = (pos.y / global_vars.screen_size_fac_y) + global_vars.screen_size_offset_y

        if centered:
            pos.x -= text_size[0] / 2
            pos.y -= text_size[1] / 2

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(pos, text_size):
            return

        glWindowPos2d(*pos.xy)
        glDrawPixels(
            surface.get_width(),
            surface.get_height(),
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            text_data
        )
