"""
Level 3 test runner for the single-file prototype in `main.py`.
"""

import main as game


if __name__ == "__main__":
    game.rand_var = 333
    game.main(3)
