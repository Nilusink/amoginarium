#! venv/bin/python
from amoginarium.controllers import KeyboardController
from amoginarium.base import BaseGame


def main():
    game = BaseGame(debug=True, show_targets=False, time_multiplier=1)

    # create initial controller
    KeyboardController.get()

    game.mainloop()


if __name__ == "__main__":
    main()
