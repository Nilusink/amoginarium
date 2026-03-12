"""
amoginarium/ui/_animated_value.py

Project: amoginarium
"""

from __future__ import annotations

from enum import Enum

import typing as tp

from ..shared import global_vars


##################################################
#                     Code                       #
##################################################

class AnimationPhase(Enum):
    """Enumeration representing the various phases of an animation."""
    AT_START = 0
    EXTENDING = 1
    STOPPED = 2
    CONTRACTING = 3
    AT_END = 4


class Animation:
    """
    Basic single float value animation
    """
    __start_value: float
    __end_value: float
    __extend_duration_seconds: float
    __reduce_duration_seconds: float

    __phase: AnimationPhase
    __current_value: float
    __current_time: float

    def __init__(
            self,
            start_value: float,
            end_value: float,
            extend_duration_seconds: float,
            reduce_duration_seconds: float,
            next_step_check_callback: tp.Callable[[], bool] | None = None
    ) -> None:
        self.__start_value = start_value
        self.__end_value = end_value
        self.__extend_duration_seconds = extend_duration_seconds
        self.__reduce_duration_seconds = reduce_duration_seconds
        self.__next_step_check_callback = next_step_check_callback

        self.__phase = AnimationPhase.AT_START
        self.__current_value = start_value
        self.__current_time = 0.0

        self.__next_step_check_mode = False

    def __calc_anim_progress(self, value_progress: float) -> float:
        if self.__start_value == self.__end_value:
            return 1.0
        else:
            return value_progress / (self.__end_value - self.__start_value)

    def extend(self) -> None:
        print("EXTEND")
        self.__phase = AnimationPhase.EXTENDING
        self.__current_time = (self.__extend_duration_seconds
                               * self.__calc_anim_progress(self.__current_value - self.__start_value))

    def contract(self) -> None:
        print("CONTRACT")
        self.__phase = AnimationPhase.CONTRACTING
        self.__current_time = (self.__reduce_duration_seconds
                               * self.__calc_anim_progress(self.__end_value - self.__current_value))

    def stop(self) -> None:
        print("STOP")
        self.__phase = AnimationPhase.STOPPED

    def __calc(self, delta: float) -> None:
        if self.__phase == "at_start" or self.__phase == "at_end" or self.__phase == "stopped":
            return

        current_relative: float = 1.0
        full_scale: float = (self.__end_value - self.__start_value)
        self.__current_time += delta

        if self.__phase == AnimationPhase.EXTENDING:
            if self.__current_time > self.__extend_duration_seconds:
                self.__phase = AnimationPhase.AT_END
                self.__current_value = self.__end_value
                self.__current_time = self.__extend_duration_seconds
                return

            if self.__extend_duration_seconds > 0:
                current_relative = self.__current_time / self.__extend_duration_seconds

            self.__current_value = self.__start_value + (full_scale * current_relative)

        elif self.__phase == AnimationPhase.CONTRACTING:
            if self.__current_time > self.__reduce_duration_seconds:
                self.__phase = AnimationPhase.AT_START
                self.__current_value = self.__start_value
                self.__current_time = self.__reduce_duration_seconds
                return

            if self.__reduce_duration_seconds > 0:
                current_relative = self.__current_time / self.__reduce_duration_seconds

            self.__current_value = self.__end_value - (full_scale * current_relative)

    def update(self, delta: float) -> float:
        self.__calc(delta)
        return self.__current_value

    def get_value(self) -> float:
        return self.__current_value

    def is_changing(self) -> bool:
        return self.__phase in [AnimationPhase.EXTENDING, AnimationPhase.CONTRACTING]


# Helper type for the inputs: accepts a single number or a sequence of numbers
AnimInput = tp.Union[float, int, tp.Sequence[tp.Union[float, int]]]


class MultiAnimation:
    __animations: list[Animation]
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
        self.__animations = []

        # Optimization: Use one animation if only scalars are given but multiple are needed
        if all_scalar and count is not None and count > 1:
            self.__is_single = True
            self.__count = count
            self.__animations = [
                Animation(float(start), float(end), float(extend_duration), float(reduce_duration)),
            ]
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
            def _normalize(val: AnimInput) -> tp.Tuple[float, ...]:
                if isinstance(val, (int, float)):
                    return (float(val),) * self.__count
                return tuple(float(v) for v in val)

            s_norm = _normalize(start)
            e_norm = _normalize(end)
            ex_norm = _normalize(extend_duration)
            red_norm = _normalize(reduce_duration)

            # Create individual animations for each index
            self.__animations = [
                Animation(s_norm[i], e_norm[i], ex_norm[i], red_norm[i])
                for i in range(self.__count)
            ]

    def extend(self) -> None:
        for anim in self.__animations:
            anim.extend()

    def contract(self) -> None:
        for anim in self.__animations:
            anim.contract()

    def stop(self) -> None:
        for anim in self.__animations:
            anim.stop()

    def update(self, delta: float) -> list[float]:
        if self.__is_single:
            val = self.__animations[0].update(delta)
            return [val] * self.__count

        return [anim.update(delta) for anim in self.__animations]

    def get_value(self) -> list[float]:
        if self.__is_single:
            val = self.__animations[0].get_value()
            return [val] * self.__count

        return [anim.get_value() for anim in self.__animations]

    def is_changing(self) -> bool:
        return any([anim.is_changing() for anim in self.__animations])
