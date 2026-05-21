"""
Target tracks.

Documents target position, velocity & acceleration over time.
Path: amoginarium/logic/entities/_weaponry/templates/_sensors/_ctarget_track.pyi
Project: amoginarium
Created: 21.05.2026
Authors: Nilusink
"""

import typing as tp

from amoginarium.shared.utility import Vec2

class TargetTrack:
    position: Vec2
    velocity: Vec2
    acceleration: Vec2

    def add_point(self, position: Vec2, dt: float) -> None:
        """Add a position point to the track."""
