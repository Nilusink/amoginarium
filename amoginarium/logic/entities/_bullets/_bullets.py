"""
amoginarium/logic/entities/_bullets/bullets.py

Project: amoginarium
Created: 31.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations
import numpy as np

from amoginarium.shared.utility import Vec2
from amoginarium.shared import DummyCIDs

from ._base_bullet import Bullet


class MortarShell(Bullet):
    _CID = DummyCIDs.mortar_bullet

    _default_hp = 0.5
    _weight = 8

    _default_base_damage = 40
    _default_ttl = 6
    _default_explosion_radius = 150
    _default_explosion_damage = 50
    _default_size = Vec2().from_cartesian(40, 20)

    __slots__ = ()


class ClusterMortarShell(MortarShell):
    _default_cluster_depth = 2
    _default_cluster_amount = 3
    _default_cluster_spread = np.pi / 5
    _default_cluster_fuze_ttl_mult = .3
    _default_cluster_step_explosion = 0
    _default_cluster_last_step_ttl = 3

    __slots__ = ()


class SniperBullet(Bullet):
    _weight = 5

    _default_size = 15
    _default_base_damage = 15

    __slots__ = ()


class FlakBullet(Bullet):
    _weight = 5

    _default_size = 18
    _default_base_damage = 30

    _default_explosion_radius = 128
    _default_explosion_damage = 40

    __slots__ = ()


class CRAMBullet(Bullet):
    _CID = DummyCIDs.cram

    _default_size = 9
    _default_base_damage = .1

    _default_explosion_damage = 0.1
    _default_explosion_radius = 15

    __slots__ = ()


class SkyShieldBullet(Bullet):
    _CID = DummyCIDs.cram

    _weight = 1.5
    _default_size = 18
    _default_base_damage = 30

    _default_cluster_depth = 1
    _default_cluster_amount = 11
    _default_cluster_fuze_ttl_mult = .02
    _default_cluster_spread = 1.5
    _default_cluster_size_mult = .3
    _default_cluster_step_explosion = 10
    _default_cluster_last_step_ttl = .07

    __slots__ = ()
