"""
Provides centralized debugging, performance decorators, and console formatting.

| ``Path``: amoginarium/shared/debugging/__init__.py
| ``Project``: amoginarium
| ``Created``: 25.01.2024
| ``Authors``: Nilusink, LukasKrah
"""

from ._console_colors import CC, get_fg_color
from ._decoators import cum_timer, run_with_debug, timeit, do_not_call
from ._utils import get_caller_name, print_ic_style, print_with_prefix
