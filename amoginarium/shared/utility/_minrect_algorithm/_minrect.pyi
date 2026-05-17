"""
amoginarium/logic/_minrect.pyi.py

Project: amoginarium
Created: 31.03.2026
Authors: LukasKrah
"""

from typing import List, Tuple

def find_minimum_rectangles(bitmap: List[List[int]]) -> List[Tuple[int, int, int, int]]:
    """
    Finds the minimum number of non-overlapping rectangles to cover all 1s in a 2D bitmap.

    Args:
        bitmap: A 2D list of integers (0 and 1).

    Returns:
        A list of tuples representing chosen rectangles: (row_start, col_start, row_end, col_end)
    """
    ...
