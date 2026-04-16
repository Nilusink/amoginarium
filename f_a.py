"""
/f_a.py

Project: amoginarium
Created: 15.04.2026
Authors: LukasKrah
"""
import typing

if typing.TYPE_CHECKING:
    from f_b import B

class A:
    def other(self, other: "B"):
        B.other()
