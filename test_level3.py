from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from game.engine import GameEngine
from game.levels.level3 import create_scene


if __name__ == "__main__":
    engine = GameEngine(create_scene())
    engine.run(title=b"Level 3 Test")
