"""
/tuple_unpack_test.py

Project: amoginarium
Created: 06.04.2026
Authors: LukasKrah
"""

from time import perf_counter_ns


def test(a: tuple[int, int]):
    for _ in range(10_000_000):
        *a


t1 = perf_counter_ns()
test((5, 10))
t2 = perf_counter_ns()

print("TOOK", (t2 - t1) / 1e6)
