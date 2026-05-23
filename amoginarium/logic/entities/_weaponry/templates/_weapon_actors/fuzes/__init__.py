"""
Exposes fuze implementations and a registry mapping for weapon actors.

| Path: amoginarium/logic/entities/_weaponry/templates/_weapon_actors/fuzes/__init__.py
| Project: amoginarium
| Created: 08.05.2026
| Authors: Nilusink
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._fuzes import AltitudeFuze, PositionFuze, ProximityFuze, TTLFuze, TTLMultFuze

if TYPE_CHECKING:
    from ._base import BaseFuze

FUZES: dict[str, type[BaseFuze]] = {
    "ttl": TTLFuze,
    "ttl_mult": TTLMultFuze,
    "distance": PositionFuze,
    "proximity": ProximityFuze,
    "alt": AltitudeFuze,
}
