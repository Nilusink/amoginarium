#! venv/bin/python
from amoginarium.controllers import KeyboardController
from amoginarium.base import BaseGame

import sys

sys.setrecursionlimit(10000)


def main():
    game = BaseGame(debug=True, show_targets=False, time_multiplier=1)

    # create initial controller
    KeyboardController.get()
    game.load_map("assets/maps/tutorial.json")
    game.mainloop()


if __name__ == "__main__":
    main()
