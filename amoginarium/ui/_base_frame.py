"""
amoginarium/ui/_base_frame.py

Project: amoginarium
"""


##################################################
#                    Imports                     #
##################################################

##################################################
#                     Code                       #
##################################################

class BaseFrame:
    def gl_draw(self) -> None:
        raise NotImplementedError
