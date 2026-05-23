"""
OpenGL Font Rendering.

| Path: amoginarium/graphics/render_bindings/opengl_fonts/_opengl_fonts.pyx
| Project: amoginarium
| Created: 03.04.2026
| Authors: LukasKrah
"""

import OpenGL.GL as GL
import pygame as pg


# Define a pure C struct to hold character data.
# This prevents Python object overhead during rendering.
cdef struct Glyph:
    bint active
    float w, h
    float u1, v1, u2, v2

# Declare the class as an extension type (cdef class)
cdef class GLFont:
    cdef:
        Glyph[128] chars       # Fixed C-array for ASCII 0-127
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
            char = chr(i)
            # Render white text with transparent background
            surf = font.render(char, True, (255, 255, 255))
            glyph_surfs[char] = surf
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

        for char, surf in glyph_surfs.items():
            x = col * max_w
            y = row * max_h
            atlas_surf.blit(surf, (x, y))

            w = surf.get_width()
            h = surf.get_height()

            # Store UV mapping for OpenGL directly into the C array
            ascii_val = ord(char)
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

    cpdef void draw(self, str text, float x, float y, float scale=1.0, object color=None):
        """Draws the text using glTranslate to match the engine's coordinate style."""
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_id)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glTranslatef(x, y, 0)

        cdef float r, g, b, a
        if color is not None:
            try:
                GL.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)
            except AttributeError:
                r = color[0] / 255.0
                g = color[1] / 255.0
                b = color[2] / 255.0
                a = color[3] / 255.0 if len(color) > 3 else 1.0
                GL.glColor4f(r, g, b, a)
        else:
            GL.glColor4f(1.0, 1.0, 1.0, 1.0)

        GL.glBegin(GL.GL_QUADS)

        cdef float start_x = 0.0
        cdef float cursor_x = 0.0
        cdef float cursor_y = 0.0
        
        cdef str char
        cdef int ascii_val
        cdef float w, h, u1, v1, u2, v2

        for char in text:
            if char == '\n':
                cursor_x = start_x
                cursor_y += self.line_height * scale
                continue

            ascii_val = ord(char)
            if ascii_val >= 128 or not self.chars[ascii_val].active:
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

            cursor_x += w  # Move cursor forward for the next letter

        GL.glEnd()
        GL.glDisable(GL.GL_TEXTURE_2D)

        # Reset color
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
