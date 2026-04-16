"""
/f_b.py

Project: amoginarium
Created: 15.04.2026
Authors: LukasKrah
"""

import typing

if typing.TYPE_CHECKING:
    from f_a import A

class B:
    def other(self, other: "A"):
        ...