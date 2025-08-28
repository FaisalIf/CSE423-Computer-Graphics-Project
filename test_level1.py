"""
Level 1 test runner for the single-file prototype in `main.py`.

This keeps things minimal: it sets a level marker and a visible value
(`rand_var`) so you can confirm you're launching Level 1, then calls main().
"""

import main as game


if __name__ == "__main__":
    # Mark the intended level for future logic in main.py
    setattr(game, "CURRENT_LEVEL", 1)
    # Change an on-screen variable so the HUD text reflects this runner
    game.rand_var = 111
    
    # Start the prototype
    game.main()
