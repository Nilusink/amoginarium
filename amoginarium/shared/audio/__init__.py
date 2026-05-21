"""
Exports background players, sound effects, and audio management utilities.

Path: amoginarium/shared/audio/__init__.py
Project: amoginarium
Created: 25.03.2024
Authors: Nilusink
"""

from ._background import BackgroundPlayer
from ._effect import AK47, Cannon, ContinuousSoundEffect, CRAM, DeathSound, DistantPop
from ._effect import LargeExplosion, MetalPings, Minigun, Mortar, MutedBurst
from ._effect import OnHoverButtonSound, PotionDrink, PresetEffect, PRESETS
from ._effect import RandomizedEffect, ReloadGeneric, RocketSound
from ._effect import ScopedRandomizedEffect, Shotgun, SmallExplosion, Sniper
from ._effect import sound_effect_wrapper, sound_effects, SoundEffect
from ._sounds import sounds
