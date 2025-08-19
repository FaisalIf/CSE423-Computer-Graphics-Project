from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from .base import Weapon, Bullet


class Handgun(Weapon):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.reload_time = 1.0
        self.reloading = 0.0

    def update(self, dt):
        super().update(dt)
        if self.reloading > 0.0:
            self.reloading -= dt
            if self.reloading <= 0.0:
                self.player.ammo = self.player.max_ammo

    def fire(self, world):
        if self.reloading > 0.0:
            return
        if not self.can_fire():
            return
        if self.player.ammo <= 0:
            return
        # shoot along player's forward (assume +Y)
        origin = [self.player.pos[0], self.player.pos[1] + 10, self.player.pos[2]]
        vel = [0, 500, 0]
        # Scope: faster bullet, larger radius to simulate accuracy/one-shot feel
        if getattr(self.player, 'scoped', False):
            vel = [0, 700, 0]
            radius = 3.5
        else:
            radius = 2.5
        world.bullets.append(Bullet(origin, vel, ttl=2.0, radius=radius, color=(1, 0, 0), friendly=True))
        self.player.ammo -= 1
        self.reset_cd()

    def reload(self):
        if self.player.ammo < self.player.max_ammo and self.reloading <= 0.0:
            self.reloading = self.reload_time
