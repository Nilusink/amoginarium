"""
amoginarium/ui/_animated_value.py

Project: amoginarium
"""
from __future__ import annotations

from typing import Literal, Tuple, Union, Sequence

from ..shared import global_vars


##################################################
#                     Code                       #
##################################################

class Animation:
    __start: float
    __end: float
    __extend_duration: float
    __reduce_duration: float

    __current_value: float
    __phase: Literal["at_start", "extending", "reducing", "at_end"]

    __anim_start_value: float
    __anim_start_time: float

    def __init__(self, start: float, end: float, extend_duration: float, reduce_duration: float) -> None:
        self.__start = start
        self.__end = end
        self.__extend_duration = extend_duration
        self.__reduce_duration = reduce_duration

        # Fixed: Initialize to start value instead of 0
        self.__current_value = start
        self.__phase = "at_start"

    def start_extend(self) -> None:
        self.__anim_start_value = self.__current_value

        # Fixed: Prevent ZeroDivisionError if start and end are identical
        if self.__start == self.__end:
            progress = 1.0
        else:
            progress = (self.__anim_start_value - self.__start) / (self.__end - self.__start)

        self.__anim_start_time = global_vars.time - (self.__extend_duration * progress)
        self.__phase = "extending"

    def start_reduce(self) -> None:
        self.__anim_start_value = self.__current_value

        # Fixed: Prevent ZeroDivisionError if start and end are identical
        if self.__start == self.__end:
            progress = 1.0
        else:
            progress = (self.__end - self.__anim_start_value) / (self.__end - self.__start)

        self.__anim_start_time = global_vars.time - (self.__reduce_duration * progress)
        self.__phase = "reducing"

    def __calc(self) -> None:
        if self.__phase == "at_start" or self.__phase == "at_end":
            return

        current_relative: float = 1.0
        full_scale = (self.__end - self.__start)

        if self.__phase == "extending":
            delta_since_start: float = global_vars.time - self.__anim_start_time

            if delta_since_start > self.__extend_duration:
                self.__phase = "at_end"
                self.__current_value = self.__end
                return

            if self.__extend_duration > 0:
                current_relative = delta_since_start / self.__extend_duration

            self.__current_value = self.__start + full_scale * current_relative

        elif self.__phase == "reducing":
            delta_since_start: float = global_vars.time - self.__anim_start_time

            if delta_since_start > self.__reduce_duration:
                self.__phase = "at_start"
                self.__current_value = self.__start
                return

            if self.__reduce_duration > 0:
                current_relative = delta_since_start / self.__reduce_duration

            self.__current_value = self.__end - full_scale * current_relative

    def update(self) -> float:
        self.__calc()
        return self.__current_value

    def get_value(self) -> float:
        return self.__current_value


# Helper type for the inputs: accepts a single number or a sequence of numbers
AnimInput = Union[float, int, Sequence[Union[float, int]]]


class MultiAnimation:
    __anims: Tuple[Animation, ...]
    __is_single: bool
    __count: int

    def __init__(
            self,
            start: AnimInput,
            end: AnimInput,
            extend_duration: AnimInput,
            reduce_duration: AnimInput,
            count: int | None = None
    ) -> None:
        # Check if all inputs are single scalar values
        all_scalar = all(
            isinstance(x, (int, float))
            for x in (start, end, extend_duration, reduce_duration)
        )

        # Optimization: Use one animation if only scalars are given but multiple are needed
        if all_scalar and count is not None and count > 1:
            self.__is_single = True
            self.__count = count
            self.__anims = (
                Animation(float(start), float(end), float(extend_duration), float(reduce_duration)),
            )
        else:
            self.__is_single = False

            # Extract all arguments that are sequences (tuples or lists)
            sequences = [
                x for x in (start, end, extend_duration, reduce_duration)
                if isinstance(x, (tuple, list))
            ]

            if sequences:
                # Check that all sequences have the exact same length
                seq_length = len(sequences[0])
                if any(len(seq) != seq_length for seq in sequences):
                    raise ValueError("All provided sequences must have the exact same length.")

                # Optional: ensure an explicitly passed count doesn't conflict with sequence lengths
                if count is not None and count != seq_length:
                    raise ValueError(
                        f"Provided count ({count}) does not match the length "
                        f"of the provided sequences ({seq_length})."
                    )

                self.__count = seq_length
            else:
                # Fallback if no sequences were found but it wasn't caught by the all_scalar optimization
                self.__count = count if count is not None else 1

            # Helper function to normalize scalar values into sequences of the correct length
            def _normalize(val: AnimInput) -> Tuple[float, ...]:
                if isinstance(val, (int, float)):
                    return (float(val),) * self.__count
                return tuple(float(v) for v in val)

            s_norm = _normalize(start)
            e_norm = _normalize(end)
            ex_norm = _normalize(extend_duration)
            red_norm = _normalize(reduce_duration)

            # Create individual animations for each index
            self.__anims = tuple(
                Animation(s_norm[i], e_norm[i], ex_norm[i], red_norm[i])
                for i in range(self.__count)
            )

    def start_extend(self) -> None:
        for anim in self.__anims:
            anim.start_extend()

    def start_reduce(self) -> None:
        for anim in self.__anims:
            anim.start_reduce()

    def update(self) -> Tuple[float, ...]:
        if self.__is_single:
            val = self.__anims[0].update()
            return (val,) * self.__count

        return tuple(anim.update() for anim in self.__anims)

    def get(self) -> Tuple[float, ...]:
        if self.__is_single:
            val = self.__anims[0].get_value()
            return (val,) * self.__count

        return tuple(anim.get_value() for anim in self.__anims)

    def debug(self) -> None:
        for anim in self.__anims:
            anim.debug()
