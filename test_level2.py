"""
Level 2 test runner for the single-file prototype in `main.py`.
"""

import main as game


if __name__ == "__main__":
    setattr(game, "CURRENT_LEVEL", 2)
    game.rand_var = 222
    game.main()
