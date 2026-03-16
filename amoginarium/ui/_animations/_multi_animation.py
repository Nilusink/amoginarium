"""
amoginarium/ui/_animations/_multi_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from ._single_animation import SingleAnimation
from ._types import AnimInput, AnimationPhase
from ._timed_animation import TimedAnimation, create_animation


class MultiAnimation[A]:
    """Handles multiple animations with flexibility to process scalar values or sequences."""
    __animations: list[TimedAnimation | SingleAnimation]
    __is_single: bool
    __count: int

    def __init__(
            self,
            start_values: AnimInput,
            end_values: AnimInput | None = None,
            extend_durations_in_seconds: AnimInput | None = None,
            collapse_duration_in_seconds: AnimInput | None = None,
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
        self.__animations = []

        # Helper to check if an input is a single scalar or None
        def _is_single_or_none(val: AnimInput) -> bool:
            return val is None or isinstance(val, (int, float))

        # Check if ALL inputs are single scalars (or None)
        all_single_or_none = (
                _is_single_or_none(start_values) and
                _is_single_or_none(end_values) and
                _is_single_or_none(extend_durations_in_seconds) and
                _is_single_or_none(collapse_duration_in_seconds)
        )

        # Optimization: Use one animation if only scalars/Nones are given
        if all_single_or_none:
            self.__is_single = True
            self.__count = count if count is not None else 1

            # Type hinting forces floats, handle None fallback in create_animation if necessary
            # or explicitly cast here if they are not None.
            s_val = float(start_values) if start_values is not None else 0.0
            e_val = float(end_values) if end_values is not None else None
            ex_val = float(extend_durations_in_seconds) if extend_durations_in_seconds is not None else None
            col_val = float(collapse_duration_in_seconds) if collapse_duration_in_seconds is not None else None

            self.__animations = [
                create_animation(s_val, e_val, ex_val, col_val)
            ]
        else:
            self.__is_single = False

            # Extract all arguments that are sequences (tuples or lists)
            sequences = [
                x for x in (start_values, end_values, extend_durations_in_seconds, collapse_duration_in_seconds)
                if isinstance(x, (tuple, list))
            ]

            if sequences:
                # Find the maximum sequence length
                seq_length = max(len(seq) for seq in sequences)

                if count is not None and count != seq_length:
                    raise ValueError(
                        f"Provided count ({count}) does not match the longest "
                        f"provided sequence ({seq_length})."
                    )
                self.__count = seq_length
            else:
                self.__count = count if count is not None else 1

            # Helper function to normalize values into sequences of the correct length, padding None
            def _normalize(val: AnimInput) -> tp.Tuple[float | None, ...]:
                if val is None:
                    return (None,) * self.__count
                if isinstance(val, (int, float)):
                    return (float(val),) * self.__count

                # It's a sequence. Pad it with the last value (or None) if it's too short
                norm_list = [float(v) if v is not None else None for v in val]
                while len(norm_list) < self.__count:
                    norm_list.append(norm_list[-1] if norm_list else None)

                return tuple(norm_list)

            s_norm = _normalize(start_values)
            e_norm = _normalize(end_values)
            ex_norm = _normalize(extend_durations_in_seconds)
            red_norm = _normalize(collapse_duration_in_seconds)

            # Create individual animations using the factory, passing Nones as allowed
            self.__animations = [
                create_animation(
                    start_value=s_norm[i] if s_norm[i] is not None else 0.0,
                    end_value=e_norm[i],
                    extend_duration_seconds=ex_norm[i],
                    collapse_duration_seconds=red_norm[i]
                )
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

        return tuple(anim.current_value for anim in self.__animations)

    @property
    def current_relative_progress(self) -> A:
        """:return: Current relative progresses of the animations from the starts"""
        return tuple(anim.current_relative_progress for anim in self.__animations)

    @property
    def current_time(self) -> A:
        """:return: Current times of the animations"""
        return tuple(anim.current_time for anim in self.__animations)
