"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from .._base_entities import PositionedLogicEntity
from .collision_manager import collision_manager

collision_group_players = collision_manager.add_group(max_level=0, hitbox_type="circle")
collision_group_bullets = collision_manager.add_group(max_level=1, hitbox_type="circle")
collision_group_grenades = collision_manager.add_group(max_level=1, hitbox_type="circle")
collision_group_islands = collision_manager.add_group(max_level=0)
collision_group_turrets = collision_manager.add_group(max_level=0)
collision_group_shields = collision_manager.add_group(max_level=0, hitbox_type="obb")

collision_start = PositionedLogicEntity.collision_start
collision_end = PositionedLogicEntity.collision_end

def create_default_relation(group_a, group_b):
    collision_manager.create_relation(
        group_a_id=group_a,
        group_b_id=group_b,
        cb_a_on_start=collision_start,
        cb_b_on_start=collision_start,
        cb_a_on_end=collision_end,
        cb_b_on_end=collision_end
    )

# Grenades collide with Islands, Bullets, Players
create_default_relation(collision_group_grenades, collision_group_islands)
create_default_relation(collision_group_grenades, collision_group_bullets)
create_default_relation(collision_group_grenades, collision_group_players)

# collision id / col

# Players collide with Islands, Bullets, (Grenades)
create_default_relation(collision_group_players, collision_group_islands)
create_default_relation(collision_group_players, collision_group_bullets)

# Bullets collide with Islands, Bullets, Turrets, (Players, Grenades)
create_default_relation(collision_group_bullets, collision_group_islands)
create_default_relation(collision_group_bullets, collision_group_bullets)
create_default_relation(collision_group_bullets, collision_group_turrets)

# TEST: shield
create_default_relation(collision_group_shields, collision_group_bullets)
create_default_relation(collision_group_shields, collision_group_grenades)
