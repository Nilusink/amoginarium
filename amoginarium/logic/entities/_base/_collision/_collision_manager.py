"""
amoginarium/logic/entities/_base/_collision/_collision_manager.py

Central manager for handling all game collision logic.
Registers groups, handles hitboxes, and establishes bidirectional collision relationships.

Project: amoginarium
Created: 16.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared.collision_detection import CollisionManager, CollisionCallback

from ._collision_types import CollisionType, HitboxTypes


# noinspection DuplicatedCode
class _GameCollisions:
    """
    Manages the collision groups and relations for the game world.
    Handles the registration of hitboxes and bidirectional collision callbacks.
    """

    __slots__ = (
        "collision_manager",
        "COLLISION_START",
        "COLLISION_END",
        "collision_group_players",
        "collision_group_bullets",
        "collision_group_grenades",
        "collision_group_islands",
        "collision_group_turrets",
        "collision_group_shields",
        "collision_group_items",
        "all_groups",
        "hitboxes",
        "_registered_relations",
        "__exception_num"
    )

    collision_manager: tp.Final[CollisionManager]
    COLLISION_START: CollisionCallback
    COLLISION_END: CollisionCallback

    collision_group_players: CollisionType.GroupID
    collision_group_bullets: CollisionType.GroupID
    collision_group_grenades: CollisionType.GroupID
    collision_group_islands: CollisionType.GroupID
    collision_group_turrets: CollisionType.GroupID
    collision_group_shields: CollisionType.GroupID
    collision_group_items: CollisionType.GroupID

    all_groups: list[CollisionType.GroupID]
    hitboxes: dict[CollisionType.GroupID, HitboxTypes]
    _registered_relations: set[tuple[int, int]]
    __exception_num: int

    def __init__(self) -> None:
        self.collision_manager = CollisionManager(
            base_cell_size=500,
            level_dividers=[10],
        )
        self._registered_relations = set()
        self.__exception_num = -1

    def init(self, callback_start: CollisionCallback, callback_end: CollisionCallback) -> None:
        """
        Initializes the collision groups and sets up the default relations.
        :param callback_start: The callback triggered when a collision begins.
        :param callback_end: The callback triggered when a collision ends.
        """
        self.COLLISION_START = callback_start
        self.COLLISION_END = callback_end
        self._setup_groups()

    def _setup_groups(self) -> None:
        """Internal method to define collision groups and their relationships."""
        self.collision_group_players = self.collision_manager.add_group(max_level=0)
        self.collision_group_bullets = self.collision_manager.add_group(max_level=1, hitbox_type="circle")
        self.collision_group_grenades = self.collision_manager.add_group(max_level=1, hitbox_type="circle")
        self.collision_group_islands = self.collision_manager.add_group(max_level=0)
        self.collision_group_turrets = self.collision_manager.add_group(max_level=0)
        self.collision_group_shields = self.collision_manager.add_group(max_level=0, hitbox_type="obb")
        self.collision_group_items = self.collision_manager.add_group(max_level=0)

        self.all_groups = [
            self.collision_group_players, self.collision_group_bullets, self.collision_group_grenades,
            self.collision_group_islands, self.collision_group_turrets, self.collision_group_shields,
            self.collision_group_items,
        ]

        self.hitboxes = {  # type: ignore
            group: self.collision_manager.get_hitbox(group) for group in self.all_groups
        }

        self.create_relations(
            self.collision_group_players,
            [
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_grenades,
                self.collision_group_items,
                self.collision_group_shields
            ]
        )
        self.create_relations(
            self.collision_group_bullets,
            [
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_turrets,
                self.collision_group_players,
                self.collision_group_grenades,
                self.collision_group_shields
            ]
        )
        self.create_relations(
            self.collision_group_grenades,
            [
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_players,
                self.collision_group_shields
            ]
        )
        self.create_relations(
            self.collision_group_islands,
            [
                self.collision_group_players,
                self.collision_group_bullets,
                self.collision_group_grenades,
                self.collision_group_shields
            ]
        )
        self.create_relations(
            self.collision_group_turrets,
            [
                self.collision_group_bullets
            ]
        )
        self.create_relations(
            self.collision_group_shields,
            [
                self.collision_group_bullets,
                self.collision_group_grenades,
                self.collision_group_islands,
                self.collision_group_players
            ]
        )

        self.create_relations(
            self.collision_group_items,
            [
                self.collision_group_players,
                self.collision_group_islands
            ]
        )

    def create_relations(self, group_a: CollisionType.GroupID, targets: list[CollisionType.GroupID]) -> None:
        """
        Registers bidirectional collision relations between a group and multiple target groups.
        Prevents redundant registration if the relation already exists.
        :param group_a: The ID of the first collision group.
        :param targets: A list of group IDs to collide with.
        """
        for group_b in targets:
            if group_a <= group_b:
                rel_key = (group_a, group_b)
            else:
                rel_key = (group_b, group_a)

            if rel_key in self._registered_relations:
                continue

            self.collision_manager.create_relation(
                group_a_id=group_a,
                group_b_id=group_b,
                cb_a_on_start=self.COLLISION_START,
                cb_b_on_start=self.COLLISION_START,
                cb_a_on_end=self.COLLISION_END,
                cb_b_on_end=self.COLLISION_END
            )
            self._registered_relations.add(rel_key)

    def add_exception(self) -> int:
        """
        Registers a new collision exception rule and returns its unique identifier.
        :return: A unique integer identifier for the collision exception.
        :rtype: int
        """
        self.__exception_num += 1
        return self.__exception_num

GameCollisions: tp.Final[_GameCollisions] = _GameCollisions()
