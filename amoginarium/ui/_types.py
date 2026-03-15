"""
amoginarium/entities/_ui/_ui_types.py

Project: amoginarium
Created: 02.03.2026
Authors: LukasKrah
"""

import pygame as pg
import typing as tp

anchor_t = tp.Literal["nw", "center"]

ui_color_t = tp.Union[tuple[int, int, int], tuple[int, int, int, int]]  # Temporary solution
