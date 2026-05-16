import typing as tp

from amoginarium.shared.utility import Vec2

from .collision_event import CollisionCallback, CollisionEvent

class CollisionManager:
    def __init__(
        self, base_cell_size: float = 100.0, level_dividers: list[int] = None
    ) -> None: ...
    def add_group(
        self, max_level: int, is_static: bool = False, hitbox_type: str = "aabb"
    ) -> int: ...
    def clear_all_entities(self) -> None: ...
    def register_entity(
        self,
        group_id: int,
        instance: tp.Any,
        position: Vec2 | None = None,
        size: Vec2 | None = None,
        centered: bool = False,
        rotation: float = 0.0,
        positions: list[Vec2] | None = None,
        radius: float | None = None,
        ignore_collisions: int | list[int] | None = None,
        is_active: bool = True,
    ) -> int: ...
    def delete_entity(self, group_id: int, entity_id: int) -> None: ...
    def update_entity(
        self,
        group_id: int,
        entity_id: int,
        position: Vec2 | None = None,
        size: Vec2 | None = None,
        centered: bool | None = None,
        rotation: float | None = None,
        positions: list[Vec2] | None = None,
        shift_history: bool = True,
        radius: float | None = None,
        ignore_collisions: int | list[int] | None = None,
        is_active: bool | None = None,
    ) -> None: ...
    def create_relation(
        self,
        group_a_id: int,
        group_b_id: int,
        cb_a_on_start: CollisionCallback | None = None,
        cb_a_on_end: CollisionCallback | None = None,
        cb_b_on_start: CollisionCallback | None = None,
        cb_b_on_end: CollisionCallback | None = None,
    ) -> int: ...
    def calculate_all_collisions(self) -> None: ...
    def calculate_collisions(self, relation_ids: list[int]) -> None: ...
    def get_points(self, group_id: int, entity_id: int) -> list[Vec2]: ...
    def manual_collision(
        self,
        group_ids: list[int],
        start_position: Vec2,
        end_position: Vec2,
        size: Vec2 | None = None,
        hitbox_type: str = "point",
        centered: bool = False,
        rotation: float = 0.0,
        start_positions: list[Vec2] | None = None,
        radius: float | None = None,
        ignore_collisions: int | list[int] | None = None,
    ) -> list[CollisionEvent]: ...
    def get_hitbox(self, group_id: int) -> str: ...
    def get_position(self, group_id: int, entity_id: int) -> Vec2 | None: ...
    def get_size(self, group_id: int, entity_id: int) -> Vec2 | None: ...
    def get_radius(self, group_id: int, entity_id: int) -> float: ...
