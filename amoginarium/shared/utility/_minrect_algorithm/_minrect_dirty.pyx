# distutils: language=c++
# cython: boundscheck=False, wraparound=False, cdivision=True
"""
Algorythm for finding minimum rectangles without a perfect result but way faster.

| ``Path``: amoginarium/shared/utility/_minrect_algorithm/_minrect_dirty.pyx
| ``Project``: amoginarium
| ``Created``: 13.04.2026
| ``Authors``: LukasKrah
"""

from libcpp.vector cimport vector


# --- Fast C-Level Struct ---
cdef struct Rect:
    int r1
    int c1
    int r2
    int c2

cpdef object find_minimum_rectangles_dirty(list bitmap):
    """
    Greedy heuristic to find near-minimum rectangles, heavily optimized in C++.
    Finds the largest available rectangle, marks it, and repeats.
    """
    cdef int rows = len(bitmap)
    if rows == 0: return []
    cdef int cols = len(bitmap[0])
    if cols == 0: return []

    # 1. Convert Python List to C++ Vector for raw memory speed
    cdef vector[vector[int]] grid
    cdef vector[int] row_vec
    cdef int r, c

    for r in range(rows):
        row_vec.clear()
        for c in range(cols):
            row_vec.push_back(bitmap[r][c])
        grid.push_back(row_vec)

    # 2. Setup C++ variables for the greedy algorithm
    cdef vector[Rect] rectangles
    cdef int best_area, area
    cdef Rect best_rect
    cdef int r1, c1, r2, c2, max_c2

    # 3. Main Greedy Loop (Runs entirely in C++)
    while True:
        best_area = 0
        best_rect.r1 = -1

        # Scan for the largest possible rectangle of 1s
        for r1 in range(rows):
            for c1 in range(cols):
                if grid[r1][c1] == 1:
                    max_c2 = cols - 1
                    for r2 in range(r1, rows):
                        # Hit a 0 going down, cannot grow taller
                        if grid[r2][c1] == 0:
                            break

                        # Find the max valid width for this height
                        for c2 in range(c1, max_c2 + 1):
                            if grid[r2][c2] == 0:
                                max_c2 = c2 - 1
                                break

                        area = (r2 - r1 + 1) * (max_c2 - c1 + 1)
                        if area > best_area:
                            best_area = area
                            best_rect.r1 = r1
                            best_rect.c1 = c1
                            best_rect.r2 = r2
                            best_rect.c2 = max_c2

        # If area is 0, no 1s are left on the board
        if best_area == 0:
            break

        # Save the best rectangle found in this pass
        rectangles.push_back(best_rect)

        # "Erase" the covered 1s by mutating the grid directly in memory
        for r in range(best_rect.r1, best_rect.r2 + 1):
            for c in range(best_rect.c1, best_rect.c2 + 1):
                grid[r][c] = 0

    # 4. Extract C++ Rect structs back into a Python list of tuples
    cdef list chosen_rectangles = []
    cdef int i
    for i in range(rectangles.size()):
        chosen_rectangles.append((
            rectangles[i].r1,
            rectangles[i].c1,
            rectangles[i].r2,
            rectangles[i].c2
        ))

    return chosen_rectangles
