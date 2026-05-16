"""
amoginarium/render_bindings/_opengl_fonts.pyi.py

Project: amoginarium
Created: 03.04.2026
Authors: LukasKrah
"""

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
        scale: float = 1.0,
        color: object | None = None,
    ) -> None: ...
