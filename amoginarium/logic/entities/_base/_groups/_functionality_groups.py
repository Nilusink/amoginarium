"""
amoginarium/logic/entities/_base/_groups/_functionality_groups.py

Contains logical groups that apply global physics properties.
Includes FrictionXAffected and GravityAffected for batch physics processing.

Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

import typing as tp

from amoginarium.shared import LogicGameEntityLike
from amoginarium import pv

from ._base_group import BaseGroup


class _GravityAffected(BaseGroup[LogicGameEntityLike]):
    """Logic group handling gravity calculations for entities."""
    __slots__ = ()

    @property
    def gravity(self) -> float:
        """
        Get the current gravity constant adjusted by the global acceleration factor.
        :return: The calculated gravity value.
        """
        return 9.81 * pv.global_vars.get_acceleration_factor()

    def calculate_gravity(self, _delta: float) -> None:
        """
        Apply gravity to the Y-axis acceleration of all entities in the group.
        :param _delta: Time elapsed since the last frame.
        """
        for sprite in self.entities():
            sprite.acceleration.y = self.gravity


class _FrictionXAffected(BaseGroup[LogicGameEntityLike]):
    """Logic group handling horizontal friction calculations for entities."""
    __slots__ = ()

    @property
    def friction(self) -> float:
        """
        Get the friction coefficient.
        :return: Friction value.
        """
        return 60.0

    def calculate_friction(self, _delta: float) -> None:
        """
        Calculate and apply horizontal friction to entities
        based on their current velocity.
        :param _delta: Time elapsed since the last frame.
        """
        friction: float = self.friction
        for sprite in self.entities():
            sprite.acceleration.x = (
                    (
                            sprite.acceleration.x
                            - (sprite.velocity.x * 0.01)
                    )
                    * friction
            )


GravityAffected: tp.Final[_GravityAffected] = _GravityAffected()
FrictionXAffected: tp.Final[_FrictionXAffected] = _FrictionXAffected()
