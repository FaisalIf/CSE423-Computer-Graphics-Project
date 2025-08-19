from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..draw import text2d


class HUD:
    def __init__(self):
        self.paused = False
        self.menu_mode = 'main'  # 'main' or 'pause'
        self.score = 0
        self.checkpoint_uses = 3

    def draw_crosshair(self, scoped=False):
        if scoped:
            text2d(490, 400, "+")
            text2d(510, 400, "+")
        else:
            text2d(500, 400, "+")

    def draw_inventory(self, player):
        # simple slot text
        slots = ' '.join([f"[{i+1}]" for i in range(9)])
        text2d(300, 10, slots)

    def draw_score(self):
        text2d(850, 770, f"Score: {int(self.score)}")

    def draw_menu(self):
        if self.paused:
            text2d(420, 420, "PAUSED")
            text2d(400, 390, "Resume (ESC)")
            text2d(400, 360, "Load Checkpoint")
            text2d(400, 330, "Restart")

    def draw_radar(self):
        # minimal radar indicator text (visual circle needs lines, kept simple)
        text2d(20, 100, "(radar)")
