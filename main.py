#! venv/bin/python
# from amoginarium.shared.controllers import KeyboardController
import sys

from amoginarium.base import BaseGame

sys.setrecursionlimit(10000)


def main():
    game = BaseGame(debug=True, show_targets=False, time_multiplier=1)

    # create initial controller
    # KeyboardController.get()
    game.load_map("assets/maps/test.json")
    # game.load_map("generated_map.json")
    game.mainloop()


if __name__ == "__main__":
    main()
