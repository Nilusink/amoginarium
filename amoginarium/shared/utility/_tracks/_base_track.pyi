"""
Base track class.

Path: amoginarium/shared/utility/_tracks/_base_track.pyi
Project: amoginarium
Created: 22.05.2026
Authors: Nilusink
"""

from enum import Enum

from .._cvectors import Vec2
from ._ctrack_enums import TrackClassification

class TrackState(Enum):
    """Track state."""

class TrackQuality(Enum):
    """Target track quality."""

class BaseTrack:
    """Base track class."""

    track_classification: TrackClassification

    @property
    def state(self) -> TrackState:
        """Track State."""

    @property
    def quality(self) -> TrackQuality:
        """Target track quality."""

    @property
    def time_since_last_update(self) -> float:
        """Time since last track update."""

    def increment_time(self, dt: float) -> None:
        """Increment track time + position predict."""

    def reset(self) -> None:
        """Reset the track."""

    def set_size(self, x: float, y: float) -> None:
        """Set size of tracked object."""

    def initialize(self, x: float, y: float, vx: float, vy: float, g: float) -> None:
        """
        Initialize the track.

        :param x: initial x position
        :param y: initial y position
        :param vx: initial x velocity
        :param vy: initial y velocity
        :param g: gravity
        """

    def step(self, mx: float, my: float, mvx: float, mvy: float, dt: float) -> None:
        """
        Add new sensor data to track.

        :param mx: x position
        :param my: y position
        :param mvx: x velocity
        :param mvy: y velocity
        :param dt: time since last step
        """

    def get_position(self) -> Vec2:
        """Get current position."""

    def get_velocity(self) -> Vec2:
        """Get current velocity."""

    def get_acceleration(self) -> Vec2:
        """Get current acceleration."""

    def predict_future_position(self, t: float) -> Vec2:
        """
        Predict position in t seconds.

        :param t: time in seconds
        :return: predicted position
        """

    def get_speed(self) -> float:
        """Get current speed in m/s."""

    def kill(self) -> None:
        """Mark track as Dead."""
