from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from .base import Entity
from ..math3d import sub, norm
from ..draw import draw_enemy


class Enemy(Entity):
    def __init__(self, boss=False):
        super().__init__()
        self.radius = 12.0
        self.speed = 120.0 if not boss else 160.0
        self.color = (1, 0, 0) if not boss else (1, 0.5, 0)
        self.damage = 20 if not boss else 40
        self.boss = boss
        self.pulse = 0.0
        self.pulse_dir = 1.0
        self.fire_accum = 0.0

    def update(self, dt, world):
        # simple chase player
        to_player = sub(world.player.pos, self.pos)
        dir_ = norm(to_player)
        self.vel[0] = dir_[0] * self.speed
        self.vel[1] = dir_[1] * self.speed
        # bobbing pulse
        self.pulse += self.pulse_dir * dt * 2
        if self.pulse > 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1.0
        if self.pulse < 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1.0
        # integrate on ground plane
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] = 12.0

        # boss may shoot projectiles
        if self.boss:
            self.fire_accum += dt
            if self.fire_accum > 1.2:
                from ..weapons.base import Bullet
                bpos = [self.pos[0], self.pos[1], self.pos[2] + 5]
                bvel = [dir_[0] * 300, dir_[1] * 300, 0]
                world.bullets.append(Bullet(bpos, bvel, ttl=3.0, radius=3.0, color=(1, 0.5, 0), friendly=False))
                self.fire_accum = 0.0

        # collision with player
        if self.collides_with(world.player):
            world.player.take_damage(self.damage)
            if self.boss:
                world.player.vel[0] += -dir_[0] * 250
                world.player.vel[1] += -dir_[1] * 250
            else:
                self.alive = False

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        draw_enemy(self.pulse, self.color)
        glPopMatrix()
