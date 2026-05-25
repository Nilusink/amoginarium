"""
Exposes map handling functionality for the logic layer.

| ``Path``: amoginarium/logic/map/__init__.py
| ``Project``: amoginarium
| ``Created``: 15.03.2026
| ``Authors``: Nilusink
"""

from ._cgenerator import array_get, iterate_chunk
from ._generator import generate_chunk_noise
from ._json_serialize import Encoder, preprocess
from ._map_handler import save_map, to_str
