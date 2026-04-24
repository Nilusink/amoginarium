"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared.collision_detection import CollisionCallback

from ._collision_manager import collision_manager, CollisionType
from .._base_entities import CollisionLogicEntity


# region Groups
collision_group_players: CollisionType.GroupID = collision_manager.add_group(max_level=0)
collision_group_bullets: CollisionType.GroupID = collision_manager.add_group(max_level=1, hitbox_type="circle")
collision_group_grenades: CollisionType.GroupID = collision_manager.add_group(max_level=1, hitbox_type="circle")
collision_group_islands: CollisionType.GroupID = collision_manager.add_group(max_level=0)
collision_group_turrets: CollisionType.GroupID = collision_manager.add_group(max_level=0)
collision_group_shields: CollisionType.GroupID = collision_manager.add_group(max_level=0, hitbox_type="obb")

all_groups: list[CollisionType.GroupID] = [
    collision_group_players,
    collision_group_bullets,
    collision_group_grenades,
    collision_group_islands,
    collision_group_turrets,
    collision_group_shields,
]

# endregion


# region Relations
COLLISION_START: tp.Final[CollisionCallback] = CollisionLogicEntity.collision_start  # type: ignore
COLLISION_END: tp.Final[CollisionCallback] = CollisionLogicEntity.collision_end  # type: ignore


def create_default_relation(group_a: CollisionType.GroupID, group_b: CollisionType.GroupID) -> None:
    """
    Registers a bidirectional collision relation between two groups using default callbacks.
    :param group_a: The ID of the first collision group.
    :param group_b: The ID of the second collision group.
    """
    collision_manager.create_relation(
        group_a_id=group_a,
        group_b_id=group_b,
        cb_a_on_start=COLLISION_START,
        cb_b_on_start=COLLISION_START,
        cb_a_on_end=COLLISION_END,
        cb_b_on_end=COLLISION_END
    )

# Grenades collide with Islands, Bullets, Players
create_default_relation(collision_group_grenades, collision_group_islands)
create_default_relation(collision_group_grenades, collision_group_bullets)
create_default_relation(collision_group_grenades, collision_group_players)

# Players collide with Islands, Bullets, (Grenades)
create_default_relation(collision_group_players, collision_group_islands)
create_default_relation(collision_group_players, collision_group_bullets)

# Bullets collide with Islands, Bullets, Turrets, (Players, Grenades)
create_default_relation(collision_group_bullets, collision_group_islands)
create_default_relation(collision_group_bullets, collision_group_bullets)
create_default_relation(collision_group_bullets, collision_group_turrets)

# Shield collides with Bullets, Grenades
create_default_relation(collision_group_shields, collision_group_bullets)
create_default_relation(collision_group_shields, collision_group_grenades)

# endregion


__all__ = (
    "collision_group_players", "collision_group_bullets", "collision_group_grenades", "collision_group_islands",
    "collision_group_turrets", "collision_group_shields", "all_groups"
)
