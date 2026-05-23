"""
Algorythm for finding minimum rectangles without a perfect result but way faster.

| Path: amoginarium/shared/utility/_minrect_algorithm/_minrect_dirty.pyi
| Project: amoginarium
| Created: 13.04.2026
| Authors: LukasKrah
"""

def find_minimum_rectangles_dirty(
    bitmap: list[list[int]],
) -> list[tuple[int, int, int, int]]:
    """
    Finds the minimum number of non-overlapping rectangles to cover all 1s in a 2D bitmap.
    """
