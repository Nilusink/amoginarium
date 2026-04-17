"""
amoginarium/logic/entities/_collisions.py

Project: amoginarium
Created: 16.04.2026
Authors: LukasKrah
"""

from amoginarium.shared.collision_detection import CollisionManager, CollisionEvent

collision_manager = CollisionManager(
    base_cell_size=500,
    level_dividers=[10],
)


