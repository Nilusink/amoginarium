"""
/local_lookup_test.py

Project: amoginarium
Created: 06.04.2026
Authors: LukasKrah
"""


class _Test:
    call = 0

    def test(self) -> int:
        return self.call


Test = _Test()


def run():
    test = Test.test
    for _ in range(10_000_000):
        a = Test.test()


from time import perf_counter_ns

t1 = perf_counter_ns()
run()
t2 = perf_counter_ns()

print("TOOK", (t2 - t1) / 1e6, "ms")
