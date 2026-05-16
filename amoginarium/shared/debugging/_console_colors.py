"""
_console_colors.py
25. January 2024

defines a few console colors

Author:
Nilusink
"""

import os
import typing as tp


class BetterDict:
    """
    each element is also accessible with instance.element
    """

    def __init__(self, **initial) -> None:
        for key, value in initial.items():
            setattr(self, key, value)

    def __setitem__(self, key: str, value: tp.Any) -> None:
        setattr(self, key, value)

    def __getitem__(self, item: str) -> tp.Any:
        return self.__dict__[item]

    def __delitem__(self, key) -> None:
        delattr(self, key)


if os.name == "nt":
    os.system("color")

CC = BetterDict(
    ctrl=BetterDict(
        ENDC="\033[0m",
        BOLD="\033[1m",
        FAINT="\033[2m",
        ITALIC="\033[3m",
        UNDERLINE="\033[4m",
        SLOW_BLINK="\033[5m",
        RAPID_BLINK="\033[6m",
        INVERSE="\033[7m",
        CONCEAL="\033[8m",
        CROSSED="\033[9m",
        FRAKTUR="\033[20",
        NORMAL1="\033[22",  # neither bold nor faint
        NORMAL2="\033[23",  # neither italic nor fraktur
        UNDERLINE_OFF="\033[24",
        BLINK_OFF="\033[25",
        INVERSE_OFF="\033[26",
        REVEAL="\033[27",
        CROSSED_OFF="\033[28",
    ),
    fg=BetterDict(
        BLACK="\u001b[30m",
        RED="\u001b[31m",
        GREEN="\u001b[32m",
        YELLOW="\u001b[33m",
        BLUE="\u001b[34m",
        MAGENTA="\u001b[35m",
        CYAN="\u001b[36m",
        WHITE="\u001b[37m",
        DEFAULT="\u001b[39m",
    ),
    bfg=BetterDict(
        BLACK="\u001b[30;1m",
        RED="\u001b[31;1m",
        GREEN="\u001b[32;1m",
        YELLOW="\u001b[33;1m",
        BLUE="\u001b[34;1m",
        MAGENTA="\u001b[35;1m",
        CYAN="\u001b[36;1m",
        WHITE="\u001b[37;1m",
    ),
    bg=BetterDict(
        BLACK="\u001b[40m",
        RED="\u001b[41m",
        GREEN="\u001b[42m",
        YELLOW="\u001b[43m",
        BLUE="\u001b[44m",
        MAGENTA="\u001b[45m",
        CYAN="\u001b[46m",
        WHITE="\u001b[47m",
        DEFAULT="\u001b[49m",
    ),
    bbg=BetterDict(
        BLACK="\u001b[40;1m",
        RED="\u001b[41;1m",
        GREEN="\u001b[42;1m",
        YELLOW="\u001b[43;1m",
        BLUE="\u001b[44;1m",
        MAGENTA="\u001b[45;1m",
        CYAN="\u001b[46;1m",
        WHITE="\u001b[47;1m",
    ),
    special=BetterDict(
        FRAMED="\u001b[51m",
        ENCIRCLED="\u001b[52m",
        OVERLINED="\u001b[53m",
        NORMAL1="\u001b[54m",  # not framed or circled
        NORMAL2="\u001b[55m",  # not overlined
    ),
)


def get_fg_color(n: int) -> str:
    """
    Standard background color where n can be a number between 0-7
    High intensity background color where n can be a number between 8-15
    Rainbow background color where n can be a number between 16-231
    Gray background color where n can be a number between 232-255
    """
    return f"\u001b[38;5;{n}m"


def terminal_link(uri, label=None):
    if label is None:
        label = uri

    parameters = ""

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"

    return escape_mask.format(parameters, uri, label)


if __name__ == "__main__":

    def p():
        t = 1243.1251
        t1, t2 = str(t).split(".")

        return f"(logic: {os.getpid()}) {t1: >4}.{t2: <4} |> "

    for i in range(8, 16):
        print(f"{get_fg_color(i)}x")

    # ic.configureOutput(prefix=p)
    # ic("hellow")
