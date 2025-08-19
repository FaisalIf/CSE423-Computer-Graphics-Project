from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..math3d import *
from ..draw import draw_bullet


class Bullet:
    def __init__(self, pos, vel, ttl=2.0, radius=2.0, color=(1, 0, 0), friendly=True):
        self.pos = list(pos)
        self.vel = list(vel)
        self.ttl = ttl
        self.radius = radius
        self.color = color
        self.alive = True
        self.friendly = friendly

    def update(self, dt):
        if not self.alive:
            return
        self.ttl -= dt
        if self.ttl <= 0:
            self.alive = False
            return
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] += self.vel[2] * dt

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        draw_bullet(radius=self.radius, color=self.color)
        glPopMatrix()


class Weapon:
    def __init__(self):
        self.cooldown = 0.2
        self.time_since_fire = 0.0

    def update(self, dt):
        self.time_since_fire += dt

    def can_fire(self):
        return self.time_since_fire >= self.cooldown

    def reset_cd(self):
        self.time_since_fire = 0.0
