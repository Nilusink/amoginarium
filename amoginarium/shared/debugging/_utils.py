"""
_utils.py
22. March 2024

generally useful functions

Author:
Nilusink
"""
from icecream import ic, stderrPrint, colorize, supportTerminalColorsInWindows
import inspect

from ._console_colors import get_fg_color, CC


def print_with_prefix(content: str, prefix: str = "", color: bool = True) -> None:
    if color:
        content = colorize(content)

    with supportTerminalColorsInWindows():
        stderrPrint(prefix + get_fg_color(247) +  content + CC.ctrl.ENDC)


def get_caller_name(extended: bool = False) -> str | dict:
    """
    get the name of the function that called this context
    """
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)

    if not extended:
        return calframe[2][3]

    return {
        "file": calframe[2][1],
        "line": calframe[2][2],
        "function": calframe[2][3],
        "context": calframe[2][4],
    }


def print_ic_style(*values, sep=" ") -> None:
    if not ic.enabled:
        return

    vals = []
    for v in values:
        if not isinstance(v, str):
            v = v.__repr__()

        vals.append(v)

    value = sep.join(vals)

    ic.outputFunction(f"{value}" + f"{CC.ctrl.ENDC}")
