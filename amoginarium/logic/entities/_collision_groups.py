"""
amoginarium/logic/entities/_collision_groups.py

Project: amoginarium
Created: 13.04.2026
Authors: LukasKrah
"""

from ._base_group import BaseGroup

# class _GridCell:
#     wall_group: BaseGroup = BaseGroup()
#     __bullet_group: BaseGroup = BaseGroup()
#
#     def add_wall(self, wall: pg.sprite.Sprite) -> None:
#         wall.add(self.wall_group)
#
#     def remove_wall(self, wall: pg.sprite.Sprite) -> None:
#         wall.remove(self.wall_group)
#
#     def add_bullet(self, bullet: pg.sprite.Sprite) -> None:
#         bullet.add(self.__bullet_group)
#
#     def remove_bullet(self, bullet: pg.sprite.Sprite) -> None:
#         bullet.remove(self.__bullet_group)
#
#     def bullet_group(self) -> BaseGroup:
#         return self.__bullet_group


class GridCell:
    __walls: BaseGroup
    __bullets: BaseGroup

    def __init__(self) -> None:
        self.__walls = BaseGroup()
        self.__bullets = BaseGroup()

    @property
    def walls(self) -> BaseGroup:
        return self.__walls

    @property
    def bullets(self) -> BaseGroup:
        return self.__bullets


class _GridSystem:
    __grid_cells: dict[int, GridCell] = {}

    def __init__(self) -> None:
        for row_num in range(-1000, 2000):
            self.__grid_cells[row_num] = GridCell()

    def get_cells_by_num(self, min_row: int, max_row: int) -> list[GridCell]:
        return [self.__grid_cells[i] for i in range(min_row, max_row + 1)]

    def get_cells_by_pos(self, from_x: float, to_x: float) -> list[GridCell]:
        return self.get_cells_by_num(int(from_x / 500), int(to_x / 500))

    def get_num(self, from_x: float, to_x: float) -> tuple[int, int]:
        return int(from_x / 500), int(to_x / 500)


GridSystem = _GridSystem()
