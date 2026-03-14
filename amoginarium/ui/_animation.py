"""
amoginarium/ui/_animated_value.py

Project: amoginarium
"""

from __future__ import annotations

from enum import Enum

import typing as tp


##################################################
#                     Code                       #
##################################################

class AnimationPhase(Enum):
    """Enumeration representing the various phases of an animation."""
    AT_START = 0
    EXTENDING = 1
    STOPPED = 2
    COLLAPSING = 3
    AT_END = 4


class Animation:
    """Basic single float value animation"""
    __start_value: float
    __end_value: float
    __extend_duration_seconds: float
    __collapse_duration_seconds: float

    __phase: AnimationPhase
    __current_value: float
    __current_time: float

    def __init__(
            self,
            start_value: float,
            end_value: float,
            extend_duration_seconds: float,
            collapse_duration_seconds: float,
    ) -> None:
        """
        Create a basic float value animation
        :param start_value: Value to start the animation from
        :param end_value: Maximum extended value
        :param extend_duration_seconds: Time from start to end
        :param collapse_duration_seconds: Time from end to start
        """
        self.__start_value = start_value
        self.__end_value = end_value
        self.__extend_duration_seconds = extend_duration_seconds
        self.__collapse_duration_seconds = collapse_duration_seconds

        self.__phase = AnimationPhase.AT_START
        self.__current_value = start_value
        self.__current_time = 0.0

    def __calc_anim_progress(self, value_progress: float) -> float:
        """
        Calculates the relative progress of the animation
        :param value_progress: Current absolute progression
        :return: Current relative progression
        """
        if self.__start_value == self.__end_value:
            return 1.0
        else:
            return value_progress / (self.__end_value - self.__start_value)

    def extend(self) -> None:
        """Start extending from current to end value"""
        self.__phase = AnimationPhase.EXTENDING
        self.__current_time = (self.__extend_duration_seconds
                               * self.__calc_anim_progress(self.__current_value - self.__start_value))

    def collapse(self) -> None:
        """Start collapsing from current to start value"""
        self.__phase = AnimationPhase.COLLAPSING
        self.__current_time = (self.__collapse_duration_seconds
                               * self.__calc_anim_progress(self.__end_value - self.__current_value))

    def stop(self) -> None:
        """Stop the animation at the current value"""
        self.__phase = AnimationPhase.STOPPED

    def __calc(self, delta: float) -> None:
        """
        Update the animation
        :param delta: Time since the last update in seconds
        """
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

        elif self.__phase == AnimationPhase.COLLAPSING:
            if self.__current_time > self.__collapse_duration_seconds:
                self.__phase = AnimationPhase.AT_START
                self.__current_value = self.__start_value
                self.__current_time = self.__collapse_duration_seconds
                return

            if self.__collapse_duration_seconds > 0:
                current_relative = self.__current_time / self.__collapse_duration_seconds

            self.__current_value = self.__end_value - (full_scale * current_relative)

    def update(self, delta: float) -> float:
        """
        Update the animation
        :param delta: Time since the last update in seconds
        :return: New value of the animation
        """
        self.__calc(delta)
        return self.__current_value

    def is_changing(self) -> bool:
        """:return: Whether the animation is currently in extension or contraction phase"""
        return self.__phase in [AnimationPhase.EXTENDING, AnimationPhase.COLLAPSING]

    @property
    def start_value(self) -> float:
        """:return: Start value of the animation"""
        return self.__start_value

    @property
    def end_value(self) -> float:
        """:return: End value of the animation"""
        return self.__end_value

    @property
    def extend_duration_seconds(self) -> float:
        """:return: The extension duration of the animation in seconds"""
        return self.__extend_duration_seconds

    @property
    def collapse_duration_seconds(self) -> float:
        """:return: The collapse duration of the animation in seconds"""
        return self.__collapse_duration_seconds

    @property
    def phase(self) -> AnimationPhase:
        """:return: Current phase of the animation"""
        return self.__phase

    @property
    def current_value(self) -> float:
        """:return: Current value of the animation"""
        return self.__current_value

    @property
    def current_relative_progress(self) -> float:
        """:return: Current relative progress of the animation from the start"""
        return self.__calc_anim_progress(self.__current_value - self.__start_value)

    @property
    def current_time(self) -> float:
        """:return: Current time of the animation"""
        return self.__current_time


AnimInput = tp.Union[float, int, tp.Sequence[tp.Union[float, int]]]


class MultiAnimation[A]:
    """
    Handles multiple animations with flexibility to process scalar values or sequences.
    """
    __animations: list[Animation]
    __is_single: bool
    __count: int

    def __init__(
            self,
            start_values: AnimInput,
            end_values: AnimInput,
            extend_durations_in_seconds: AnimInput,
            collapse_duration_in_seconds: AnimInput,
            count: int | None = None
    ) -> None:
        """
        Create a MultiAnimation instance
        :param start_values: Single value or sequence of values to start the animations from.
        :param end_values: Single value or sequence of values to end the animations at.
        :param extend_durations_in_seconds: Single value / sequence of values for the extension durations in seconds.
        :param collapse_duration_in_seconds: Single value / sequence of values for the collapse durations in seconds.
        :param count: Number of animations to create. If not provided, it will be inferred from the input sequences.
        """
        # Check if all inputs are single scalar values
        all_scalar = all(
            isinstance(x, (int, float))
            for x in (start_values, end_values, extend_durations_in_seconds, collapse_duration_in_seconds)
        )
        self.__animations = []

        # Optimization: Use one animation if only scalars are given but multiple is needed
        if all_scalar and count is not None and count > 1:
            self.__is_single = True
            self.__count = count
            self.__animations = [
                Animation(float(start_values), float(end_values), float(extend_durations_in_seconds),
                          float(collapse_duration_in_seconds)),
            ]
        else:
            self.__is_single = False

            # Extract all arguments that are sequences (tuples or lists)
            sequences = [
                x for x in (start_values, end_values, extend_durations_in_seconds, collapse_duration_in_seconds)
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
                # Fallback if no sequences were found, but it wasn't caught by the all_scalar optimization
                self.__count = count if count is not None else 1

            # Helper function to normalize scalar values into sequences of the correct length
            def _normalize(val: AnimInput) -> tp.Tuple[float, ...]:
                if isinstance(val, (int, float)):
                    return (float(val),) * self.__count
                return tuple(float(v) for v in val)

            s_norm = _normalize(start_values)
            e_norm = _normalize(end_values)
            ex_norm = _normalize(extend_durations_in_seconds)
            red_norm = _normalize(collapse_duration_in_seconds)

            # Create individual animations for each index
            self.__animations = [
                Animation(s_norm[i], e_norm[i], ex_norm[i], red_norm[i])
                for i in range(self.__count)
            ]

    def extend(self) -> None:
        """Start extending from current to end values"""
        for anim in self.__animations:
            anim.extend()

    def contract(self) -> None:
        """Start contracting from current to start values"""
        for anim in self.__animations:
            anim.collapse()

    def stop(self) -> None:
        """Stop the animations at the current values"""
        for anim in self.__animations:
            anim.stop()

    def update(self, delta: float) -> A:
        """
        Update the animations
        :param delta: Time since the last update in seconds
        :return: New values of the animations
        """
        if self.__is_single:
            val = self.__animations[0].update(delta)
            return (val,) * self.__count

        return tuple(anim.update(delta) for anim in self.__animations)

    def is_changing(self) -> bool:
        """:return: Whether any animation is currently in extension or contraction phase"""
        return any([anim.is_changing() for anim in self.__animations])

    @property
    def start_values(self) -> A:
        """:return: Start values of the animations"""
        return tuple(anim.start_value for anim in self.__animations)

    @property
    def end_value(self) -> A:
        """:return: End values of the animations"""
        return tuple(anim.end_value for anim in self.__animations)

    @property
    def extend_duration_seconds(self) -> A:
        """:return: The extension durations of the animations in seconds"""
        return tuple(anim.extend_duration_seconds for anim in self.__animations)

    @property
    def collapse_duration_seconds(self) -> A:
        """:return: The collapse durations of the animations in seconds"""
        return tuple(anim.collapse_duration_seconds for anim in self.__animations)

    @property
    def phase(self) -> tuple[AnimationPhase, ...]:
        """:return: Current phases of the animations"""
        return tuple(anim.phase for anim in self.__animations)

    @property
    def current_value(self) -> A:
        """:return: Current values of the animations"""
        if self.__is_single:
            val = self.__animations[0].current_value
            return (val,) * self.__count

        return (anim.current_value for anim in self.__animations)

    @property
    def current_relative_progress(self) -> A:
        """:return: Current relative progresses of the animations from the starts"""
        return tuple(anim.current_relative_progress for anim in self.__animations)

    @property
    def current_time(self) -> A:
        """:return: Current times of the animations"""
        return tuple(anim.current_time for anim in self.__animations)
