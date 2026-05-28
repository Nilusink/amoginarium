"""
OpenGL Font Rendering.

| ``Path``: amoginarium/graphics/render_bindings/opengl_fonts/_opengl_fonts.pyx
| ``Project``: amoginarium
| ``Created``: 03.04.2026
| ``Authors``: LukasKrah
"""

import OpenGL.GL as GL
import pygame as pg

from libc.stdint cimport uint8_t
from mpl_toolkits.axes_grid1 import axes_size

from amoginarium.shared.utility._ccolor cimport Color
from ...sound_effect import PresetGraphicsSoundEffect


# Define a pure C struct to hold character data.
# This prevents Python object overhead during rendering.
cdef struct Glyph:
    bint active
    float w, h
    float u1, v1, u2, v2


cdef struct term_color_t:
    float r
    float g
    float b


cdef list base = [
    (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
    (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
    (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
    (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
]


cpdef tuple ansi_256_to_rgb(uint8_t x):
    if x < 16:
        # standard ANSI colors (simplified xterm set)
        r, g, b = base[x]

    elif x < 232:
        x -= 16
        r = (x // 36) % 6
        g = (x // 6) % 6
        b = x % 6

        # scale 0–5 → 0–255
        r = 55 + r * 40 if r else 0
        g = 55 + g * 40 if g else 0
        b = 55 + b * 40 if b else 0

    else:
        # grayscale ramp
        v = 8 + (x - 232) * 10
        r = g = b = v

    return r / 255.0, g / 255.0, b / 255.0


cdef uint8_t NORMAL = 0
cdef uint8_t ESC = 1
cdef uint8_t CSI = 2


class TerminalBell(PresetGraphicsSoundEffect):
    _sound_name = "error_attention"


# Declare the class as an extension type (cdef class)
cdef class GLFont:
    cdef:
        Glyph[128] chars       # Fixed C-array for ASCII 0-127
        term_color_t[10] term_colors
        public int tex_id
        public float line_height

    def __init__(self, str font_name, int size, bint bold=False, bint italic=False):
        if not pg.font.get_init():
            pg.font.init()

        # Initialize the Pygame font
        font = pg.font.SysFont(font_name, size, bold=bold, italic=italic)

        self.tex_id = GL.glGenTextures(1)

        # 0. Initialize all C structs to inactive
        cdef int i
        for i in range(128):
            self.chars[i].active = False

        # 1. Render all ASCII glyphs to individual surfaces to find max dimensions
        glyph_surfs = {}
        cdef float max_w = 0.0
        cdef float max_h = 0.0

        cdef str char
        # ASCII 32 (space) to 126 (~) covers standard English characters
        for i in range(32, 127):
            character = chr(i)
            # Render white text with transparent background
            surf = font.render(character, True, (255, 255, 255))
            glyph_surfs[character] = surf
            max_w = max(max_w, surf.get_width())
            max_h = max(max_h, surf.get_height())

        self.line_height = max_h

        # 2. Create the master Atlas surface
        cdef int cols = 10
        cdef int rows = 10
        cdef float atlas_w = cols * max_w
        cdef float atlas_h = rows * max_h
        atlas_surf = pg.Surface((int(atlas_w), int(atlas_h)), pg.SRCALPHA)

        # 3. Blit characters onto the Atlas and calculate their OpenGL UV coordinates
        cdef int col = 0
        cdef int row = 0
        cdef float x, y, w, h
        cdef int ascii_val

        for character, surf in glyph_surfs.items():
            x = col * max_w
            y = row * max_h
            atlas_surf.blit(surf, (x, y))

            w = surf.get_width()
            h = surf.get_height()

            # Store UV mapping for OpenGL directly into the C array
            ascii_val = ord(character)
            if ascii_val < 128:
                self.chars[ascii_val].active = True
                self.chars[ascii_val].w = w
                self.chars[ascii_val].h = h
                self.chars[ascii_val].u1 = x / atlas_w
                self.chars[ascii_val].v1 = y / atlas_h
                self.chars[ascii_val].u2 = (x + w) / atlas_w
                self.chars[ascii_val].v2 = (y + h) / atlas_h

            col += 1
            if col >= cols:
                col = 0
                row += 1

        # 4. Upload the completed Atlas to the GPU
        image_data = pg.image.tostring(atlas_surf, "RGBA", False)

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_id)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, int(atlas_w), int(atlas_h), 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, image_data)

        # create predefined colors
        self.term_colors[0] = term_color_t(0, 0, 0)  # black
        self.term_colors[1] = term_color_t(1, 0, 0)  # red
        self.term_colors[2] = term_color_t(0, 1, 0)  # green
        self.term_colors[3] = term_color_t(1, 1, 0)  # yellow
        self.term_colors[4] = term_color_t(0, 0, 1)  # blue
        self.term_colors[5] = term_color_t(1, 0, 1)  # magenta
        self.term_colors[6] = term_color_t(0, 1, 1)  # cyan
        self.term_colors[7] = term_color_t(1, 1, 1)  # white
        self.term_colors[9] = term_color_t(1, 1, 1)  # default

    cpdef tuple get_dimensions(self, str text, float scale=1.0):
        """Calculates the total width and total height of a string, including newlines."""
        cdef float max_width = 0.0
        cdef float current_width = 0.0
        cdef int lines = 1
        cdef str char
        cdef int ascii_val

        for char in text:
            if char == '\n':
                if current_width > max_width:
                    max_width = current_width
                current_width = 0.0
                lines += 1
                continue

            ascii_val = ord(char)
            if ascii_val < 128 and self.chars[ascii_val].active:
                current_width += self.chars[ascii_val].w * scale

        if current_width > max_width:
            max_width = current_width
            
        cdef float total_height = self.line_height * lines * scale

        return max_width, total_height

    cpdef void draw(
        self,
        str text,
        float x,
        float y,
        Color color,
        float scale=1.0,
        float line_height=1.0
    ):
        """Draws the text using glTranslate to match the engine's coordinate style."""
        cdef:
            int ascii_val
            float w, h, u1, v1, u2, v2

            float start_x = 0.0
            float cursor_x = 0.0
            float cursor_y = 0.0

            int params[8]
            int param_count = 0
            int current = 0
            uint8_t state = NORMAL
            bint building_number = 0
            term_color_t color_
            tuple color_t

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_id)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glPushMatrix()

        GL.glTranslatef(x, y, 0)

        GL.glColor4f(color._r1, color._g1, color._b1, color._a1)

        GL.glBegin(GL.GL_QUADS)

        for character in text:
            if character == '\n':
                cursor_x = start_x
                cursor_y += self.line_height * scale * line_height
                continue

            ascii_val = ord(character)

            # check for escape characters
            if state == NORMAL:
                if ascii_val == 27:   # ESC
                    state = ESC
                    continue

                # elif ascii_val == ord('\a'):  # alarm  # disabled cuz permanently playing
                #     TerminalBell().play()  # error sound

                # render normal char

            elif state == ESC:
                if ascii_val == ord('['):  # control sequence
                    state = CSI
                    param_count = 0
                    current = 0
                    building_number = False

                else:
                    state = NORMAL

                continue

            elif state == CSI:
                # digit
                if 48 <= ascii_val <= 57:
                    current = current * 10 + (ascii_val - 48)
                    building_number = True
                    continue

                # semicolon
                if ascii_val == ord(';'):
                    params[param_count] = current
                    param_count += 1
                    current = 0
                    building_number = False
                    continue

                # final byte (e.g. 'm')
                if ascii_val == ord('m'):
                    if building_number:
                        params[param_count] = current
                        param_count += 1

                    # set colors
                    if param_count == 1:  # normal stuff
                        if params[0] == 0:  # endc
                            GL.glColor4f(color._r1, color._g1, color._b1, color._a1)

                        elif 30 <= params[0] < 40:  # normal fg
                            color_ = self.term_colors[params[0] - 30]
                            GL.glColor4f(
                                color_.r,
                                color_.g,
                                color_.b,
                                1.0,
                            )

                    elif param_count == 2:  # highlight fg
                        if 30 <= params[0] < 40 and params[1] == 1:
                            color_ = self.term_colors[params[0] - 30]
                            GL.glColor4f(
                                color_.r,
                                color_.g,
                                color_.b,
                                1.0,
                            )

                    elif param_count == 3:
                        if params[0] == 38 and params[1] == 5:  # ansi_256 fg
                            color_t = ansi_256_to_rgb(params[2])
                            GL.glColor4f(
                                color_t[0],
                                color_t[1],
                                color_t[2],
                                1.0,
                            )

                    elif param_count == 5:
                        if params[0] == 38 and params[1] == 2:  # ansi true RGB
                            GL.glColor4f(
                                params[2] / 255.0,
                                params[3] / 255.0,
                                params[4] / 255.0,
                                1.0,
                            )

                    state = NORMAL
                    continue

                # unknown → reset
                state = NORMAL
                continue

            if ascii_val >= 128 or not self.chars[ascii_val].active:
                # checkOpenGLError()
                continue

            # Fetch properties instantly via C array
            w = self.chars[ascii_val].w * scale
            h = self.chars[ascii_val].h * scale
            u1 = self.chars[ascii_val].u1
            v1 = self.chars[ascii_val].v1
            u2 = self.chars[ascii_val].u2
            v2 = self.chars[ascii_val].v2

            # Top-Left
            GL.glTexCoord2f(u1, v1)
            GL.glVertex2f(cursor_x, cursor_y)

            # Bottom-Left
            GL.glTexCoord2f(u1, v2)
            GL.glVertex2f(cursor_x, cursor_y + h)

            # Bottom-Right
            GL.glTexCoord2f(u2, v2)
            GL.glVertex2f(cursor_x + w, cursor_y + h)

            # Top-Right
            GL.glTexCoord2f(u2, v1)
            GL.glVertex2f(cursor_x + w, cursor_y)
            # checkOpenGLError()

            cursor_x += w  # Move cursor forward for the next letter

        GL.glEnd()

        GL.glPopMatrix()

        GL.glDisable(GL.GL_TEXTURE_2D)

        # Reset color
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
