from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL import GLUT as GLUTmod

# =============================================================
# Demons & Portals — Minimal 3D FPS-Puzzle (single-file, KISS)
# Only uses: GL / GLUT / GLU from PyOpenGL as allowed.
# No depth buffer. No extra OpenGL/GLUT functions beyond these.
# =============================================================

import math, random, time

# ------------------- Window / Camera Globals -------------------
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W/ WIN_H
fovY_default = 77.3
fovY_scoped  = 40.0

# camera modes
CAM_FIRST  = 0
CAM_THIRD  = 1
CAM_TOPDOWN = 2 
camera_mode = CAM_THIRD

# current FOV; updated when scoping
fovY = fovY_default

# third-person camera parameters
third_cam_back = 120.0
third_cam_side = 30.0
third_cam_height = 120.0
camera_smooth = 0.15
cam_eye = None
cam_cen = None

# --------------------------- Utils / Low-level ----------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


_COLORS = {
    'grey': (0.6, 0.6, 0.6),
    'dark_grey': (0.15, 0.15, 0.15),
    'orange': (1.0, 0.55, 0.0),
    'light_blue': (0.52, 0.74, 0.88),
    'light_brown': (0.87, 0.72, 0.53),
    'dark_brown': (0.35, 0.2, 0.1),
    'brown': (0.55, 0.33, 0.16),
    'gold': (0.9, 0.75, 0.2),
    'red': (0.9, 0.1, 0.1),
    'crimson': (0.86, 0.08, 0.24),
    'deep_crimson': (0.6, 0.0, 0.1),
    'mahogany': (0.30, 0.10, 0.10),
    'magenta': (0.9, 0.1, 0.9),
    'yellow': (0.95, 0.95, 0.1),
    'cyan': (0.1, 0.95, 0.95),
    'toothpaste': (0.1, 0.6, 0.6),
    'black': (0.0, 0.0, 0.0),
    'grass_green': (0.2, 0.8, 0.2),
    'white': (1.0, 1.0, 1.0),
}


def get_color(name):
    return _COLORS.get(name, (1.0, 1.0, 1.0))


def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in str(text):
        glutBitmapCharacter(GLUTmod.GLUT_BITMAP_9_BY_15, ord(ch))


# --------------------------- Core Entity ---------------------

class Entity:
    def __init__(self, x, y, z, rx=0, ry=0, rz=0, width=1, depth=1, height=1):
        self.x = x; self.y = y; self.z = z
        self.rx = rx; self.ry = ry; self.rz = rz
        self.width = width; self.depth = depth; self.height = height
        self.bbox_sync()

    def bbox_sync(self):
        # Treat (x,y,z) as center of the volume for AABB
        self.x_min = self.x - self.width/2;  self.x_max = self.x + self.width/2
        self.y_min = self.y - self.depth/2;  self.y_max = self.y + self.depth/2
        self.z_min = self.z - self.height/2; self.z_max = self.z + self.height/2

    def draw(self):
        pass

    def check_collision(self, other):
        return not (
            self.x_max < other.x_min or self.x_min > other.x_max or
            self.y_max < other.y_min or self.y_min > other.y_max or
            self.z_max < other.z_min or self.z_min > other.z_max
        )

    # Rotations around pivot points in the respective planes
    def rotate_x(self, rx, ay, az):
        self.rx += rx
        rad = math.radians(rx)
        dy = self.y - ay
        dz = self.z - az
        self.y = ay + dy * math.cos(rad) - dz * math.sin(rad)
        self.z = az + dy * math.sin(rad) + dz * math.cos(rad)
        self.bbox_sync()

    def rotate_y(self, ry, ax, az):
        self.ry += ry
        rad = math.radians(ry)
        dx = self.x - ax
        dz = self.z - az
        self.x = ax + dx * math.cos(rad) + dz * math.sin(rad)
        self.z = az - dx * math.sin(rad) + dz * math.cos(rad)
        self.bbox_sync()

    def rotate_z(self, rz, ax, ay):
        self.rz += rz
        rad = math.radians(rz)
        dx = self.x - ax
        dy = self.y - ay
        self.x = ax + dx * math.cos(rad) - dy * math.sin(rad)
        self.y = ay + dx * math.sin(rad) + dy * math.cos(rad)
        self.bbox_sync()

class Shape3D(Entity):
    quadric = gluNewQuadric()

    def __init__(self, color, x, y, z, rx, ry, rz, *dims):
        self.color = get_color(color)
        super().__init__(x, y, z, rx, ry, rz, *dims)

class Sphere(Shape3D):
    def __init__(self, color, x, y, z, rx, ry, rz, *dims):
        # If only a single radius was passed, expand to (r, r, r)
        if len(dims) == 1:
            r = dims[0]
            dims = (r, r, r)
        super().__init__(color, x, y, z, rx, ry, rz, *dims)

    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)
        glRotatef(self.rz, 0, 0, 1)
        # Use the three stored dimensions; for heads these are equal so it's round
        glScalef(self.width, self.depth, self.height)
        # Higher tessellation for a smoother, circular look
        gluSphere(self.quadric, 1, 24, 24)
        glPopMatrix()

class Box(Shape3D):
    def __init__(self, color, x, y, z, rx, ry, rz, *dims):
        super().__init__(color, x, y, z, rx, ry, rz, *dims)
    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)
        glRotatef(self.rz, 0, 0, 1)
        glScalef(self.width, self.depth, self.height)
        glutSolidCube(1)
        glPopMatrix()

class Cylinder(Shape3D):
    # Cylinder with configurable pivot anchor: 'center', 'base', or 'top'
    # Drawn as a GLU cylinder extruded along +Z from its local origin.
    def __init__(self, color, x, y, z, rx, ry, rz, radius=10, height=20, top_radius=None, anchor='center'):
        super().__init__(color, x, y, z, rx, ry, rz, radius*2, radius*2, height)
        self.radius = radius
        self.top_radius = radius if top_radius is None else top_radius
        self.height = height
        self.anchor = anchor  # 'center'|'base'|'top'
    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        # Position according to anchor so rotations pivot correctly
        if self.anchor == 'base':
            glTranslatef(self.x, self.y, self.z)
        elif self.anchor == 'top':
            glTranslatef(self.x, self.y, self.z)
        else:  # center
            glTranslatef(self.x, self.y, self.z - self.height/2)
        # Apply rotation at pivot
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)
        glRotatef(self.rz, 0, 0, 1)
        # For 'top' anchor, draw downwards by translating -height then extruding +Z
        if self.anchor == 'top':
            glTranslatef(0, 0, -self.height)
        # For 'base', start at base; for 'center', already moved to base-like start
        gluCylinder(self.quadric, self.radius, self.top_radius, self.height, 16, 1)
        glPopMatrix()

class CompoundEntity(Entity):
    def __init__(self, *entities):
        x = sum(e.x for e in entities)/len(entities)
        y = sum(e.y for e in entities)/len(entities)
        z = sum(e.z for e in entities)/len(entities)
        x_min = min(e.x_min for e in entities)
        y_min = min(e.y_min for e in entities)
        z_min = min(e.z_min for e in entities)
        x_max = max(e.x_max for e in entities)
        y_max = max(e.y_max for e in entities)
        z_max = max(e.z_max for e in entities)
        rx = 0; ry = 0; rz = 0
        width = x_max - x_min
        depth = y_max - y_min
        height = z_max - z_min
        super().__init__(x, y, z, rx, ry, rz, width, depth, height)
        self.x_min = x_min; self.y_min = y_min; self.z_min = z_min
        self.x_max = x_max; self.y_max = y_max; self.z_max = z_max
        self.entities = list(entities)
    def draw(self):
        for e in self.entities: e.draw()
    def rotate_x(self, rx):
        self.rx += rx
        for e in self.entities: e.rotate_x(rx, self.y, self.z)
    def rotate_y(self, ry):
        self.ry += ry
        for e in self.entities: e.rotate_y(ry, self.x, self.z)
    def rotate_z(self, rz):
        self.rz += rz
        for e in self.entities: e.rotate_z(rz, self.x, self.y)

# --------------------------- Game Models -----------------------

class Chest(CompoundEntity):
    def __init__(self, x, y, ground_z, rx=0, ry=0, rz=0, w=60, d=40, h=40):
        base_h = 0.6*h
        base_z = ground_z + base_h/2
        base = Box('dark_brown', x, y, base_z, rx, ry, rz, w, d, base_h)
        ins_z = ground_z + base_h
        ins_1 = Box('dark_brown', x, y, ins_z-10, rx, ry, rz, w-10, d-10, 0)
        ins_2 = Box('brown', x, y, ins_z+10, rx, ry, rz, w-10, d-10, 0)
        lid_h = h - base_h
        lid_z = ground_z + base_h + lid_h/2
        lid = Box('brown', x, y, lid_z, rx, ry, rz, w, d, lid_h)
        super().__init__(base, ins_1, lid, ins_2)
        self.closed = True
        self.contains = None  # will be set to item name
    def open(self):
        ins_1 = self.entities[1]
        lid = self.entities[2]
        ins_2 = self.entities[3]
        lid.rotate_x(-135, lid.y_max, lid.z_min)
        ins_2.rotate_x(-135, lid.y_max, lid.z_min)
        ins_1.color = get_color('gold')
        ins_2.color = get_color('dark_brown')
        self.closed = False
    def close(self):
        ins_1 = self.entities[1]
        lid = self.entities[2]
        ins_2 = self.entities[3]
        lid.rotate_x(135, lid.y_max, lid.z_min)
        ins_2.rotate_x(135, lid.y_max, lid.z_min)
        ins_1.color = get_color('dark_brown')
        ins_2.color = get_color('brown')
        self.closed = True
    def toggle(self):
        if self.closed: self.open()
        else: self.close()

class StickPlayer(CompoundEntity):
    def __init__(self, x, y, ground_z, rz):
        # Proportions inspired by reference
        self.leg_h = 40.0
        self.body_h = 40.0
        self.head_r = 12.0
        self.arm_h = 40.0
        self.arm_r = 5.0
        self.leg_r = 7.0
        self.body_r = 20.0
        self.shoulder_span = 46.0

        hip_z = ground_z + self.leg_h
        shoulder_z = hip_z + self.body_h
        head_center_z = shoulder_z + self.head_r + 4.0

        # Build components for bounds/collisions
        leg_left = Cylinder('grey', x - 7, y, hip_z, 0, 0, 0, radius=self.leg_r, height=self.leg_h, anchor='top')
        leg_right = Cylinder('grey', x + 7, y, hip_z, 0, 0, 0, radius=self.leg_r, height=self.leg_h, anchor='top')
        # Body rises upward from hip level
        body = Cylinder('orange', x, y, hip_z, 0, 0, 0, radius=self.body_r, height=self.body_h, anchor='base')
        # Arms hang down from the shoulder line
        arm_left = Cylinder('light_blue', x - self.shoulder_span/2, y, shoulder_z, 0, 0, 0, radius=self.arm_r, height=self.arm_h, anchor='top')
        arm_right = Cylinder('light_blue', x + self.shoulder_span/2, y, shoulder_z, 0, 0, 0, radius=self.arm_r, height=self.arm_h, anchor='top')
        head = Sphere('light_brown', x, y, head_center_z, 0, 0, 0, self.head_r)
        super().__init__(leg_left, leg_right, body, arm_left, arm_right, head)

        self.on_ground_z = ground_z
        self.anim = 0.0
        self.anim_dir = 0.015
        self.speed = 1.2
        self.jump_v = 0.0
        self.health = 100
        self.damage = 10
        self.inventory = {'handgun_ammo':24,'keys':1,'Nourishment':0,'Aegis':0,'Shard':0,'portalgun':0}
        self.active_slot = 1
        self.head_visible = True
        self.yaw = 0

    def head_entity(self):
        return self.entities[-1]

    def ensure_head_visibility(self, show):
        self.head_visible = show

    def walk_anim_tick(self):
        # swing legs a bit
        leg_left = self.entities[0]; leg_right = self.entities[1]
        if self.anim > 1 or self.anim < -1:
            self.anim_dir *= -1
        self.anim += self.anim_dir
        swing = 12.0 * math.sin(self.anim * math.pi)
        leg_left.rx = swing; leg_right.rx = -swing

    def move(self, dx, dy):
        self.x += dx; self.y += dy
        for e in self.entities:
            e.x += dx; e.y += dy; e.bbox_sync()
        self.bbox_sync()

    def stand_center_z(self):
        return self.on_ground_z + 0.5*self.leg_h

    def jump(self):
        if abs(self.z - self.stand_center_z()) < 0.2:
            self.jump_v = 6.5

    def physics(self):
        if self.jump_v != 0:
            self.z += self.jump_v
            for e in self.entities:
                e.z += self.jump_v; e.bbox_sync()
            self.jump_v -= 0.35
            if self.z <= self.stand_center_z():
                dz = self.stand_center_z() - self.z
                self.z += dz
                for e in self.entities:
                    e.z += dz; e.bbox_sync()
                self.jump_v = 0.0
        self.bbox_sync()

    def draw(self):
        hip_z = self.on_ground_z + self.leg_h
        shoulder_z = hip_z + self.body_h
        head_center_z = shoulder_z + self.head_r + 4.0

        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glRotatef(self.yaw, 0, 0, 1)

        # Legs
        glColor3f(*get_color('grey'))
        glPushMatrix(); glTranslatef(-7, 0, hip_z - self.leg_h); gluCylinder(Sphere.quadric, self.leg_r, self.leg_r, self.leg_h, 16, 1); glPopMatrix()
        glPushMatrix(); glTranslatef( 7, 0, hip_z - self.leg_h); gluCylinder(Sphere.quadric, self.leg_r, self.leg_r, self.leg_h, 16, 1); glPopMatrix()

        # Body
        glColor3f(*get_color('orange'))
        glPushMatrix(); glTranslatef(0, 0, hip_z); gluCylinder(Sphere.quadric, self.body_r, self.body_r, self.body_h, 16, 1); glPopMatrix()

        # Arms and simple stick weapon on right hand
        glColor3f(*get_color('light_blue'))
        glPushMatrix(); glTranslatef(-self.shoulder_span/2, 0, shoulder_z - self.arm_h); gluCylinder(Sphere.quadric, self.arm_r, self.arm_r, self.arm_h, 16, 1); glPopMatrix()
        glPushMatrix(); glTranslatef( self.shoulder_span/2, 0, shoulder_z - self.arm_h); gluCylinder(Sphere.quadric, self.arm_r, self.arm_r, self.arm_h, 16, 1)
        # weapon
        glPushMatrix(); glTranslatef(0, 0, self.arm_h - 2); glRotatef(90, 0, 1, 0); glColor3f(0.3,0.3,0.3); gluCylinder(Sphere.quadric, 3, 3, 30, 12, 1); glPopMatrix()
        glPopMatrix()

        # Head
        if self.head_visible:
            glColor3f(*get_color('light_brown'))
            glPushMatrix(); glTranslatef(0, 0, head_center_z); gluSphere(Sphere.quadric, self.head_r, 10, 10); glPopMatrix()

        glPopMatrix()

class Enemy(CompoundEntity):
    def __init__(self, x, y, ground_z, is_boss=False):
        # Boss gets a scarier, bigger model with grey head and black body
        if is_boss:
            body_col, head_col = 'black', 'grey'
            # slightly bigger boss
            body_h = 100.0
            body_r = 48.0
            head_r = 48.0
            # Scarier: add spikes (vertical cylinders) around head
            spike_r = 2.5
            spike_h = 30.0
            spike_count = 8
            spike_entities = []
            for i in range(spike_count):
                angle = 2 * math.pi * i / spike_count
                sx = x + (body_r + head_r + 10) * math.cos(angle)
                sy = y + (body_r + head_r + 10) * math.sin(angle)
                sz = ground_z + body_h + head_r + 10
                spike = Cylinder('grey', sx, sy, sz, 0, 0, 0, radius=spike_r, height=spike_h, anchor='base')
                spike_entities.append(spike)
        else:
            palette = ['red', 'orange', 'light_blue', 'cyan', 'yellow']
            body_col = random.choice(palette)
            head_col = random.choice([c for c in palette if c != body_col])
            # slightly bigger normal enemy
            body_h = 50.0
            body_r = 24.0
            head_r = 24.0
            spike_entities = []

        # Core parts
        body = Cylinder(body_col, x, y, ground_z, 0, 0, 0, radius=body_r, height=body_h, anchor='base')
        head = Sphere(head_col, x, y, ground_z + body_h + head_r, 0, 0, 0, head_r)

        # Two thin, black, upward-facing hands, slightly farther than body radius
        hand_r = 4.0
        hand_h = 30.0 if not is_boss else 50.0
        hx = body_r + 5.0
        handL = Cylinder('black', x - hx, y, ground_z + body_h, 0, 0, 0, radius=hand_r, height=hand_h, anchor='base')
        handR = Cylinder('black', x + hx, y, ground_z + body_h, 0, 0, 0, radius=hand_r, height=hand_h, anchor='base')

        # Compose entity
        if is_boss:
            super().__init__(body, head, handL, handR, *spike_entities)
        else:
            super().__init__(body, head, handL, handR)

        # Behavior/visuals (moved inside __init__)
        self.is_boss = is_boss
        self.base_color = get_color(body_col)
        self.pulse = 0.0
        self.speed = 0.1 if not is_boss else 0
        self.hp = 20 if not is_boss else 120
        self.projectiles = []  # boss only
        # give the boss an initial cooldown so it doesn't start firing instantly
        self.shoot_cool = 220 if is_boss else 0
        self._pulse_scale = 1.0
        # hit radius for bullet collision (horizontal plane)
        self.hit_radius = max(body_r, head_r) * 1.2
        # Boss lives represented by grey spikes around the head
        if is_boss:
            self.spikes = list(spike_entities)
        else:
            self.spikes = []

    def hit_by_bullet(self, dmg):
        """Apply bullet impact. Returns 'hit' or 'defeated' when enemy is done.
           For boss, remove one spike per hit; defeat when all spikes gone.
        """
        if self.is_boss:
            if self.spikes:
                # remove one life spike and from render list
                spike = self.spikes.pop()
                try:
                    self.entities.remove(spike)
                except ValueError:
                    pass
                return 'defeated' if len(self.spikes) == 0 else 'hit'
            # fallback to HP if no spikes present
            self.hp -= dmg
            return 'defeated' if self.hp <= 0 else 'hit'
        else:
            self.hp -= dmg
            return 'defeated' if self.hp <= 0 else 'hit'

    def update(self, target):
        # Very slow pulse
        self.pulse += 0.003
        s = 1.0 + 0.12 * math.sin(self.pulse)
        self._pulse_scale = s
        # Keep bbox updated for collisions
        for e in self.entities:
            e.width *= s; e.depth *= s; e.height *= s; e.bbox_sync()
            e.width /= s; e.depth /= s; e.height /= s

        # chase (speed is 0 for now per user setting)
        dx = target.x - self.x
        dy = target.y - self.y
        d = math.hypot(dx, dy) + 1e-6
        vx = self.speed * (dx / d)
        vy = self.speed * (dy / d)
        self.x += vx; self.y += vy
        for e in self.entities:
            e.x += vx; e.y += vy; e.bbox_sync()
        self.bbox_sync()

        if self.is_boss:
            self.shoot_cool -= 1
            if self.shoot_cool <= 0:
                # further reduce fire rate with a larger cooldown
                self.shoot_cool = 220
                bvx = 3.5 * (dx / d)
                bvy = 3.5 * (dy / d)
                # much bigger range
                self.projectiles.append({'x': self.x, 'y': self.y, 'z': self.z + 20, 'vx': bvx, 'vy': bvy, 'life': 2000})
            for b in self.projectiles:
                b['x'] += b['vx']; b['y'] += b['vy']
                b['life'] -= 1
            self.projectiles = [b for b in self.projectiles if b['life'] > 0]

    def draw(self):
        # Scale model about its center for pulsing visuals
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glScalef(self._pulse_scale, self._pulse_scale, self._pulse_scale)
        glTranslatef(-self.x, -self.y, -self.z)
        super().draw()
        glPopMatrix()

        if self.is_boss:
            # draw projectiles as small spheres
            glColor3f(1, 1, 0)
            for b in self.projectiles:
                glPushMatrix(); glTranslatef(b['x'], b['y'], b['z']); glScalef(5,5,5); gluSphere(Sphere.quadric,1,8,8); glPopMatrix()

# --------------------------- Weapons & Items -------------------

class Bullet:
    def __init__(self, x, y, z, vx, vy, dmg, max_dist=800):
        self.x=x; self.y=y; self.z=z
        self.vx=vx; self.vy=vy
        self.dmg=dmg
        self.dist=0
        self.max_dist=max_dist
    def update(self):
        self.x += self.vx; self.y += self.vy
        self.dist += math.hypot(self.vx, self.vy)
        return self.dist < self.max_dist
    def draw(self):
        glColor3f(*get_color('red'))
        glPushMatrix(); glTranslatef(self.x, self.y, self.z); glScalef(6,6,6); gluSphere(Sphere.quadric,1,8,8); glPopMatrix()

class Portal:
    def __init__(self, color_name):
        self.active=False
        self.x=0; self.y=0; self.z=20
        self.normal=(0,1,0)  # not physically used; visual only
        self.color = get_color(color_name)
    def place(self, x,y,z):
        self.active=True; self.x=x; self.y=y; self.z=z
    def draw(self):
        if not self.active: return
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        # draw flat cylinder (ellipse look by non-uniform scale)
        glRotatef(90,1,0,0)
        glScalef(1.6, 1.0, 1.0)
        gluCylinder(Sphere.quadric, 20, 20, 2, 24, 1)
        glPopMatrix()

# --------------------------- Camera ----------------------------

class Cam3rd:
    def __init__(self, ex, ey, ez, cx, cy, cz, ux=0, uy=0, uz=1):
        self.eye_x = ex; self.eye_y = ey; self.eye_z = ez
        self.cen_x = cx; self.cen_y = cy; self.cen_z = cz
        self.up_x = ux;  self.up_y = uy;  self.up_z = uz
    def move(self, dx, dy, dz):
        self.eye_x += dx; self.eye_y += dy; self.eye_z += dz
        self.cen_x += dx; self.cen_y += dy; self.cen_z += dz
    def get_cam(self):
        return (self.eye_x, self.eye_y, self.eye_z,
                self.cen_x, self.cen_y, self.cen_z,
                self.up_x,  self.up_y,  self.up_z)

# --------------------------- Game State ------------------------

GRID_Z = 10
floor = Box('toothpaste', 0, 0, GRID_Z/2, 0,0,0, 1000, 1000, GRID_Z)
player = StickPlayer(0, 0, GRID_Z, 0)
cam1 = Cam3rd(50, -200, 200, 0,0,0, 0,0,1)

# enemies, chests, keys, pickups
enemies = []
chests = []
key_positions = []  # simple pickups drawn as small boxes
pickups = []  # items tossed from chests: {'name':str,'x','y','z','vz'}
walls = []    # level boundary walls
world_bounds = None  # {'min_x':..,'max_x':..,'min_y':..,'max_y':..}

# gameplay
paused = True
menu_mode = 'title'  # 'title' at start, 'paused' later, None when playing
score = 0
start_time = None
best_score = 0

# inventory slots mapping (1..9)
# 1: handgun, 2: portalgun, 3.. consumables
inventory_slots = {
    1: 'handgun',
    2: 'portalgun',
    3: 'Nourishment',
    4: 'Aegis',
    5: 'Shard'
}

selected_slot = 1

# bullets
bullets = []

# portals
blue_portal = Portal('cyan')
red_portal  = Portal('red')

# scope
scoped = False
pre_scope_camera_mode = CAM_THIRD

# checkpoints
checkpoints = []
last_checkpoint = None
load_uses_left = 3

# level
current_level = 1
boss_spawned = False
boss_seen_alive = False
win_check_cooldown = 0

# --------------------------- Utilities ------------------------

def camera():
    global cam_eye, cam_cen
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # FOV (projection)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)

    if camera_mode == CAM_THIRD:
        # follow player with planar offsets relative to yaw, z locked
        yaw_rad = math.radians(player.yaw)
        fx, fy = math.cos(yaw_rad), math.sin(yaw_rad)  # forward
        rx, ry = -math.sin(yaw_rad), math.cos(yaw_rad) # right
        des_eye = (
            player.x - fx*third_cam_back + rx*third_cam_side,
            player.y - fy*third_cam_back + ry*third_cam_side,
            player.z + third_cam_height
        )
        des_cen = (player.x, player.y, player.z+40)
        # initialize smoothing targets
        if cam_eye is None: cam_eye = list(des_eye)
        if cam_cen is None: cam_cen = list(des_cen)
        # smooth follow (LERP)
        cam_eye[0] += (des_eye[0]-cam_eye[0])*camera_smooth
        cam_eye[1] += (des_eye[1]-cam_eye[1])*camera_smooth
        cam_eye[2] += (des_eye[2]-cam_eye[2])*camera_smooth
        cam_cen[0] += (des_cen[0]-cam_cen[0])*(camera_smooth*1.2)
        cam_cen[1] += (des_cen[1]-cam_cen[1])*(camera_smooth*1.2)
        cam_cen[2] += (des_cen[2]-cam_cen[2])*(camera_smooth*1.2)
        gluLookAt(cam_eye[0],cam_eye[1],cam_eye[2], cam_cen[0],cam_cen[1],cam_cen[2], 0,0,1)
    elif camera_mode == CAM_FIRST:
        # first person from head (no smoothing for responsiveness)
        head = player.head_entity()
        ex,ey,ez = head.x, head.y, head.z
        dx = math.cos(math.radians(player.yaw))
        dy = math.sin(math.radians(player.yaw))
        cam_eye = None; cam_cen = None  # reset smoothing when switching back later
        gluLookAt(ex,ey,ez, ex+dx*50, ey+dy*50, ez, 0,0,1)
    elif camera_mode == CAM_TOPDOWN:
        gluLookAt(0, 0, 2500, 0, 0, 0, 1, 0, 0)

# --------------------------- Level Setup ----------------------

def clear_level():
    enemies.clear(); chests.clear(); key_positions.clear(); pickups.clear(); walls.clear()
    bullets.clear(); blue_portal.active=False; red_portal.active=False
    checkpoints.clear()
    globals()['world_bounds'] = None

def setup_level(level):
    global current_level, last_checkpoint, start_time, boss_spawned, boss_seen_alive, win_check_cooldown
    current_level = level
    clear_level()
    boss_spawned = False
    boss_seen_alive = False
    win_check_cooldown = 120  # frames to wait before evaluating win
    # place player at origin
    place_player(0,0)
    player.inventory['portalgun'] = 1 if level>=1 else 0  # L1 finds it in a chest
    player.inventory['keys'] = 1 if level==1 else 0
    player.health = 100; player.damage = 10
    # checkpoints
    checkpoints.extend([(-200,-200), (0,0), (300,200)])
    last_checkpoint = (0,0)
    # keys scattered (esp L2+)
    if level > 1:
        for _ in range(2 if level==1 else (3 if level==2 else 0)):
            key_positions.append((random.randint(-300,300), random.randint(-300,300)))
    # chests
    if level > 1:
        for i in range(2 if level==1 else 3):
            cx = random.randint(-250,250); cy = random.randint(-250,250)
            c = Chest(cx, cy, GRID_Z)
            c.contains = random.choice(['ammo','Nourishment','Aegis','Shard','portalgun'])
            chests.append(c)
    # enemies
    if level==1:
        field_size = 1600
        build_level3_bounds(field_size, 2000)
        place_player(-field_size + 120, 0)
    elif level==2:
        for i in range(8): enemies.append(Enemy(random.randint(-350,350), random.randint(-350,350), GRID_Z, False))
    else:
        # Level 3 field: half of previous (from 3200 to 1600)
        field_size = 1600
        for i in range(10): enemies.append(Enemy(random.randint(-field_size,field_size), random.randint(-field_size,field_size), GRID_Z, False))
        # Place boss near a corner
        enemies.append(Enemy(field_size-100, field_size-100, GRID_Z, True))
        # Fallback: ensure there's at least one boss; if not, spawn one near origin
        if not any(e.is_boss for e in enemies):
            enemies.append(Enemy(180,0, GRID_Z, True))
        boss_spawned = any(e.is_boss for e in enemies)
        # Build boundary walls and grass floor for the whole field
        build_level3_bounds(field_size)
    # timer/score
    start_time = time.time()

def build_level3_bounds(field_size, wall_height = 200):
    # Set floor to cover entire field in grass green
    global floor
    size = (field_size + 150) * 2  # a bit larger than field for coverage
    # base floor set to a dark wood tone; tiles will be drawn on top
    floor = Box('dark_brown', 0, 0, GRID_Z/2, 0,0,0, size, size, GRID_Z)
    # Build four tall mahogany walls bordering the field
    wall_thick = 20
    wall_height = wall_height
    half = field_size
    zc = GRID_Z + wall_height/2
    # Left and right walls (parallel to Y axis)
    walls.append(Box('mahogany', -half-wall_thick/2, 0, zc, 0,0,0, wall_thick, half*2 + wall_thick*2, wall_height))
    walls.append(Box('mahogany',  half+wall_thick/2, 0, zc, 0,0,0, wall_thick, half*2 + wall_thick*2, wall_height))
    # Bottom and top walls (parallel to X axis)
    walls.append(Box('mahogany', 0, -half-wall_thick/2, zc, 0,0,0, half*2 + wall_thick*2, wall_thick, wall_height))
    walls.append(Box('mahogany', 0,  half+wall_thick/2, zc, 0,0,0, half*2 + wall_thick*2, wall_thick, wall_height))
    # Set playable bounds to inside the walls
    globals()['world_bounds'] = {'min_x': -half, 'max_x': half, 'min_y': -half, 'max_y': half}

# --------------------------- Player Helpers -------------------

def place_player(x,y):
    dx = x - player.x
    dy = y - player.y
    player.move(dx,dy)

def apply_pickup(name):
    if name=='ammo':
        player.inventory['handgun_ammo'] += 12
    elif name=='Nourishment':
        player.health = clamp(player.health+25, 0, 100)
    elif name=='Aegis':
        player.inventory['Aegis'] += 1
    elif name=='Shard':
        player.damage += 5
    elif name=='portalgun':
        player.inventory['portalgun'] = 1

# --------------------------- UI (2D) --------------------------

def draw_inventory_bar():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    slot_w = 70; slot_h = 50; x0 = 20; y0 = 20
    for i in range(1,10):
        x = x0 + (i-1)*(slot_w+6)
        y = y0
        if i==selected_slot:
            glColor3f(1,1,1)
        else:
            glColor3f(0.5,0.5,0.5)
        glBegin(GL_QUADS)
        glVertex2f(x,y); glVertex2f(x+slot_w,y); glVertex2f(x+slot_w,y+slot_h); glVertex2f(x,y+slot_h)
        glEnd()
        draw_text(x+6, y+slot_h-18, str(i))
        # item label
        name = inventory_slots.get(i,'')
        if name:
            draw_text(x+20, y+20, name[:6])
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_crosshair(scoped_mode):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    cx, cy = WIN_W/2, WIN_H/2 - 21
    glColor3f(1,1,1)
    glBegin(GL_LINES)
    if scoped_mode:
        # screen-wide cross shaped crosshair
        glVertex2f(cx-200, cy); glVertex2f(cx+200, cy)
        glVertex2f(cx, cy-200); glVertex2f(cx, cy+200)
    else:
        glVertex2f(cx-15, cy); glVertex2f(cx+15, cy)
        glVertex2f(cx, cy-15); glVertex2f(cx, cy+15)
    glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_radar():
    # very simple 2D circle + dots around player showing nearby objects
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    cx, cy, R = WIN_W-110, 110, 90
    # circle approx
    glColor3f(1,1,1)
    glBegin(GL_LINE_LOOP)
    for i in range(40):
        a = 2*math.pi*i/40
        glVertex2f(cx + R*math.cos(a), cy + R*math.sin(a))
    glEnd()
    # plot enemies/keys/chests within 400 units
    def to_local(px,py):
        dx = px - player.x; dy = py - player.y
        d = math.hypot(dx,dy)
        if d>400: return None
        scale = R/400.0
        # rotate by -yaw so forward is up
        yaw_rad = -math.radians(player.yaw)
        lx = dx*math.cos(yaw_rad) - dy*math.sin(yaw_rad)
        ly = dx*math.sin(yaw_rad) + dy*math.cos(yaw_rad)
        return (cx + lx*scale, cy + ly*scale)
    glPointSize(5)
    glBegin(GL_POINTS)
    glColor3f(1,0,0)
    for e in enemies:
        p = to_local(e.x,e.y)
        if p: glVertex2f(p[0],p[1])
    glColor3f(1,1,0)
    for kx,ky in key_positions:
        p = to_local(kx,ky)
        if p: glVertex2f(p[0],p[1])
    glColor3f(0,1,1)
    for c in chests:
        p = to_local(c.x,c.y)
        if p: glVertex2f(p[0],p[1])
    glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_hud_stats():
    # Fixed-position HUD text in top-left corner using 2D orthographic projection
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor3f(1,1,1)
    x, y = 10, WIN_H - 24
    text = f"HP: {int(player.health)}  Ammo: {player.inventory['handgun_ammo']}  Keys: {player.inventory['keys']}  Level: {current_level}  Score: {int(score)}  Best: {int(best_score)}  Loads:{load_uses_left}"
    glRasterPos2f(x, y)
    font = globals().get('GLUT_BITMAP_HELVETICA_18', None)
    if font is not None:
        for ch in text:
            glutBitmapCharacter(font, ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# --------------------------- Drawing --------------------------

def draw_floor():
    # Base slab
    floor.draw()
    # Wood tile overlay: draw alternating quads in two wood tones
    # Only paint within current world bounds if available
    wb = globals().get('world_bounds')
    if wb:
        # Static, world-aligned grid covering the whole field so tiles don't move with the player
        tile = 200.0
        z = GRID_Z + 0.1  # slightly above slab to avoid z-fighting
        x0 = math.floor(wb['min_x'] / tile) * tile
        x1 = math.ceil(wb['max_x'] / tile) * tile
        y0 = math.floor(wb['min_y'] / tile) * tile
        y1 = math.ceil(wb['max_y'] / tile) * tile
        ix_max = int((x1 - x0) / tile)
        iy_max = int((y1 - y0) / tile)
        # pass 1: draw one color on (ix+iy) even
        glColor3f(*get_color('brown'))
        glBegin(GL_QUADS)
        for ix in range(ix_max):
            for iy in range(iy_max):
                if ((ix + iy) & 1) == 0:
                    x = x0 + ix*tile
                    y = y0 + iy*tile
                    glVertex3f(x,     y,     z)
                    glVertex3f(x+tile,y,     z)
                    glVertex3f(x+tile,y+tile,z)
                    glVertex3f(x,     y+tile,z)
        glEnd()
        # pass 2: other color on (ix+iy) odd
        glColor3f(*get_color('dark_brown'))
        glBegin(GL_QUADS)
        for ix in range(ix_max):
            for iy in range(iy_max):
                if ((ix + iy) & 1) == 1:
                    x = x0 + ix*tile
                    y = y0 + iy*tile
                    glVertex3f(x,     y,     z)
                    glVertex3f(x+tile,y,     z)
                    glVertex3f(x+tile,y+tile,z)
                    glVertex3f(x,     y+tile,z)
        glEnd()
    # draw level-3 walls if present
    for w in walls:
        w.draw()

def draw_keys():
    glColor3f(1,1,0)
    for kx,ky in key_positions:
        glPushMatrix(); glTranslatef(kx,ky,GRID_Z+8); glScalef(10,10,5); glutSolidCube(1); glPopMatrix()

# --------------------------- Game Loop ------------------------

def display():
    glClear(GL_COLOR_BUFFER_BIT)  # no depth buffer bit per instructions
    camera()

    # world
    draw_floor()
    for c in chests: c.draw()
    for e in enemies: e.draw()
    draw_keys()
    for b in bullets: b.draw()
    blue_portal.draw(); red_portal.draw()
    # player model (hide head when in first-person)
    player.ensure_head_visibility(camera_mode==CAM_THIRD)
    player.draw()

    # HUD
    draw_inventory_bar()
    draw_radar()
    draw_hud_stats()
    if scoped:
        draw_crosshair(True)
    else:
        draw_crosshair(False)

    # Menus
    if paused:
        draw_menu()

    glutSwapBuffers()

# --------------------------- Menus ----------------------------

def draw_menu():
    # menu_mode: 'title', 'paused', 'win', 'lose'
    if menu_mode == 'win':
        title = 'You Win'
    elif menu_mode == 'lose':
        title = 'You Lost'
    elif menu_mode == 'paused':
        title = 'Paused'
    else:
        title = 'Demons & Portals'
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    # dark overlay
    glColor3f(0,0,0)
    glBegin(GL_QUADS)
    glVertex2f(0,0); glVertex2f(WIN_W,0); glVertex2f(WIN_W,WIN_H); glVertex2f(0,WIN_H)
    glEnd()
    draw_text(WIN_W/2-120, WIN_H-120, title)
    if menu_mode=='title':
        draw_text(WIN_W/2-200, WIN_H-170, 'Press N for New Game | F1/F2/F3 for Level Tests')
    elif menu_mode=='paused':
        draw_text(WIN_W/2-250, WIN_H-170, 'ESC Resume | L Load Checkpoint | R Restart Level')
    elif menu_mode in ('win','lose'):
        draw_text(WIN_W/2-140, WIN_H-170, f'Total Score: {int(score)}')
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# --------------------------- Update ---------------------------

def animate():
    global score, best_score, paused, win_check_cooldown
    if not paused:
        # movement animation and physics
        player.walk_anim_tick()
        player.physics()
    # bullets
        alive = []
        for b in bullets:
            if b.update(): alive.append(b)
        bullets[:] = alive
        # enemies
        for e in enemies:
            e.update(player)
            # enemy collision / damage
            if e.check_collision(player):
                if e.is_boss:
                    player.health -= 25
                    # knockback
                    dx = player.x - e.x; dy=player.y - e.y; d=math.hypot(dx,dy)+1e-6
                    player.move(30*dx/d, 30*dy/d)
                else:
                    player.health -= 10
                    enemies.remove(e)
                break
            # boss projectile hits
            if e.is_boss:
                for pb in list(e.projectiles):
                    # approximate hit on player center
                    if math.hypot(pb['x']-player.x, pb['y']-player.y) < 20:
                        player.health -= 10
                        e.projectiles.remove(pb)
        # bullet hit enemies (improved collision + boss lives logic)
        for b in list(bullets):
            for e in list(enemies):
                dx = b.x - e.x; dy = b.y - e.y
                hit_r = getattr(e, 'hit_radius', 20)
                if math.hypot(dx, dy) < hit_r:
                    if hasattr(e, 'hit_by_bullet'):
                        outcome = e.hit_by_bullet(b.dmg)
                        if outcome == 'defeated':
                            enemies.remove(e)
                            if e.is_boss:
                                score_add(500)
                                pause_game('win')
                            else:
                                score_add(20)
                        # remove bullet on any hit
                        try: bullets.remove(b)
                        except: pass
                        break
                    else:
                        e.hp -= b.dmg
                        if e.hp <= 0:
                            enemies.remove(e)
                            score_add(20 if not e.is_boss else 200)
                        try: bullets.remove(b)
                        except: pass
                        break
        # pickups physics
        for p in pickups:
            p['vz'] -= 0.3
            p['z'] += p['vz']
            if p['z'] <= GRID_Z+8:
                p['z'] = GRID_Z+8; p['vz']=0
        # pickup collection
        for p in list(pickups):
            if math.hypot(p['x']-player.x, p['y']-player.y) < 30:
                apply_pickup(p['name'])
                pickups.remove(p)
                score_add(5)
        # keys collection
        for k in list(key_positions):
            if math.hypot(k[0]-player.x, k[1]-player.y) < 30:
                player.inventory['keys'] += 1
                key_positions.remove(k)
                score_add(3)
        # portals teleport
        if blue_portal.active and red_portal.active:
            if math.hypot(player.x-blue_portal.x, player.y-blue_portal.y) < 25:
                player.move(red_portal.x - player.x, red_portal.y - player.y)
        # checkpoints trigger
        for cx,cy in checkpoints:
            if math.hypot(player.x-cx, player.y-cy) < 20:
                set_checkpoint((cx,cy))
        # health check / win conditions
        if player.health<=0:
            pause_game('lose')
        # Secondary win guard: if no bosses remain and we had one, declare win
        if current_level==3 and win_check_cooldown==0:
            if any(e.is_boss for e in enemies):
                globals()['boss_seen_alive'] = True
            if boss_spawned and boss_seen_alive and not any(e.is_boss for e in enemies):
                pause_game('win')
                score_add(500)
        if win_check_cooldown>0:
            win_check_cooldown -= 1
        # score as time-based (speedrun style)
        if start_time:
            elapsed = time.time()-start_time
            # higher score for faster clear -> we subtract elapsed each tick
            pass
    glutPostRedisplay()

# --------------------------- Score ----------------------------

def score_add(v):
    global score, best_score
    score += v
    best_score = max(best_score, score)

# --------------------------- Checkpoints ----------------------

def set_checkpoint(pos):
    global last_checkpoint
    last_checkpoint = pos

def load_checkpoint():
    global load_uses_left
    if last_checkpoint and load_uses_left>0:
        load_uses_left -= 1
        place_player(last_checkpoint[0], last_checkpoint[1])

# --------------------------- Input ----------------------------

moving = {'w':False,'a':False,'s':False,'d':False}


def keys(key, x, y):
    global paused, menu_mode, camera_mode, scoped, fovY, selected_slot
    k = key
    if k==b'\x1b':  # ESC
        if paused:
            paused=False; menu_mode=None
        else:
            pause_game('paused')
        return

    if paused:
        if k in (b'n', b'N') and menu_mode=='title':
            paused=False; menu_mode=None
            setup_level(1)
            return
        if k in (b'r', b'R') and menu_mode=='paused':
            setup_level(current_level)
            paused=False; menu_mode=None
            return
        if k in (b'l', b'L') and menu_mode=='paused':
            load_checkpoint(); paused=False; menu_mode=None
            return
        # allow switching test levels from menu too
        if k==b'1': setup_level(1); return
        if k==b'2': setup_level(2); return
        if k==b'3': setup_level(3); return
        return

    # gameplay keys
    if k in (b'w',b'a',b's',b'd'):
        moving[k.decode()] = True
    if k==b' ':
        player.jump()
    if k in (b'p', b'P'):
        toggle_perspective()
    if k==b'k':
        # test: toggle nearest chest
        if chests:
            nearest = min(chests, key=lambda c: math.hypot(c.x-player.x,c.y-player.y))
            if math.hypot(nearest.x-player.x, nearest.y-player.y) < 80:
                open_chest(nearest)
    # inventory hotkeys 1..9
    if k in [bytes(str(i),'ascii') for i in range(1,10)]:
        selected_slot = int(k.decode())
    if k in (b't', b'T'):
        set_camera_mode(CAM_TOPDOWN)


def key_up(key, x, y):
    if key in (b'w',b'a',b's',b'd'):
        moving[key.decode()] = False


def special_keys(key, x, y):
    # arrow keys adjust third-person camera in the X/Y plane (Z locked)
    global third_cam_back, third_cam_side
    if camera_mode == CAM_THIRD:
        if key == GLUT_KEY_LEFT:
            third_cam_side -= 5
        if key == GLUT_KEY_RIGHT:
            third_cam_side += 5
        if key == GLUT_KEY_UP:
            third_cam_back = max(60.0, third_cam_back - 5)  # move closer
        if key == GLUT_KEY_DOWN:
            third_cam_back += 5  # move further back
    # level test shortcuts
    if key == GLUT_KEY_F1: setup_level(1)
    if key == GLUT_KEY_F2: setup_level(2)
    if key == GLUT_KEY_F3: setup_level(3)


def clicks(button, state, x, y):
    global scoped, pre_scope_camera_mode, fovY
    if state != GLUT_DOWN: return
    # map window x,y not used — just actions
    if button == GLUT_LEFT_BUTTON:
        # left click: shoot / place portal / use consumable depending on slot
        do_primary_action()
    if button == GLUT_RIGHT_BUTTON:
        # right click: scope
        if not scoped:
            scoped = True
            pre_scope_camera_mode = camera_mode
            set_camera_mode(CAM_FIRST)
            set_fov(True)
        else:
            scoped = False
            if pre_scope_camera_mode == CAM_THIRD:
                set_camera_mode(CAM_THIRD)
            set_fov(False)
    # wheel
    if button == 3:  # wheel up
        change_slot(1)
    if button == 4:  # wheel down
        change_slot(-1)

# --------------------------- Actions --------------------------

def set_fov(scope):
    global fovY
    fovY = fovY_scoped if scope else fovY_default


def set_camera_mode(mode):
    global camera_mode, cam_eye, cam_cen
    camera_mode = mode
    # reset smoothing accumulators when switching modes to avoid laggy snaps
    cam_eye = None
    cam_cen = None
    # hide head in first person to avoid blocking view; show in third
    if mode == CAM_FIRST:
        player.ensure_head_visibility(False)
    else:
        player.ensure_head_visibility(True)


def toggle_perspective():
    if scoped:
        return  # scoped locks to first person
    set_camera_mode(CAM_FIRST if camera_mode==CAM_THIRD else CAM_THIRD)


def change_slot(delta):
    global selected_slot
    selected_slot = ((selected_slot-1 + delta) % 9) + 1


def do_primary_action():
    # 1 = handgun, 2 = portalgun, 3.. consumables
    item = inventory_slots.get(selected_slot, '')
    if item=='handgun':
        shoot_handgun()
    elif item=='portalgun' and player.inventory['portalgun']:
        place_portal()
    elif item=='Nourishment' and player.inventory['Nourishment']>0:
        player.inventory['Nourishment']-=1; apply_pickup('Nourishment')
    elif item=='Aegis' and player.inventory['Aegis']>0:
        player.inventory['Aegis']-=1; # simple: temporary invuln not implemented: KISS
    elif item=='Shard':
        # passive already applied via pickups
        pass


def shoot_handgun():
    if player.inventory['handgun_ammo']<=0: return
    player.inventory['handgun_ammo']-=1
    # bullet spawns at player head / gun tip forward
    head = player.head_entity()
    ang = math.radians(player.yaw)
    vx = math.cos(ang)*16
    vy = math.sin(ang)*16
    dmg = player.damage
    bullets.append(Bullet((head.x + math.cos(ang) * 55), (head.y + math.sin(ang) * 55), head.z - 15, vx, vy, dmg))

portal_toggle = True  # alternate blue/red

def place_portal():
    global portal_toggle
    # place portal some distance in facing direction
    ang = math.radians(player.yaw)
    px = player.x + math.cos(ang)*120
    py = player.y + math.sin(ang)*120
    pz = GRID_Z+20
    if portal_toggle:
        blue_portal.place(px,py,pz)
    else:
        red_portal.place(px,py,pz)
    portal_toggle = not portal_toggle


def open_chest(c:Chest):
    if c.closed:
        if player.inventory['keys']>0:
            player.inventory['keys']-=1
            c.open()
            # toss item out
            if c.contains:
                pickups.append({'name':c.contains, 'x':c.x+random.randint(-10,10), 'y':c.y+random.randint(-10,10), 'z':GRID_Z+15, 'vz':5.0})
                c.contains=None

# --------------------------- Movement Tick --------------------

def update_movement():
    # WASD planar move
    dx=0; dy=0
    sp = player.speed
    # yaw update from A/D keys (rotate while held)
    yaw_step = 0.8  # degrees per tick while held (even slower)
    # Swap A/D rotation directions
    if moving['a']:
        player.yaw = (player.yaw + yaw_step) % 360
    if moving['d']:
        player.yaw = (player.yaw - yaw_step) % 360
    # convert WASD relative to yaw
    dir_forward = math.radians(player.yaw)
    fx, fy = math.cos(dir_forward), math.sin(dir_forward)
    if moving['w']: dx += fx*sp; dy += fy*sp
    if moving['s']: dx -= fx*sp; dy -= fy*sp
    if dx or dy:
        # apply movement, but clamp within world bounds if defined
        new_x = player.x + dx
        new_y = player.y + dy
        wb = globals().get('world_bounds')
        if wb is not None:
            # keep a small inner padding to avoid intersecting wall geometry
            pad = 10
            new_x = clamp(new_x, wb['min_x']+pad, wb['max_x']-pad)
            new_y = clamp(new_y, wb['min_y']+pad, wb['max_y']-pad)
            dx = new_x - player.x
            dy = new_y - player.y
        if dx or dy:
            player.move(dx,dy)

# --------------------------- Idle -----------------------------

def idle():
    if not paused:
        update_movement()
    animate()

# --------------------------- Init / Main ----------------------

def pause_game(mode='paused'):
    global paused, menu_mode
    paused=True; menu_mode=mode


def main(level=None):
    global ASPECT
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # NO DEPTH
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Demons & Portals")

    # listeners
    glutDisplayFunc(display)
    glutKeyboardFunc(keys)
    glutKeyboardUpFunc(key_up)
    glutSpecialFunc(special_keys)
    glutMouseFunc(clicks)
    glutIdleFunc(idle)

    # projection once (will reset per frame in camera())
    glMatrixMode(GL_PROJECTION)
    gluPerspective(fovY, ASPECT, 0.1, 5000)

    # clear color
    bg = get_color('dark_grey')
    glClearColor(bg[0], bg[1], bg[2], 1)

    # start at title menu or jump straight into a requested level
    if level is not None:
        setup_level(level)
        # enter gameplay directly
        global paused, menu_mode
        paused = False
        menu_mode = None
    else:
        pause_game('title')

    glutMainLoop()

# --------------------------- Helpers for Tests ----------------
# F1: Level 1 — easy/tutorial, harmless-ish enemies
# F2: Level 2 — more enemies, keys hidden
# F3: Level 3 — fast enemies + boss

if __name__ == "__main__":
    main()
