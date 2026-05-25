"""
Defines the core game.

| ``Path``: amoginarium/shared/debugging/_decoators.py
| ``Project``: amoginarium
| ``Created``: 25.01.2024
| ``Authors``: Nilusink, LukasKrah
"""
# ruff: noqa: T201

import typing as tp
from time import perf_counter_ns
from traceback import format_exc

from icecream import ic

from ._console_colors import CC, get_fg_color
from ._utils import get_caller_name


def run_with_debug(
    show_call: bool = True,
    show_finish: bool = False,
    show_args: bool = False,
    on_fail: tp.Callable[[Exception], tp.Any] = ...,
    reraise_errors: bool = False,
):
    """
    Run a function with debugging and exception printing.
    """

    def decorator[**A, R](func: tp.Callable[A, R]):
        def wrapper(*args: A.args, **kwargs: A.kwargs) -> R:
            # get caller name
            prefix = ic.prefix
            if not isinstance(prefix, str):
                prefix = prefix()

            prefix_time = prefix[:-3]
            prefix_arrow = prefix[-3:]

            func_name = func.__name__  # terminal_link(
            #     inspect.getfile(func),
            #     func.__name__
            # )

            if ic.enabled and show_call:
                context = get_caller_name(True)
                ic.outputFunction(
                    f"{get_fg_color(36)}{prefix_time}"
                    f"{get_fg_color(247)}{prefix_arrow}{CC.fg.GREEN}"
                    f"running {CC.fg.MAGENTA}{func_name}"
                    f"{get_fg_color(36)}, called by {CC.fg.MAGENTA}"
                    f'{context["function"]}{get_fg_color(247)} in File "'
                    f'{context["file"]}", line {CC.fg.MAGENTA}{context["line"]}'
                    f"{get_fg_color(36)}"
                    + (f" with {args, kwargs}" if show_args else "")
                    + f"{CC.ctrl.ENDC}",
                    color=False,
                )

            # execute function
            try:
                val = func(*args, **kwargs)

                if ic.enabled and show_finish:
                    ic.outputFunction(
                        f"{get_fg_color(36)}{prefix_time}"
                        f"{get_fg_color(247)}{prefix_arrow}{CC.fg.GREEN}"
                        f"finished {CC.fg.MAGENTA}{func_name}"
                        f"{CC.ctrl.ENDC}",
                        color=False,
                    )

                return val

            # log caught errors
            except Exception as e:
                if ic.enabled:
                    print(
                        f"{get_fg_color(36)}{prefix_time}"
                        f"{get_fg_color(247)}{prefix_arrow}{CC.fg.RED}"
                        f"{'':#>5} exception in {CC.fg.YELLOW}"
                        f'"{func.__name__}"{CC.fg.RED} {"":#<5}\n'
                        f"{format_exc()}{CC.ctrl.ENDC}"
                    )

                if on_fail is not ...:
                    on_fail(e)

                if reraise_errors:
                    raise

        return wrapper

    return decorator


def timeit(times_run: int):
    def decorator[**A, R](func: tp.Callable[A, R]):
        def wrapper(*args: A.args, **kwargs: A.kwargs) -> R:
            start = perf_counter_ns()
            for _ in range(times_run - 1):
                func(*args, **kwargs)

            result = func(*args, **kwargs)
            end = perf_counter_ns()
            time_taken = (end - start) / (times_run * 1000)

            prefix = ic.prefix()
            prefix_time = prefix[:-3]
            prefix_arrow = prefix[-3:]
            print(
                f"{get_fg_color(36)}{prefix_time}"
                f"{get_fg_color(247)}{prefix_arrow}{CC.fg.GREEN}"
                f"timing {CC.fg.MAGENTA}{func.__name__}"
                f"{get_fg_color(36)} for {get_fg_color(247)}{times_run}"
                f"{get_fg_color(36)} iterations. result: {CC.fg.MAGENTA}"
                f"{time_taken}µs{CC.ctrl.ENDC}"
            )

            return result

        return wrapper

    return decorator


class _CumTimer:
    """
    cumulative timing for all functions over one frame.
    """

    def __init__(self) -> None:
        self._func_times: dict[str, list[float | int]] = {}

    def time_this[**A, R](self, func: tp.Callable[[A], R]):
        def wrapper(*args: A.args, **kwargs: A.kwargs) -> R:
            start = perf_counter_ns()
            res = func(*args, **kwargs)
            end = perf_counter_ns()
            time_taken = (end - start) / 1000

            fname = func.__name__
            if fname not in self._func_times:
                self._func_times[fname] = [time_taken, 1]
                return res

            self._func_times[fname][0] += time_taken
            self._func_times[fname][1] += 1
            return res

        return wrapper

    def get_times(self) -> dict[str, list[float | int]]:
        """
        Get all cumulated times and reset.
        """
        out = {}
        for key in self._func_times:
            out[key] = [
                self._func_times[key][0],
                self._func_times[key][1],
                self._func_times[key][0] / self._func_times[key][1],
            ]

        self._func_times.clear()
        return out


cum_timer = _CumTimer()
