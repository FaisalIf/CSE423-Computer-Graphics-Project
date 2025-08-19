from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..math3d import add, sub, mul, norm
from ..draw import draw_stickman, text2d


class Inventory:
    def __init__(self):
        # slots 1-9
        self.slots = [None] * 9
        self.selected = 0

    def select(self, idx):
        if 0 <= idx < len(self.slots):
            self.selected = idx

    def next(self, step):
        self.selected = (self.selected + step) % len(self.slots)


class Player:
    def __init__(self):
        self.pos = [0.0, 0.0, 20.0]
        self.vel = [0.0, 0.0, 0.0]
        self.color = (1, 1, 1)
        # collision radius used by generic Entity.collides_with
        self.radius = 6.0
        self.health = 100
        self.damage = 25
        self.speed = 200.0
        self.jump_v = 300.0
        self.grounded = True
        self.first_person = False
        self.scoped = False
        self.inventory = Inventory()
        self.ammo = 12
        self.max_ammo = 12

    def handle_input(self, keys):
        vx, vy = 0.0, 0.0
        if b'w' in keys:
            vy += 1
        if b's' in keys:
            vy -= 1
        if b'a' in keys:
            vx -= 1
        if b'd' in keys:
            vx += 1
        self.vel[0] = vx * self.speed
        self.vel[1] = vy * self.speed

    def update(self, dt):
        # gravity
        if not self.grounded:
            self.vel[2] -= 500 * dt
        # integrate
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] += self.vel[2] * dt
        # ground collision
        if self.pos[2] <= 20.0:
            self.pos[2] = 20.0
            self.vel[2] = 0.0
            self.grounded = True

    def jump(self):
        if self.grounded:
            self.vel[2] = self.jump_v
            self.grounded = False

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        draw_stickman(scale=1.0, color=self.color)
        glPopMatrix()

    def take_damage(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.health = 0

    def heal(self, amount):
        self.health = min(100, self.health + amount)

    def add_ammo(self, count):
        self.ammo = min(self.max_ammo, self.ammo + count)

    def render_ui(self):
        text2d(10, 770, f"HP: {self.health}   Ammo: {self.ammo}   Slot: {self.inventory.selected+1}")
