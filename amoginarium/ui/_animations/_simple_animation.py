"""
amoginarium/ui/_animations/_single_animation.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""

from ._animation_types import AnimationPhase


class SimpleAnimation:
    """Basic 2-position float value animation"""
    _start_value: float
    _end_value: float

    _phase: AnimationPhase
    _current_value: float
    _last_value: float

    def __init__(
            self,
            start_value: float,
            end_value: float = ...
    ) -> None:
        """
        Create a basic 2-position float value animation
        :param start_value: Value to start the animation from
        :param end_value: Maximum extended value
        """
        self._start_value = start_value
        self._end_value = end_value if end_value != ... else start_value

        self._phase = AnimationPhase.AT_START
        self._current_value = start_value
        self._last_value = start_value

    def extend(self) -> None:
        """Start extending from current to end value"""
        self._phase = AnimationPhase.EXTENDING

    def collapse(self) -> None:
        """Start collapsing from current to start value"""
        self._phase = AnimationPhase.COLLAPSING

    def stop(self) -> None:
        """Stop the animation at the current value"""
        self._phase = AnimationPhase.STOPPED

    def _calc(self, _delta: float) -> None:
        """Update the animation"""
        self._last_value = self._current_value
        if self._phase == "at_start" or self._phase == "at_end" or self._phase == "stopped":
            return

        if self._phase == AnimationPhase.EXTENDING:
            self._phase = AnimationPhase.AT_END
            self._current_value = self._end_value
        elif self._phase == AnimationPhase.COLLAPSING:
            self._phase = AnimationPhase.AT_START
            self._current_value = self._start_value

    def update(self, delta: float) -> float:
        """
        Update the animation
        :param delta: Time since the last update in seconds
        :return: Value difference between current and last value
        """
        self._calc(delta)
        return self._current_value - self._last_value

    def reset(self) -> None:
        """Reset the animation to its start value"""
        self._phase = AnimationPhase.AT_START
        self._current_value = self._start_value

    def is_changing(self) -> bool:
        """:return: Whether the animation is currently in extension or contraction phase"""
        return self._phase in [AnimationPhase.EXTENDING, AnimationPhase.COLLAPSING]

    # region Methods: properties
    @property
    def start_value(self) -> float:
        """:return: Start value of the animation"""
        return self._start_value

    @property
    def end_value(self) -> float:
        """:return: End value of the animation"""
        return self._end_value

    @property
    def phase(self) -> AnimationPhase:
        """:return: Current phase of the animation"""
        return self._phase

    @property
    def current_value(self) -> float:
        """:return: Current value of the animation"""
        return self._current_value

    # endregion
