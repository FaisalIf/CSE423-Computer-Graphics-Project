from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..math3d import add, sub, mul, norm, length


class Entity:
    def __init__(self):
        self.pos = [0.0, 0.0, 0.0]
        self.vel = [0.0, 0.0, 0.0]
        self.radius = 10.0
        self.alive = True

    def update(self, dt, world):
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] += self.vel[2] * dt

    def draw(self):
        pass

    def distance_to(self, other):
        dx = self.pos[0] - other.pos[0]
        dy = self.pos[1] - other.pos[1]
        dz = self.pos[2] - other.pos[2]
        return (dx*dx + dy*dy + dz*dz) ** 0.5

    def collides_with(self, other):
        # Be robust if either side lacks a radius attribute
        r_self = getattr(self, 'radius', 0.0)
        r_other = getattr(other, 'radius', 0.0)
        return self.distance_to(other) <= (r_self + r_other)
