"""
amoginarium/entities/_ui/_ui_group.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from ..entities import _BaseGroup

from ..debugging import run_with_debug


##################################################
#                     Code                       #
##################################################

class UIGroup(_BaseGroup):
    @run_with_debug()
    def __init__(self) -> None:
        super().__init__()
