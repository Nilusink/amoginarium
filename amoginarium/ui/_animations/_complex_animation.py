"""
amoginarium/ui/_animations/_complex_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

import typing as tp
from types import EllipsisType

from ._animation_types import AnimationPhase, anim_curve_t
from ._simple_animation import SimpleAnimation


class ComplexAnimation(SimpleAnimation):
    """Animation with extended functionality"""
    _extend_duration: float
    _extend_debounce_duration: float
    _collapse_duration: float
    _collapse_debounce_duration: float

    _extend_curve: anim_curve_t
    _collapse_curve: anim_curve_t

    _current_time: float

    _linear_progress: float
    _run_start_value: float
    _run_duration: float
    _debounce_timer: float

    def __init__(
            self,
            start_value: float | EllipsisType,
            end_value: float | EllipsisType = ...,
            *_args: tp.Any,
            extend_duration: float | EllipsisType = 0.0,
            collapse_duration: float | EllipsisType = ...,
            extend_debounce_duration: float | EllipsisType = 0.0,
            collapse_debounce_duration: float | EllipsisType = ...,
            extend_curve: anim_curve_t | EllipsisType = lambda a: a,
            collapse_curve: anim_curve_t | EllipsisType = ...,
    ) -> None:
        """
        Create a basic float value animation
        :param start_value: Value to start the animation from
        :param end_value: Maximum extended value. Defaults to start_value
        :param extend_duration: Time from start to end
        :param collapse_duration: Time from end to start. Defaults to extend_duration
        :param extend_debounce_duration: Minimum time in extending phase before starting to extend
        :param collapse_debounce_duration: Minimum time in collapsing phase before starting to collapse.
        Defaults to extend_debounce_duration
        :param extend_curve: Extend curve function. Takes float from 0 to 1
        :param collapse_curve: Collapse curve function. Takes float from 0 to 1. Defaults t reverse extend_curve
        """
        super().__init__(start_value, end_value)

        self._extend_duration = extend_duration if extend_duration != ... else 0.0
        self._collapse_duration = collapse_duration if collapse_duration != ... else self._extend_duration

        self._extend_debounce_duration = extend_debounce_duration if extend_debounce_duration != ... else 0.0
        self._collapse_debounce_duration = collapse_debounce_duration \
            if collapse_debounce_duration != ... else self._extend_debounce_duration

        self._extend_curve = extend_curve if extend_curve != ... else lambda a: a
        self._collapse_curve = collapse_curve if collapse_curve != ... else lambda a: 1 - self._extend_curve(1 - a)

        self._current_time = 0.0
        self._linear_progress = 0.0
        self._run_start_value = self._start_value
        self._run_duration = 0.0
        self._debounce_timer = 0.0

    def __calc_anim_progress(self, value_progress: float) -> float:
        """
        Calculates the relative progress of the animation based on value
        :param value_progress: Current absolute progression
        :return: Current relative progression
        """
        if self._start_value == self._end_value:
            return 1.0
        else:
            return value_progress / (self._end_value - self._start_value)

    def extend(self) -> None:
        """Start extending from current to end value"""
        if self._phase in (AnimationPhase.EXTENDING, AnimationPhase.AT_END):
            return

        # Only debounce if starting from the absolute beginning
        if self._phase == AnimationPhase.AT_START:
            self._debounce_timer = self._extend_debounce_duration
        else:
            self._debounce_timer = 0.0

        self._phase = AnimationPhase.EXTENDING
        self._run_start_value = self._current_value

        self._run_duration = self._extend_duration * (1.0 - self._linear_progress)
        self._current_time = 0.0

    def collapse(self) -> None:
        """Start collapsing from current to start value"""
        if self._phase in (AnimationPhase.COLLAPSING, AnimationPhase.AT_START):
            return

        # Only debounce if starting from the absolute end
        if self._phase == AnimationPhase.AT_END:
            self._debounce_timer = self._collapse_debounce_duration
        else:
            self._debounce_timer = 0.0

        self._phase = AnimationPhase.COLLAPSING
        self._run_start_value = self._current_value

        self._run_duration = self._collapse_duration * self._linear_progress
        self._current_time = 0.0

    def stop(self) -> None:
        """Stop the animation at the current value"""
        self._phase = AnimationPhase.STOPPED
        self._debounce_timer = 0.0

    def _calc(self, delta: float) -> None:
        """
        Update the animation
        :param delta: Time since the last update in seconds
        """
        if self._phase in (AnimationPhase.AT_START, AnimationPhase.AT_END, AnimationPhase.STOPPED):
            return

        if self._debounce_timer >= 0.0:
            self._debounce_timer -= delta
            if self._debounce_timer > 0.0:
                return
            # Debounce finished this frame, carry over the remaining time to current_time
            delta = -self._debounce_timer
            self._debounce_timer = 0.0

        self._current_time += delta

        if self._phase == AnimationPhase.EXTENDING:
            # Update absolute logical time progress (0.0 to 1.0)
            if self._extend_duration > 0:
                self._linear_progress += delta / self._extend_duration
            else:
                self._linear_progress = 1.0
            self._linear_progress = min(1.0, self._linear_progress)

            if self._current_time >= self._run_duration:
                self._phase = AnimationPhase.AT_END
                self._current_value = self._end_value
                self._current_time = self._run_duration
                self._linear_progress = 1.0
                return

            current_relative = self._current_time / self._run_duration if self._run_duration > 0 else 1.0

            # Map the curve over the remaining distance dynamically
            dist = self._end_value - self._run_start_value
            self._current_value = self._run_start_value + (dist * self._extend_curve(current_relative))

        elif self._phase == AnimationPhase.COLLAPSING:
            # Update absolute logical time progress (1.0 down to 0.0)
            if self._collapse_duration > 0:
                self._linear_progress -= delta / self._collapse_duration
            else:
                self._linear_progress = 0.0
            self._linear_progress = max(0.0, self._linear_progress)

            if self._current_time >= self._run_duration:
                self._phase = AnimationPhase.AT_START
                self._current_value = self._start_value
                self._current_time = self._run_duration
                self._linear_progress = 0.0
                return

            current_relative = self._current_time / self._run_duration if self._run_duration > 0 else 1.0

            # Map the curve over the remaining distance dynamically
            dist = self._start_value - self._run_start_value
            self._current_value = self._run_start_value + (dist * self._collapse_curve(current_relative))

    def reset(self) -> None:
        super().reset()
        self._current_time = 0.0
        self._linear_progress = 0.0
        self._run_start_value = self._start_value
        self._run_duration = 0.0
        self._debounce_timer = 0.0

    # region Methods: properties
    @property
    def extend_duration(self) -> float:
        """:return: The extension duration of the animation in seconds"""
        return self._extend_duration

    @property
    def extend_debounce_duration(self) -> float:
        """:return: Minimum time in extending phase before starting to extend"""
        return self._extend_debounce_duration

    @property
    def collapse_duration(self) -> float:
        """:return: The collapse duration of the animation in seconds"""
        return self._collapse_duration

    @property
    def collapse_debounce_duration(self) -> float:
        """:return: Minimum time in collapsing phase before starting to collapse"""
        return self._collapse_debounce_duration

    @property
    def current_relative_progress(self) -> float:
        """:return: Current relative progress of the animation from the start"""
        return self.__calc_anim_progress(self._current_value - self._start_value)

    @property
    def extend_curve(self) -> anim_curve_t:
        """:return: Extend curve function. Takes float from 0 to 1"""
        return self._extend_curve

    @property
    def collapse_curve(self) -> anim_curve_t:
        """:return: Collapse curve function. Takes float from 0 to 1"""
        return self._collapse_curve

    @property
    def current_time(self) -> float:
        """:return: Current time of the animation"""
        return self._current_time
    # endregion


Animation = SimpleAnimation | ComplexAnimation


def create_animation(
        start_value: float | EllipsisType,
        end_value: float | EllipsisType = ...,
        *_args: tp.Any,
        extend_duration: float | EllipsisType = ...,
        collapse_duration: float | EllipsisType = ...,
        extend_debounce_duration: float | EllipsisType = ...,
        collapse_debounce_duration: float | EllipsisType = ...,
        extend_curve: anim_curve_t | EllipsisType = ...,
        collapse_curve: anim_curve_t | EllipsisType = ...,
) -> Animation:
    """
    Creates either a SimpleAnimation or a ComplexAnimation based on the input values.
    """
    # Guard against Ellipsis on start/end values falling into SimpleAnimation
    s_val = float(start_value) if start_value != ... else 0.0
    e_val = float(end_value) if end_value != ... else s_val

    if end_value is None or s_val == e_val:
        return SimpleAnimation(start_value=s_val, end_value=e_val)

    if (
            (extend_duration != ... and extend_duration > 0.0)
            or (collapse_duration != ... and collapse_duration > 0.0)
            or (extend_debounce_duration != ... and extend_debounce_duration > 0.0)
            or (collapse_debounce_duration != ... and collapse_debounce_duration > 0.0)
            or extend_curve != ... or collapse_curve != ...
    ):
        return ComplexAnimation(
            start_value=s_val,
            end_value=e_val,
            extend_duration=extend_duration,
            collapse_duration=collapse_duration,
            extend_debounce_duration=extend_debounce_duration,
            collapse_debounce_duration=collapse_debounce_duration,
            extend_curve=extend_curve,
            collapse_curve=collapse_curve
        )

    return SimpleAnimation(start_value=s_val, end_value=e_val)
