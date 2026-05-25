"""
Manages multiple synchronized animations using scalar or sequence inputs.

| ``Path``: amoginarium/graphics/ui/_animations/_multi_animation.py
| ``Project``: amoginarium
| ``Created``: 16.03.2026
| ``Authors``: LukasKrah
"""

from __future__ import annotations

import typing as tp

from ._complex_animation import create_animation

if tp.TYPE_CHECKING:
    from ._animation_types import anim_curve_input_t, anim_curve_t
    from ._animation_types import anim_input_t, AnimationPhase
    from ._complex_animation import Animation


class MultiAnimation[A]:
    """Handles multiple animations with flexibility to process scalar values or sequences."""

    __animations: list[Animation]
    __is_single: bool
    __count: int

    def __init__(
        self,
        start_values: anim_input_t,
        end_values: anim_input_t | None = None,
        *_args: tp.Any,
        extend_durations: anim_input_t | None = None,
        collapse_durations: anim_input_t | None = None,
        extend_debounce_duration: anim_input_t | None = None,
        collapse_debounce_duration: anim_input_t | None = None,
        extend_curve: anim_curve_input_t | None = None,
        collapse_curve: anim_curve_input_t | None = None,
        count: int | None = None,
    ) -> None:
        """
        Create a MultiAnimation instance
        :param start_values: Single value or sequence of values to start the animations from.
        :param end_values: Single value or sequence of values to end the animations at.
        :param extend_durations: Single value / sequence of values for the extension durations in seconds.
        :param collapse_durations: Single value / sequence of values for the collapse durations in seconds.
        :param extend_debounce_duration: Single value / sequence of values for the extension debounce in seconds.
        :param collapse_debounce_duration: Single value / sequence of values for the collapse debounce in seconds.
        :param extend_curve: Single curve or sequence of curves for the extension phase.
        :param collapse_curve: Single curve or sequence of curves for the collapse phase.
        :param count: Number of animations to create. If not provided, it will be inferred from the input sequences.
        """
        self.__animations = []

        def _is_single_or_none(val) -> bool:
            return val in (None, ...) or not isinstance(val, (list, tuple))

        def _safe_float(val, default=...):
            """Safely cast to float, returning the default if val is None or Ellipsis."""
            return float(val) if val not in (None, ...) else default

        # Check if ALL inputs are single values (or None)
        all_single_or_none = (
            _is_single_or_none(start_values)
            and _is_single_or_none(end_values)
            and _is_single_or_none(extend_durations)
            and _is_single_or_none(collapse_durations)
            and _is_single_or_none(extend_debounce_duration)
            and _is_single_or_none(collapse_debounce_duration)
            and _is_single_or_none(extend_curve)
            and _is_single_or_none(collapse_curve)
        )

        if all_single_or_none:
            self.__is_single = True
            self.__count = count if count is not None else 1

            # Use _safe_float to avoid crashing on Ellipsis
            s_val = _safe_float(start_values, default=0.0)
            e_val = _safe_float(end_values)
            ex_dur = _safe_float(extend_durations)
            col_dur = _safe_float(collapse_durations)
            ex_deb = _safe_float(extend_debounce_duration)
            col_deb = _safe_float(collapse_debounce_duration)

            ex_curve = extend_curve if extend_curve not in (None, ...) else ...
            col_curve = collapse_curve if collapse_curve not in (None, ...) else ...

            self.__animations = [
                create_animation(
                    start_value=s_val,
                    end_value=e_val,
                    extend_duration=ex_dur,
                    collapse_duration=col_dur,
                    extend_debounce_duration=ex_deb,
                    collapse_debounce_duration=col_deb,
                    extend_curve=ex_curve,
                    collapse_curve=col_curve,
                )
            ]
        else:
            self.__is_single = False

            # Extract all arguments that are sequences
            sequences = [
                x
                for x in (
                    start_values,
                    end_values,
                    extend_durations,
                    collapse_durations,
                    extend_debounce_duration,
                    collapse_debounce_duration,
                    extend_curve,
                    collapse_curve,
                )
                if isinstance(x, (tuple, list))
            ]

            if sequences:
                seq_length = max(len(seq) for seq in sequences)
                if count is not None and count != seq_length:
                    msg = (
                        f"Provided count ({count}) does not match the longest "
                        f"provided sequence ({seq_length})."
                    )
                    raise ValueError(msg)
                self.__count = seq_length
            else:
                self.__count = count if count is not None else 1

            def _normalize(val, is_numeric: bool = True) -> tuple:
                # Map None to Ellipsis (...) so default kwargs in create_animation trigger correctly
                if val in (None, ...):
                    return (...,) * self.__count

                if not isinstance(val, (list, tuple)):
                    converted = _safe_float(val) if is_numeric else val
                    return (converted,) * self.__count

                if is_numeric:
                    norm_list = [_safe_float(v) for v in val]
                else:
                    norm_list = [v if v not in (None, ...) else ... for v in val]

                # Pad sequence if it's too short
                while len(norm_list) < self.__count:
                    norm_list.append(norm_list[-1] if norm_list else ...)

                return tuple(norm_list)

            s_norm = _normalize(start_values)
            e_norm = _normalize(end_values)
            ex_dur_norm = _normalize(extend_durations)
            col_dur_norm = _normalize(collapse_durations)
            ex_deb_norm = _normalize(extend_debounce_duration)
            col_deb_norm = _normalize(collapse_debounce_duration)
            ex_curve_norm = _normalize(extend_curve, is_numeric=False)
            col_curve_norm = _normalize(collapse_curve, is_numeric=False)

            self.__animations = [
                create_animation(
                    start_value=s_norm[i] if s_norm[i] is not ... else 0.0,
                    end_value=e_norm[i],
                    extend_duration=ex_dur_norm[i],
                    collapse_duration=col_dur_norm[i],
                    extend_debounce_duration=ex_deb_norm[i],
                    collapse_debounce_duration=col_deb_norm[i],
                    extend_curve=ex_curve_norm[i],
                    collapse_curve=col_curve_norm[i],
                )
                for i in range(self.__count)
            ]

    def extend(self) -> None:
        """Start extending from current to end values."""
        for anim in self.__animations:
            anim.extend()

    def contract(self) -> None:
        """Start contracting from current to start values."""
        for anim in self.__animations:
            anim.collapse()

    def stop(self) -> None:
        """Stop the animations at the current values."""
        for anim in self.__animations:
            anim.stop()

    def update(self, delta: float) -> A:
        """
        Update the animations
        :param delta: Time since the last update in seconds
        :return: Value differences between current and last values.
        """
        if self.__is_single:
            val = self.__animations[0].update(delta)
            return (val,) * self.__count

        return tuple(anim.update(delta) for anim in self.__animations)

    def is_changing(self) -> bool:
        """:return: Whether any animation is currently in extension or contraction phase"""
        return any(anim.is_changing() for anim in self.__animations)

    def reset(self) -> None:
        """Reset the animations to their start values."""
        for anim in self.__animations:
            anim.reset()

    # region Methods: properties
    @property
    def start_values(self) -> A:
        """:return: Start values of the animations"""
        return tuple(anim.start_value for anim in self.__animations)

    @property
    def end_value(self) -> A:
        """:return: End values of the animations"""
        return tuple(anim.end_value for anim in self.__animations)

    @property
    def extend_durations(self) -> A:
        """:return: The extension durations of the animations in seconds"""
        return tuple(anim.extend_duration for anim in self.__animations)

    @property
    def extend_debounce_durations(self) -> A:
        """:return: Minimum times in extending phase before starting to extend"""
        return tuple(anim.extend_debounce_duration for anim in self.__animations)

    @property
    def collapse_durations(self) -> A:
        """:return: The collapse durations of the animations in seconds"""
        return tuple(anim.collapse_duration for anim in self.__animations)

    @property
    def collapse_debounce_durations(self) -> A:
        """:return: Minimum times in collapsing phase before starting to collapse"""
        return tuple(anim.collapse_debounce_duration for anim in self.__animations)

    @property
    def extend_curves(self) -> tuple[anim_curve_t, ...]:
        """:return: Extend curves functions"""
        return tuple(anim.extend_curve for anim in self.__animations)

    @property
    def collapse_curves(self) -> tuple[anim_curve_t, ...]:
        """:return: Collapse curves functions"""
        return tuple(anim.collapse_curve for anim in self.__animations)

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

    # endregion
