from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Core timing and loop use only GLUT callbacks and idle, per constraints.

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
ASPECT = WINDOW_WIDTH / WINDOW_HEIGHT


class Scene:
    def update(self, dt):
        pass

    def draw(self):
        pass

    def on_key(self, key):
        pass

    def on_special(self, key):
        pass

    def on_mouse(self, button, state, x, y):
        pass


class Camera:
    def __init__(self):
        self.mode = 'third'
        self.pos = [0.0, 500.0, 500.0]
        self.look = [0.0, 0.0, 0.0]
        self.up = [0.0, 0.0, 1.0]
        self.fovY = 120.0

    def apply(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fovY, ASPECT, 0.1, 1500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.pos[0], self.pos[1], self.pos[2], self.look[0], self.look[1], self.look[2], self.up[0], self.up[1], self.up[2])


class GameEngine:
    def __init__(self, scene):
        self.scene = scene
        self.camera = Camera()
        self._paused = False

    def _idle(self):
        # Fixed small timestep to avoid using extra GLUT timing APIs
        dt = 1.0 / 60.0
        if not self._paused:
            self.scene.update(dt)
        glutPostRedisplay()

    def _display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        if hasattr(self.scene, 'camera_hook'):
            self.scene.camera_hook(self.camera)
        self.camera.apply()
        self.scene.draw()
        glutSwapBuffers()

    def _keyboard(self, key, x, y):
        if key == b'\x1b':
            self._paused = not self._paused
        self.scene.on_key(key)

    def _special(self, key, x, y):
        self.scene.on_special(key)

    def _mouse(self, button, state, x, y):
        self.scene.on_mouse(button, state, x, y)

    def run(self, title=b"Demons & Portals"):
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        glutInitWindowPosition(0, 0)
        glutCreateWindow(title)
        glutDisplayFunc(self._display)
        glutKeyboardFunc(self._keyboard)
        glutSpecialFunc(self._special)
        glutMouseFunc(self._mouse)
        glutIdleFunc(self._idle)
        glutMainLoop()
