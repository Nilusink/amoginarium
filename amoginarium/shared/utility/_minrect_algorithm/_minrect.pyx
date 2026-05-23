# distutils: language=c++
# cython: boundscheck=False, wraparound=False
"""
Algorythm for finding minimum rectangles.

| Path: amoginarium/shared/utility/_minrect_algorithm/_minrect.pyx
| Project: amoginarium
| Created: 31.03.2026
| Authors: LukasKrah
"""
from libcpp.vector cimport vector

import pulp


# --- Fast C-Level Structs ---
cdef struct Point:
    int r
    int c

cdef struct Rect:
    int r1
    int c1
    int r2
    int c2

cpdef list find_minimum_rectangles(list bitmap):
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

    # 2. Extract 1s using C++ Points
    cdef vector[Point] ones
    cdef Point p
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                p.r = r
                p.c = c
                ones.push_back(p)

    if ones.empty(): return []

    # 3. Generate Valid Candidate Rectangles (The O(N^4) bottleneck)
    cdef vector[Rect] candidates
    cdef Rect rect
    cdef int r1, c1, r2, c2, rr, cc
    cdef bint is_valid

    for r1 in range(rows):
        for c1 in range(cols):
            if grid[r1][c1] == 1:
                for r2 in range(r1, rows):
                    for c2 in range(c1, cols):
                        is_valid = True
                        for rr in range(r1, r2 + 1):
                            for cc in range(c1, c2 + 1):
                                if grid[rr][cc] == 0:
                                    is_valid = False
                                    break
                            if not is_valid:
                                break
                        if is_valid:
                            rect.r1 = r1
                            rect.c1 = c1
                            rect.r2 = r2
                            rect.c2 = c2
                            candidates.push_back(rect)

    # 4. Pre-calculate Coverage Matrix in C++ Memory
    cdef vector[vector[int]] coverage
    coverage.resize(ones.size())
    cdef int i, j

    for i in range(ones.size()):
        for j in range(candidates.size()):
            if candidates[j].r1 <= ones[i].r <= candidates[j].r2 and candidates[j].c1 <= ones[i].c <= candidates[j].c2:
                coverage[i].push_back(j)

    # 5. --- Standard Python Space for Pulp ILP ---
    prob = pulp.LpProblem("Minimum_Rectangular_Partition", pulp.LpMinimize)

    # Extract C++ candidates back into Python tuples
    cdef list py_candidates = [
        (candidates[j].r1, candidates[j].c1, candidates[j].r2, candidates[j].c2)
        for j in range(candidates.size())
    ]

    x = [pulp.LpVariable(f"rect_{idx}", cat=pulp.LpBinary) for idx in range(candidates.size())]
    prob += pulp.lpSum(x)

    # Map the pre-calculated C++ coverage arrays directly to Pulp constraints
    for i in range(ones.size()):
        covering_rects = [x[idx] for idx in coverage[i]]
        prob += pulp.lpSum(covering_rects) == 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # 6. Extract Result
    cdef list chosen_rectangles = []
    for j in range(candidates.size()):
        if pulp.value(x[j]) is not None and pulp.value(x[j]) > 0.5:
            chosen_rectangles.append(py_candidates[j])

    return chosen_rectangles
