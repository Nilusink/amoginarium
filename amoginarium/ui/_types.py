"""
amoginarium/entities/_ui/_ui_types.py

Project: amoginarium
"""

from typing import Literal, Union

anchor_t = Literal["nw", "center"]

ui_color_t = Union[tuple[int, int, int], tuple[int, int, int, int]]  # Temporary solution
