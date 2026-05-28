"""
OpenGl Fonts.

| ``Path``: amoginarium/graphics/render_bindings/opengl_fonts/_opengl_fonts.pyi
| ``Project``: amoginarium
| ``Created``: 03.04.2026
| ``Authors``: LukasKrah
"""

from amoginarium.shared.utility import Color

class GLFont:
    tex_id: int
    line_height: float

    def __init__(
        self, font_name: str, size: int, bold: bool = False, italic: bool = False
    ) -> None: ...
    def get_dimensions(self, text: str, scale: float = 1.0) -> tuple[float, float]: ...
    def draw(
        self,
        text: str,
        x: float,
        y: float,
        color: Color,
        *,
        scale: float = 1.0,
        line_height: float = 1.0,
    ) -> None: ...
