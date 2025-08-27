from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

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
camera_mode = CAM_THIRD

# third-person camera state (follows player)
# Lock Z (height) and move only in X/Y based on player's aim.
third_cam_back = 160.0   # how far behind the player (along -forward)
third_cam_side = 0.0     # lateral offset (right is +)
third_cam_height = 90.0  # fixed height above player
camera_smooth = 0.15     # smoothing factor for camera follow
cam_eye = None           # smoothed eye position
cam_cen = None           # smoothed center position

# active perspective FOV
fovY = fovY_default

# --------------------------- Colors ----------------------------
COLORS = {
    "dark_grey": (0.1, 0.1, 0.1),
    'brown': (0.396, 0.067, 0),
    'dark_brown': (0.251, 0.059, 0.024),
    'gold': (0.996, 0.839, 0),
    'red': (1, 0, 0),
    'toothpaste': (0.788, 0.933, 0.973),
    'dark_blue': (0.149, 0.278, 0.51),
    'blue': (0.2, 0.5, 1.0),
    'cyan': (0.0, 0.9, 0.9),
    'green': (0.0, 1.0, 0.0),
    'white': (1.0, 1.0, 1.0),
    'black': (0.0, 0.0, 0.0),
    'yellow': (1.0, 1.0, 0.0),
    'magenta': (1.0, 0.0, 1.0)
}

def get_color(name):
    return COLORS[name]

# --------------------------- UI Text ---------------------------

def draw_text(x, y, text, font=None):
    if font is None:
        # default to GLUT helvetica if available (resolved at runtime)
        font = globals().get('GLUT_BITMAP_HELVETICA_18', None)
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    if font is not None:
        for ch in text:
            glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --------------------------- Math ------------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# --------------------------- Entities --------------------------

class Entity:
    def __init__(self, x, y, z, rx, ry, rz, *dims):
        # Dimensions
        if len(dims) == 1:
            self.width = self.depth = self.height = dims[0]
        elif len(dims) == 2:
            self.width = self.depth = dims[0]
            self.height = dims[1]
        elif len(dims) == 3:
            self.width, self.depth, self.height = dims

        # Center
        self.x = x; self.y = y; self.z = z
        self.rx = rx; self.ry = ry; self.rz = rz

        # Bounding box (AABB — not updated on rotation intentionally)
        self.x_min = x - self.width/2
        self.y_min = y - self.depth/2
        self.z_min = z - self.height/2
        self.x_max = self.x_min + self.width
        self.y_max = self.y_min + self.depth
        self.z_max = self.z_min + self.height

    def bbox_sync(self):
        # Only used if we change center/scale directly (not with rotation)
        self.x_min = self.x - self.width/2
        self.y_min = self.y - self.depth/2
        self.z_min = self.z - self.height/2
        self.x_max = self.x_min + self.width
        self.y_max = self.y_min + self.depth
        self.z_max = self.z_min + self.height

    def check_collision(self, other):
        return (self.x_min <= other.x_max and self.x_max >= other.x_min and
                self.y_min <= other.y_max and self.y_max >= other.y_min and
                self.z_min <= other.z_max and self.z_max >= other.z_min)

    # anchored rotations (AABB unchanged by design — symmetric models preferred)
    def rotate_x(self, rx, ay=0, az=0):
        self.rx += rx
        dy = self.y - ay
        dz = self.z - az
        rad = math.radians(rx)
        self.y = ay + dy * math.cos(rad) - dz * math.sin(rad)
        self.z = az + dy * math.sin(rad) + dz * math.cos(rad)
        self.bbox_sync()

    def rotate_y(self, ry, ax=0, az=0):
        self.ry += ry
        dx = self.x - ax
        dz = self.z - az
        rad = math.radians(ry)
        self.x = ax + dx * math.cos(rad) + dz * math.sin(rad)
        self.z = az - dx * math.sin(rad) + dz * math.cos(rad)
        self.bbox_sync()

    def rotate_z(self, rz, ax=0, ay=0):
        self.rz += rz
        dx = self.x - ax
        dy = self.y - ay
        rad = math.radians(rz)
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
        super().__init__(color, x, y, z, rx, ry, rz, *dims)
    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)
        glRotatef(self.rz, 0, 0, 1)
        glScalef(self.width, self.depth, self.height)
        gluSphere(self.quadric, 1, 10, 16)
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
    # tiny height cylinders used as portal rings / bullets etc.
    def __init__(self, color, x, y, z, rx, ry, rz, radius=10, height=2):
        super().__init__(color, x, y, z, rx, ry, rz, radius*2, radius*2, height)
        self.radius = radius
        self.height = height
    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)
        glRotatef(self.rz, 0, 0, 1)
        gluCylinder(self.quadric, self.radius, self.radius, self.height, 16, 1)
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
        w, h = 40, 80
        leg_h = 0.4 * h
        leg_w = 0.1 * w
        leg_z = ground_z + leg_h/2
        leg_off = w/4 - leg_w/2
        hip_z = ground_z + leg_h
        hip_w = w/2
        hip_h = leg_w
        body_h = leg_h
        body_w = leg_w
        body_z = ground_z + leg_h + body_h/2
        sho_z = hip_z + body_h
        sho_w = hip_w
        arm_h = 0.7 * leg_h
        arm_z = sho_z - arm_h/2
        head_h = 0.1 * h
        head_z = ground_z + h - head_h/2
        leg1 = Box('dark_blue', x-leg_off, y, leg_z, 0, 0, 0, leg_w, leg_h)
        leg2 = Box('dark_blue', x+leg_off, y, leg_z, 0, 0, 0, leg_w, leg_h)
        hip  = Box('dark_blue', x, y, hip_z, 0, 0, 0, hip_w, hip_h, hip_h)
        body = Box('dark_blue', x, y, body_z, 0, 0, 0, body_w, body_h)
        sho  = Box('dark_blue', x, y, sho_z, 0, 0, 0, sho_w, hip_h, hip_h)
        arm1 = Box('dark_blue', x-leg_off, y, arm_z, 0, 0, 0, leg_w, arm_h)
        arm2 = Box('dark_blue', x+leg_off, y, arm_z, 0, 0, 0, leg_w, arm_h)
        head = Sphere('dark_blue', x, y, head_z, 0, 0, 0, head_h)
        super().__init__(leg1, leg2, hip, body, sho, arm1, arm2, head)
        self.anim = 0
        self.anim_dir = 0.0015
        self.speed = 3.0
        self.jump_v = 0.0
        self.on_ground_z = ground_z
        self.health = 100
        self.damage = 10
        self.inventory = {
            'handgun_ammo': 24,
            'keys': 1,
            'Nourishment': 0,
            'Aegis': 0,
            'Shard': 0,
            'portalgun': 0,
        }
        self.active_slot = 1  # 1..9
        self.head_visible = True
        self.yaw = 0  # facing (deg)
    def head_entity(self):
        return self.entities[-1]
    def ensure_head_visibility(self, show):
        self.head_visible = show
        self.head_entity().color = get_color('dark_blue') if show else get_color('black')
    def walk_anim_tick(self):
        leg1 = self.entities[0]; leg2 = self.entities[1]
        if self.anim > 1 or self.anim < -1:
            self.anim_dir *= -1
        self.anim += self.anim_dir
        ay1 = (leg1.y_max + leg1.y_min)/2
        ay2 = (leg2.y_max + leg2.y_min)/2
        leg1.rotate_x(7*self.anim, ay1, leg1.z_max)
        leg2.rotate_x(-7*self.anim, ay2, leg2.z_max)
    def move(self, dx, dy):
        self.x += dx; self.y += dy
        for e in self.entities:
            e.x += dx; e.y += dy; e.bbox_sync()
        self.bbox_sync()
    def jump(self):
        if abs(self.z - (self.on_ground_z+40)) < 0.1:  # simple grounded check
            self.jump_v = 6.5
    def physics(self):
        if self.jump_v != 0:
            # update vertical (apply gravity)
            self.z += self.jump_v
            for e in self.entities:
                e.z += self.jump_v; e.bbox_sync()
            self.jump_v -= 0.35
            if self.z <= self.on_ground_z+40:
                dz = (self.on_ground_z+40) - self.z
                self.z += dz
                for e in self.entities:
                    e.z += dz; e.bbox_sync()
                self.jump_v = 0.0
        self.bbox_sync()

class Enemy(CompoundEntity):
    def __init__(self, x, y, ground_z, is_boss=False):
        body = Sphere('red' if not is_boss else 'magenta', x, y, ground_z+30, 0,0,0, 18)
        head = Sphere('red' if not is_boss else 'yellow', x, y, ground_z+50, 0,0,0, 10)
        super().__init__(body, head)
        self.is_boss = is_boss
        self.base_color = body.color
        self.pulse = 0.0
        self.speed = 1.2 if not is_boss else 1.9
        self.hp = 20 if not is_boss else 120
        self.projectiles = []  # boss only
        self.shoot_cool = 0
    def update(self, target):
        # pulse
        self.pulse += 0.1
        s = 1.0 + 0.05*math.sin(self.pulse)
        for e in self.entities:
            e.width *= s; e.depth *= s; e.height *= s; e.bbox_sync()
            e.width /= s; e.depth /= s; e.height /= s
        # chase
        dx = target.x - self.x
        dy = target.y - self.y
        d = math.hypot(dx, dy)+1e-6
        vx = self.speed * (dx/d)
        vy = self.speed * (dy/d)
        self.x += vx; self.y += vy
        for e in self.entities:
            e.x += vx; e.y += vy; e.bbox_sync()
        self.bbox_sync()
        if self.is_boss:
            self.shoot_cool -= 1
            if self.shoot_cool <= 0:
                self.shoot_cool = 90
                # shoot projectile toward player
                bvx = 3.0 * (dx/d)
                bvy = 3.0 * (dy/d)
                self.projectiles.append({'x': self.x, 'y': self.y, 'z': self.z+20, 'vx': bvx, 'vy': bvy, 'life': 400})
            # update boss projectiles
            for b in self.projectiles:
                b['x'] += b['vx']; b['y'] += b['vy']
                b['life'] -= 1
            self.projectiles = [b for b in self.projectiles if b['life']>0]
    def draw(self):
        super().draw()
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
    else:
        # first person from head (no smoothing for responsiveness)
        head = player.head_entity()
        ex,ey,ez = head.x, head.y, head.z
        dx = math.cos(math.radians(player.yaw))
        dy = math.sin(math.radians(player.yaw))
        cam_eye = None; cam_cen = None  # reset smoothing when switching back later
        gluLookAt(ex,ey,ez, ex+dx*50, ey+dy*50, ez, 0,0,1)

# --------------------------- Level Setup ----------------------

def clear_level():
    enemies.clear(); chests.clear(); key_positions.clear(); pickups.clear()
    bullets.clear(); blue_portal.active=False; red_portal.active=False
    checkpoints.clear()

def setup_level(level):
    global current_level, last_checkpoint, start_time
    current_level = level
    clear_level()
    # place player at origin
    place_player(0,0)
    player.inventory['portalgun'] = 1 if level>=1 else 0  # L1 finds it in a chest
    player.inventory['keys'] = 1 if level==1 else 0
    player.health = 100; player.damage = 10
    # checkpoints
    checkpoints.extend([(-200,-200), (0,0), (300,200)])
    last_checkpoint = (0,0)
    # keys scattered (esp L2+)
    for _ in range(2 if level==1 else (3 if level==2 else 0)):
        key_positions.append((random.randint(-300,300), random.randint(-300,300)))
    # chests
    for i in range(2 if level==1 else 3):
        cx = random.randint(-250,250); cy = random.randint(-250,250)
        c = Chest(cx, cy, GRID_Z)
        c.contains = random.choice(['ammo','Nourishment','Aegis','Shard','portalgun'])
        chests.append(c)
    # enemies
    if level==1:
        for i in range(4): enemies.append(Enemy(random.randint(-200,200), random.randint(-200,200), GRID_Z, False))
    elif level==2:
        for i in range(8): enemies.append(Enemy(random.randint(-350,350), random.randint(-350,350), GRID_Z, False))
    else:
        for i in range(10): enemies.append(Enemy(random.randint(-400,400), random.randint(-400,400), GRID_Z, False))
        enemies.append(Enemy(350,350, GRID_Z, True))
    # timer/score
    start_time = time.time()

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
    cx, cy = WIN_W/2, WIN_H/2
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

# --------------------------- Drawing --------------------------

def draw_floor():
    floor.draw()

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
    draw_text(10, WIN_H-30, f"HP: {int(player.health)}  Ammo: {player.inventory['handgun_ammo']}  Keys: {player.inventory['keys']}  Level: {current_level}  Score: {int(score)}  Best: {int(best_score)}  Loads:{load_uses_left}")
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
    title = 'Demons & Portals' if menu_mode=='title' else 'Paused'
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
    else:
        draw_text(WIN_W/2-250, WIN_H-170, 'ESC Resume | L Load Checkpoint | R Restart Level')
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# --------------------------- Update ---------------------------

def animate():
    global score, best_score, paused
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
        # bullet hit enemies
        for b in list(bullets):
            for e in list(enemies):
                if abs(b.x - e.x) < 20 and abs(b.y - e.y) < 20:
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
            pause_game('paused')
        if current_level==3 and all(not e.is_boss for e in enemies):
            # boss dead => win
            pause_game('paused')
            score_add(500)
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
    vx = math.cos(ang)*8.0
    vy = math.sin(ang)*8.0
    dmg = player.damage
    bullets.append(Bullet(head.x, head.y, head.z, vx, vy, dmg))

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
    yaw_step = 2.2  # degrees per tick while held
    if moving['a']:
        player.yaw = (player.yaw - yaw_step) % 360
    if moving['d']:
        player.yaw = (player.yaw + yaw_step) % 360
    # convert WASD relative to yaw
    dir_forward = math.radians(player.yaw)
    fx, fy = math.cos(dir_forward), math.sin(dir_forward)
    if moving['w']: dx += fx*sp; dy += fy*sp
    if moving['s']: dx -= fx*sp; dy -= fy*sp
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


def main():
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

    # start at title menu
    pause_game('title')

    glutMainLoop()

# --------------------------- Helpers for Tests ----------------
# F1: Level 1 — easy/tutorial, harmless-ish enemies
# F2: Level 2 — more enemies, keys hidden
# F3: Level 3 — fast enemies + boss

if __name__ == "__main__":
    main()
