"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from .._base_entities import PositionedLogicEntity
from .collision_manager import collision_manager

collision_group_players = collision_manager.add_group(max_level=0)
collision_group_bullets = collision_manager.add_group(max_level=1)
collision_group_grenades = collision_manager.add_group(max_level=1)
collision_group_islands = collision_manager.add_group(max_level=0)
collision_group_turrets = collision_manager.add_group(max_level=0)

on_collision = PositionedLogicEntity.on_collision
set_normals = PositionedLogicEntity.set_normals

def create_default_relation(group_a, group_b):
    collision_manager.create_relation(
        group_a_id=group_a,
        group_b_id=group_b,
        cb_a_on_col=on_collision,
        cb_b_on_col=on_collision,
        cb_a_set_norm=set_normals,
        cb_b_set_norm=set_normals
    )

# region Grenades collide with Islands, Bullets, Players
create_default_relation(collision_group_grenades, collision_group_islands)
create_default_relation(collision_group_grenades, collision_group_bullets)
create_default_relation(collision_group_grenades, collision_group_players)
# endregion

# region Players collide with Islands, Bullets

create_default_relation(collision_group_bullets, collision_group_islands)  # Bullets - Islands
create_default_relation(collision_group_players, collision_group_islands)  # Players - Islands
create_default_relation(collision_group_players, collision_group_bullets)  # Players - Bullets
create_default_relation(collision_group_bullets, collision_group_bullets)  # Bullets - Bullets