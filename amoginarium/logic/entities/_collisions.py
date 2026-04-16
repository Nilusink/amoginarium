"""
amoginarium/logic/entities/_collisions.py

Project: amoginarium
Created: 16.04.2026
Authors: LukasKrah
"""

from amoginarium.shared.collision_detection import CollisionManager

collision_manager = CollisionManager(
    base_cell_size=500,
    level_dividers=[10],
)

# region Groups
collision_group_players = collision_manager.add_group(max_level=0)
collision_group_bullets = collision_manager.add_group(max_level=1)
collision_group_islands = collision_manager.add_group(max_level=0)
collision_group_turrets = collision_manager.add_group(max_level=0)
# endregion

# region Relations

# endregion