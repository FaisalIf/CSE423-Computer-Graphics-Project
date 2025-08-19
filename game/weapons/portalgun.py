from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..draw import draw_portal


class Portal:
    def __init__(self, color=(0, 0, 1)):
        self.pos = [None, None, None]
        self.active = False
        self.color = color
        self.scale = (1.0, 1.5)

    def place(self, pos, scale=None):
        self.pos = list(pos)
        self.active = True
        if scale is not None:
            self.scale = scale

    def draw(self):
        if not self.active:
            return
        glPushMatrix()
        try:
            glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        except Exception:
            # Guard against None positions
            glTranslatef(0, 0, 0)
        draw_portal(elliptical_scale=self.scale, color=self.color)
        glPopMatrix()


class PortalGun:
    def __init__(self, player):
        self.player = player
        self.blue = Portal((0, 0, 1))
        self.red = Portal((1, 0, 0))
        self.cooldown = 0.15
        self.time_since_fire = 0.0
        self.last_blue = True

    def update(self, dt):
        self.time_since_fire += dt

    def can_fire(self):
        return self.time_since_fire >= self.cooldown

    def place_portal(self, world):
        if not self.can_fire():
            return
        target = [self.player.pos[0], self.player.pos[1] + 60, 20]
        scale = (1.3, 2.0) if getattr(self.player, 'scoped', False) else (1.0, 1.5)
        if self.last_blue:
            self.blue.place(target, scale)
        else:
            self.red.place(target, scale)
        self.last_blue = not self.last_blue
        self.time_since_fire = 0.0

    def try_teleport(self, entity):
        if self.blue.active and self.red.active:
            # Simple overlap check near blue -> move to red
            if abs(entity.pos[0] - self.blue.pos[0]) < 10 and abs(entity.pos[1] - self.blue.pos[1]) < 10:
                entity.pos[0] = self.red.pos[0]
                entity.pos[1] = self.red.pos[1]
                entity.pos[2] = self.red.pos[2]
            # And vice versa
            elif abs(entity.pos[0] - self.red.pos[0]) < 10 and abs(entity.pos[1] - self.red.pos[1]) < 10:
                entity.pos[0] = self.blue.pos[0]
                entity.pos[1] = self.blue.pos[1]
                entity.pos[2] = self.blue.pos[2]

    def draw(self):
        self.blue.draw()
        self.red.draw()
