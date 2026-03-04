"""
_basegame.py
25. January 2024

Defines the core game

Author:
Nilusink
"""
from traceback import format_exc
from icecream import ic
import typing as tp
import inspect


from ._console_colors import CC, get_fg_color, terminal_link
from ._utils import get_caller_name


def run_with_debug(
    show_call: bool = True,
    show_finish: bool = False,
    show_args: bool = False,
    on_fail: tp.Callable[[Exception], tp.Any] = ...,
    reraise_errors: bool = False
):
    """
    run a function with debugging and exception printing
    """
    def decorator[**A, R](func: tp.Callable[A, R]):
        def wrapper(*args: A.args, **kwargs: A.kwargs) -> R:
            # get caller name
            prefix = ic.prefix()
            prefix_time = prefix[:-3]
            prefix_arrow = prefix[-3:]

            func_name = func.__name__  # terminal_link(
            #     inspect.getfile(func),
            #     func.__name__
            # )

            if ic.enabled and show_call:
                print(
                    f"{get_fg_color(36)}{prefix_time}"
                    f"{get_fg_color(247)}{prefix_arrow}{CC.fg.GREEN}"
                    f"running {CC.fg.MAGENTA}{func_name}"
                    f"{get_fg_color(36)}, called by {CC.fg.MAGENTA}"
                    f"{get_caller_name()}{get_fg_color(36)}" +
                    (f" with {args, kwargs}" if show_args else "") +
                    f"{CC.ctrl.ENDC}"
                )

            # execute function
            try:
                val = func(*args, **kwargs)

                if ic.enabled and show_finish:
                    print(
                        f"{get_fg_color(36)}{prefix_time}"
                        f"{get_fg_color(247)}{prefix_arrow}{CC.fg.GREEN}"
                        f"finished {CC.fg.MAGENTA}{func_name}"
                        f"{CC.ctrl.ENDC}"
                    )

                return val

            # log caught errors
            except Exception as e:
                if ic.enabled:
                    print(
                        f"{get_fg_color(36)}{prefix_time}"
                        f"{get_fg_color(247)}{prefix_arrow}{CC.fg.RED}"
                        f"{'':#>5} exception in {CC.fg.YELLOW}"
                        f"\"{func.__name__}\"{CC.fg.RED} {'':#<5}\n"
                        f"{format_exc()}{CC.ctrl.ENDC}"
                    )

                if on_fail is not ...:
                    on_fail(e)

                if reraise_errors:
                    raise e

        return wrapper
    return decorator
