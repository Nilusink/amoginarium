"""
_constants.py
01.04.2026

constant values reused in the program

Author:
Nilusink
"""

import numpy as np

SQ2 = np.sqrt(2)
MASK16 = 0b1111111111111111
MASK32 = MASK16 | MASK16 << 16
MASK64 = MASK32 | MASK32 << 32

PI = np.pi
PI_2 = PI / 2
PI_4 = PI / 4
PI_3_4 = PI_4 * 3
M_2_PI = 2 * PI

RTD = 180 / PI
DTR = PI / 180


__all__ = (
    "SQ2",
    "MASK16",
    "MASK32",
    "MASK64",
    "PI",
    "PI_2",
    "PI_4",
    "PI_3_4",
    "M_2_PI",
    "RTD",
    "DTR",
)


if __name__ == "__main__":
    print(bin(MASK64))
    print(bin(MASK32))
    print(bin(MASK16))
