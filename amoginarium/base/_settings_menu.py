"""
amoginarium/base/_settings.py

Project: amoginarium
"""

from typing import Literal

from ..settings import Settings
from ..ui import Rectangle


##################################################
#                     Code                       #
##################################################

class SettingsMenu(Rectangle):
    def __init__(self) -> None:
        super().__init__((0.5, 0.5), (0.9, 0.9))

    def gl_draw(self) -> None:
        super().gl_draw()
