"""
amoginarium/ui/_animations/_single_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from ._single_animation import SingleAnimation
from ._animation_types import AnimationPhase


class TimedAnimation(SingleAnimation):
    """Basic timed single float value animation"""
    _extend_duration_seconds: float
    _collapse_duration_seconds: float
    _current_time: float

    def __init__(
            self,
            start_value: float,
            end_value: float | None = None,
            extend_duration_seconds: float | None = None,
            collapse_duration_seconds: float | None = None,
    ) -> None:
        """
        Create a basic float value animation
        :param start_value: Value to start the animation from
        :param end_value: Maximum extended value
        :param extend_duration_seconds: Time from start to end
        :param collapse_duration_seconds: Time from end to start
        """
        super().__init__(start_value, end_value)
        self._extend_duration_seconds = extend_duration_seconds if extend_duration_seconds else 0.0
        self._collapse_duration_seconds = collapse_duration_seconds if collapse_duration_seconds else 0.0
        self._current_time = 0.0

    def __calc_anim_progress(self, value_progress: float) -> float:
        """
        Calculates the relative progress of the animation
        :param value_progress: Current absolute progression
        :return: Current relative progression
        """
        if self._start_value == self._end_value:
            return 1.0
        else:
            return value_progress / (self._end_value - self._start_value)

    def extend(self) -> None:
        """Start extending from current to end value"""
        self._phase = AnimationPhase.EXTENDING
        if self._current_time is not None:
            self._current_time = (self._extend_duration_seconds
                                  * self.__calc_anim_progress(self._current_value - self._start_value))

    def collapse(self) -> None:
        """Start collapsing from current to start value"""
        self._phase = AnimationPhase.COLLAPSING
        if self._current_time is not None:
            self._current_time = (self._collapse_duration_seconds
                                  * self.__calc_anim_progress(self._end_value - self._current_value))

    def stop(self) -> None:
        """Stop the animation at the current value"""
        self._phase = AnimationPhase.STOPPED

    def _calc(self, delta: float) -> None:
        """
        Update the animation
        :param delta: Time since the last update in seconds
        """
        if self._phase == "at_start" or self._phase == "at_end" or self._phase == "stopped":
            return

        current_relative: float = 1.0
        full_scale: float = (self._end_value - self._start_value)
        self._current_time += delta

        if self._phase == AnimationPhase.EXTENDING:
            if self._current_time > self._extend_duration_seconds:
                self._phase = AnimationPhase.AT_END
                self._current_value = self._end_value
                self._current_time = self._extend_duration_seconds
                return

            if self._extend_duration_seconds > 0:
                current_relative = self._current_time / self._extend_duration_seconds

            self._current_value = self._start_value + (full_scale * current_relative)

        elif self._phase == AnimationPhase.COLLAPSING:
            if self._current_time > self._collapse_duration_seconds:
                self._phase = AnimationPhase.AT_START
                self._current_value = self._start_value
                self._current_time = self._collapse_duration_seconds
                return

            if self._collapse_duration_seconds > 0:
                current_relative = self._current_time / self._collapse_duration_seconds

            self._current_value = self._end_value - (full_scale * current_relative)

    @property
    def extend_duration_seconds(self) -> float:
        """:return: The extension duration of the animation in seconds"""
        return self._extend_duration_seconds

    @property
    def collapse_duration_seconds(self) -> float:
        """:return: The collapse duration of the animation in seconds"""
        return self._collapse_duration_seconds

    @property
    def current_relative_progress(self) -> float:
        """:return: Current relative progress of the animation from the start"""
        return self.__calc_anim_progress(self._current_value - self._start_value)

    @property
    def current_time(self) -> float:
        """:return: Current time of the animation"""
        return self._current_time


Animation = SingleAnimation | TimedAnimation


def create_animation(
        start_value: float,
        end_value: float | None = None,
        extend_duration_seconds: float | None = None,
        collapse_duration_seconds: float | None = None,
) -> Animation:
    """
    Creates either a SingleAnimation or a TimedAnimation.
    :param start_value: Value to start the animation from
    :param end_value: Maximum extended value
    :param extend_duration_seconds: Time from start to end
    :param collapse_duration_seconds: Time from end to start
    :return:
    """
    if end_value is None or start_value == end_value:
        return SingleAnimation(start_value=start_value, end_value=end_value)

    has_extend_time = extend_duration_seconds is not None and extend_duration_seconds > 0.0
    has_collapse_time = collapse_duration_seconds is not None and collapse_duration_seconds > 0.0

    if has_extend_time or has_collapse_time:
        return TimedAnimation(
            start_value=start_value,
            end_value=end_value,
            extend_duration_seconds=extend_duration_seconds,
            collapse_duration_seconds=collapse_duration_seconds
        )

    return SingleAnimation(start_value=start_value, end_value=end_value)
