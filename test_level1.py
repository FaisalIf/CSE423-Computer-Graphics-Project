"""
Level 1 test runner for the single-file prototype in `main.py`.

This keeps things minimal: it sets a level marker and a visible value
(`rand_var`) so you can confirm you're launching Level 1, then calls main().
"""

import main as game


if __name__ == "__main__":
    game.rand_var = 111
    game.main(1)
