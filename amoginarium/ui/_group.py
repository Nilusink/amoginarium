"""
amoginarium/entities/_ui/_ui_group.py

Project: amoginarium
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
        print("NEW GROUP")
