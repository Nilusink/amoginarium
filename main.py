"""
Run amoginarium.

Path: main.py
Project: amoginarium
Created: 25.01.2024
Authors: Nilusink, LukasKrah
"""

# from amoginarium.shared.controllers import KeyboardController  # noqa: ERA001
import sys

from amoginarium.base import BaseGame

sys.setrecursionlimit(10000)


def main() -> None:
    game = BaseGame(debug=True, show_targets=True, time_multiplier=1)

    # create initial controller
    # KeyboardController.get()
    game.load_map("assets/maps/tutorial.json")
    # game.load_map("generated_map.json")
    game.mainloop()


if __name__ == "__main__":
    main()
