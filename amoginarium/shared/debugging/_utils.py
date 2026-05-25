"""
Generally useful functions.

| ``Path``: amoginarium/shared/debugging/_utils.py
| ``Project``: amoginarium
| ``Created``: 22.03.2024
| ``Authors``: Nilusink, LukasKrah
"""

import inspect

from icecream import colorize, ic, stderrPrint, supportTerminalColorsInWindows

from ._console_colors import CC, get_fg_color


def print_with_prefix(content: str, prefix: str = "", *, color: bool = True) -> None:
    """StderrPrint with prefix and togglable colorization."""
    if color:
        content = colorize(content)

    with supportTerminalColorsInWindows():
        stderrPrint(prefix + get_fg_color(247) + content + CC.ctrl.ENDC)


def get_caller_name(*, extended: bool = False) -> str | dict:
    """
    Get the name of the function that called this context.
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


def print_ic_style(
    *values,
    sep=" ",
    error: bool = False,
    warning: bool = False,
) -> None:
    """Print like ic but without colors."""
    if not ic.enabled:
        return

    vals = []
    for v in values:
        if not isinstance(v, str):
            v = repr(v)

        vals.append(v)

    value = sep.join(vals)

    if error:
        value = CC.fg.RED + value

    elif warning:
        value = CC.fg.YELLOW + value

    ic.outputFunction(f"{value}" + f"{CC.ctrl.ENDC}", color=False)
