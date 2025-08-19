from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


class Item:
    def __init__(self, name):
        self.name = name
        self.pos = [0.0, 0.0, 10.0]
        self.vel = [0.0, 0.0, 0.0]
        self.alive = True

    def update(self, dt):
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] += self.vel[2] * dt
        if self.pos[2] > 10:
            self.vel[2] -= 300 * dt
        else:
            self.pos[2] = 10
            self.vel[2] = 0

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        if self.name == 'Vitae':
            glColor3f(0, 1, 0)
            glutSolidCube(6)
        elif self.name == 'Aegis':
            glColor3f(0, 1, 1)
            gluSphere(gluNewQuadric(), 4, 8, 8)
        elif self.name == 'Shard':
            glColor3f(1, 0, 1)
            gluCylinder(gluNewQuadric(), 2, 0.5, 8, 6, 1)
        glPopMatrix()


class Chest:
    def __init__(self):
        self.pos = [0.0, 0.0, 10.0]
        self.opened = False
        self.key_required = True
        self.contents = []  # items

    def try_open(self, player, world):
        if self.opened:
            return
        # proximity and simple key logic: assume player always has key if close
        dx = player.pos[0] - self.pos[0]
        dy = player.pos[1] - self.pos[1]
        if (dx*dx + dy*dy) ** 0.5 < 30:
            self.opened = True
            # throw out contents
            for i, item in enumerate(self.contents):
                item.pos = [self.pos[0], self.pos[1], 20]
                item.vel = [(-1)**i * 80, 60, 120]
                world.items.append(item)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glColor3f(0.7, 0.4, 0.2)
        glutSolidCube(20)
        glPopMatrix()
