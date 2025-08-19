from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from game.engine import GameEngine
from game.levels.level1 import create_scene as scene1
from game.levels.level2 import create_scene as scene2
from game.levels.level3 import create_scene as scene3


if __name__ == "__main__":
    # start at level 1 for now
    engine = GameEngine(scene1())
    engine.run(title=b"Demons & Portals")
