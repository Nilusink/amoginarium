"""
Fast tuple basic math operations.

| Path: amoginarium/shared/utility/_tuplemath.pyi
| Project: amoginarium
| Created: 03.04.2026
| Authors: LukasKrah
"""

from typing import Any, TypeVar

T = TypeVar("T", bound=tuple[Any, ...])

class _TupleMath:
    def add(self, t1: T, t2: T) -> T: ...
    def sub(self, t1: T, t2: T) -> T: ...
    def mul(self, t1: T, t2: T) -> T: ...
    def div(self, t1: T, t2: T) -> T: ...

TupleMath: _TupleMath
