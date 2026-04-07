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


if __name__ == "__main__":
    print(bin(MASK64))
    print(bin(MASK32))
    print(bin(MASK16))
