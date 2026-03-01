"""
_utils.py
22. March 2024

generally useful functions

Author:
Nilusink
"""
from icecream import ic
import inspect

from ._console_colors import get_fg_color, CC


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

    prefix = ic.prefix
    if not isinstance(prefix, str):
        prefix = prefix()

    prefix_time = prefix[:-3]
    prefix_arrow = prefix[-3:]

    vals = []
    for v in values:
        if not isinstance(v, str):
            v = v.__repr__()

        vals.append(v)

    value = sep.join(vals)

    print(
        f"{get_fg_color(36)}{prefix_time}"
        f"{get_fg_color(247)}{prefix_arrow}" +
        f"{value}" +
        f"{CC.ctrl.ENDC}"
    )
