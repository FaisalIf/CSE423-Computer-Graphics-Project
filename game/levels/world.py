from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..draw import draw_floor


class World:
    def __init__(self):
        self.player = None
        self.enemies = []
        self.bullets = []
        self.items = []
        self.chests = []
        self.portalgun = None
        self.checkpoints = []  # list of positions
        self.last_checkpoint = None

    def update(self, dt):
        # items
        for it in list(self.items):
            it.update(dt)
        # bullets
        for b in list(self.bullets):
            b.update(dt)
            if not b.alive:
                self.bullets.remove(b)
        # enemies
        for e in list(self.enemies):
            e.update(dt, self)
            if self.portalgun:
                self.portalgun.try_teleport(e)
            if not e.alive:
                self.enemies.remove(e)
        # chests
        for c in self.chests:
            c.try_open(self.player, self)

        # player-portal interaction
        if self.portalgun:
            self.portalgun.try_teleport(self.player)

    def draw(self):
        draw_floor(600)
        for c in self.chests:
            c.draw()
        for it in self.items:
            it.draw()
        for e in self.enemies:
            e.draw()
        for b in self.bullets:
            b.draw()
        if self.portalgun:
            self.portalgun.draw()

    def save_checkpoint(self):
        self.last_checkpoint = list(self.player.pos)

    def load_checkpoint(self):
        if self.last_checkpoint is not None:
            self.player.pos = list(self.last_checkpoint)
