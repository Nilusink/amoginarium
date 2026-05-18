"""
Class decorator for visualizing UI element bounding boxes and anchors.

Path: amoginarium/graphics/ui/_debug.py
Project: amoginarium
Created: 25.03.2026
Authors: LukasKrah
"""

import functools
import typing as tp

from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared.utility import TupleMath

T = tp.TypeVar("T", bound=type)


def draw_debug_bounds[T: type](cls: T) -> T:
    """
    Class decorator for UIElements. Automatically draws the center,
    corners, and bounding lines after the standard _gl_draw is called.
    """
    # Grab the original drawing method from the class
    original_gl_draw = cls._gl_draw

    @functools.wraps(original_gl_draw)
    def _wrapped_gl_draw(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        # 1. Execute the standard UI drawing code first
        original_gl_draw(self, *args, **kwargs)

        # 2. Draw Center (Red)
        renderer.draw_circle(
            self.center.absolute_global,
            radius=10,
            color=(255, 0, 0),
            num_segments=16,
            convert_global=False,
        )

        # 3. Draw Corners (Green)
        for point in [
            self.top_left,
            self.top_right,
            self.bottom_left,
            self.bottom_right,
        ]:
            renderer.draw_circle(
                point.absolute_global,
                radius=10,
                color=(0, 255, 0),
                num_segments=16,
                convert_global=False,
            )

        # 4. Draw Edges (Blue)
        tl_xy = self.top_left.absolute_global.xy

        # Top Edge
        renderer.draw_line(
            tl_xy,
            TupleMath.add(tl_xy, (self.width.absolute, 0)),
            (0, 0, 255),
            convert_global=False,
        )

        # Left Edge
        renderer.draw_line(
            tl_xy,
            TupleMath.add(tl_xy, (0, self.height.absolute)),
            (0, 0, 255),
            convert_global=False,
        )

        # Bottom Edge (Added to complete the box)
        renderer.draw_line(
            self.bottom_left.absolute_global.xy,
            TupleMath.add(
                self.bottom_left.absolute_global.xy, (self.width.absolute, 0)
            ),
            (0, 0, 255),
            convert_global=False,
        )

        # Right Edge (Added to complete the box)
        renderer.draw_line(
            self.top_right.absolute_global.xy,
            TupleMath.add(self.top_right.absolute_global.xy, (0, self.height.absolute)),
            (0, 0, 255),
            convert_global=False,
        )

    # Replace the class's _gl_draw with our wrapped version
    cls._gl_draw = _wrapped_gl_draw
    return cls
