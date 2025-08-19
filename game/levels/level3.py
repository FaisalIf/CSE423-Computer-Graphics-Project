from .level_base import LevelScene


def create_scene():
    return LevelScene(difficulty=3, boss=True)
