#Necessary imports for the game to run

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL import GLUT as GLUTmod
import math, random, time

#Variables for window and camera
window_width, window_height = 1000, 800
aspect_ratio = window_width/ window_height
fovY_default = 77.3
fovY_scoped  = 40.0
yaw_step_values = [0.8, 0.25]
yaw_step = yaw_step_values[0]

#Camera modes
cam_first  = 0
cam_third  = 1
cam_topdown = 2 
camera_mode = cam_third

#Current FOV; updated when scoping
fovY = fovY_default

#Third-person camera parameters
third_cam_back = 120.0
third_cam_side = 30.0
third_cam_height = 120.0
camera_smooth = 0.15
cam_eye = None
cam_cen = None

#Variables for the checkpoint tile functionality
checkpoint_tiles = []
GRID_Z = 10

#Variables for the exit tile functionality
exit_tiles = []

lava_tiles = []
lava_msg = ""
lava_msg_timer = 0

golden_tiles = []
golden_tile_msg = ""
golden_tile_msg_timer = 0

#Messages for level 1 tutorials
level1_start_msg = ""
level1_msg_active = False

level1_checkpoint_msg = ""
level1_checkpoint_msg_active = False

level1_enemy_stat = 0

level1_all_enemies_msg = ""
level1_all_enemies_msg_active = False
level1_enemies_spawned = False  # Track if the 5 enemies have been spawned

trap_triggered = False
trap_spawn_locations = [(-1200, 400), (-800, 800), (-400, 1200), (0, 800), (400, 400)]

#Utility functions

#To keep stats within valid range
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

#Preset of colors to use later
preset_colors = {
    'hero_blue': (0.01, 0.31, 0.76),
    'hero_red': (1.00, 0.15, 0.15),
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
    'chest_dark': (0.0588, 0.0549, 0.0549),
    'chest_maroon': (0.3294, 0.0706, 0.0706),
    'bright_green': (0.2, 0.8, 0.2),
    'hulk_green': (0.04, 0.34, 0.03),
    'hulk_purple': (0.25, 0.03, 0.34)
}

#Get color, if not found, return white as default
def get_color(name):
    return preset_colors.get(name, (1.0, 1.0, 1.0))

#Draw text on the screen
def draw_text(x, y, text, color = (1, 1, 1), font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top

    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

#Core functions

class Entity:
    def __init__(self, x, y, z, rx=0, ry=0, rz=0, width=1, depth=1, height=1):
        self.x, self.y, self.z = x, y, z
        self.rx, self.ry, self.rz = rx, ry, rz
        self.width, self.depth, self.height = width, depth, height
        self.sync_bounding_box()

    def sync_bounding_box(self):
        # Treat (x,y,z) as center of the volume for AABB
        self.x_min = self.x - self.width/2;  self.x_max = self.x + self.width/2
        self.y_min = self.y - self.depth/2;  self.y_max = self.y + self.depth/2
        self.z_min = self.z - self.height/2; self.z_max = self.z + self.height/2

    def draw(self):
        #To be drawn by the child classes
        pass

    def check_collision(self, other):
        #Checks collision for all the boundaries
        return not (
            self.x_max < other.x_min or 
            self.x_min > other.x_max or
            self.y_max < other.y_min or 
            self.y_min > other.y_max or
            self.z_max < other.z_min or 
            self.z_min > other.z_max
        )

    # Rotations around pivot points in the respective planes
    def rotate_x(self, rx, ay, az):
        self.rx += rx
        rad = math.radians(rx)
        dy = self.y - ay
        dz = self.z - az
        self.y = ay + dy * math.cos(rad) - dz * math.sin(rad)
        self.z = az + dy * math.sin(rad) + dz * math.cos(rad)

    def rotate_y(self, ry, ax, az):
        self.ry += ry
        rad = math.radians(ry)
        dx = self.x - ax
        dz = self.z - az
        self.x = ax + dx * math.cos(rad) + dz * math.sin(rad)
        self.z = az - dx * math.sin(rad) + dz * math.cos(rad)

    def rotate_z(self, rz, ax, ay):
        self.rz += rz
        rad = math.radians(rz)
        dx = self.x - ax
        dy = self.y - ay
        self.x = ax + dx * math.cos(rad) - dy * math.sin(rad)
        self.y = ay + dx * math.sin(rad) + dy * math.cos(rad)

#Class for the implementation of checkpoint tiles.
class CheckpointTile(Entity):
    def __init__(self, x, y, z=GRID_Z):
        super().__init__(x, y, z, width=100, depth=100, height=0)
        self.active = True
        self.saved = False

    def draw(self):
        pass

#To place the checkpoint tiles on individual levels
def place_checkpoint_tile(x, y):
    checkpoint_tiles.append(CheckpointTile(x, y))

# Class for the implementation of level exit tiles.
class LevelExitTile(Entity):
    def __init__(self, x, y, z=GRID_Z):
        super().__init__(x, y, z, width=100, depth=100, height=8)
        self.active = True

    def draw(self):
        pass

# To place the exit tiles on individual levels
def place_exit_tile(x, y):
    global exit_tiles
    exit_tiles.append(LevelExitTile(x, y))

class LavaTile(Entity):
    def __init__(self, x, y, z=GRID_Z):
        super().__init__(x, y, z, width=100, depth=100, height=0)
        self.active = True

    def draw(self):
        pass

def place_lava_tile(x, y):
    lava_tiles.append(LavaTile(x, y))

class GoldenTile(Entity):
    def __init__(self, x, y, z=GRID_Z, message=""):
        super().__init__(x, y, z, width=200, depth=200, height=0)
        self.active = True
        self.message = message
        self.triggered = False

    def draw(self):
        pass

def place_golden_tile(x, y, message):
    golden_tiles.append(GoldenTile(x, y, GRID_Z, message))

class Shape3D(Entity):
    quadric = gluNewQuadric()

    def __init__(self, color, x, y, z, rx, ry, rz, *dims):
        self.color = get_color(color)
        super().__init__(x, y, z, rx, ry, rz, *dims)

class Sphere(Shape3D):
    def __init__(self, color, x, y, z, rx, ry, rz, *dims):
        #If only a single radius was passed, expand to (r, r, r)
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
        #Use the three stored dimensions; for heads these are equal so it's round
        glScalef(self.width, self.depth, self.height)
        #Higher tessellation for a smoother, circular look
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
        for entity in self.entities: entity.draw()

    def rotate_x(self, rx):
        self.rx += rx
        for entity in self.entities: entity.rotate_x(rx, self.y, self.z)

    def rotate_y(self, ry):
        self.ry += ry
        for entity in self.entities: entity.rotate_y(ry, self.x, self.z)

    def rotate_z(self, rz):
        self.rz += rz
        for entity in self.entities: entity.rotate_z(rz, self.x, self.y)

#Game models

class Chest(CompoundEntity):
    def __init__(self, x, y, ground_z, rx=0, ry=0, rz=0, w=60, d=40, h=40):
        base_h = 0.6*h
        base_z = ground_z + base_h/2
        base = Box('chest_dark', x, y, base_z, rx, ry, rz, w, d, base_h)
        ins_z = ground_z + base_h
        ins_1 = Box('chest_dark', x, y, ins_z-10, rx, ry, rz, w-10, d-10, 0)
        ins_2 = Box('chest_maroon', x, y, ins_z+10, rx, ry, rz, w-10, d-10, 0)
        lid_h = h - base_h
        lid_z = ground_z + base_h + lid_h/2
        lid = Box('chest_maroon', x, y, lid_z, rx, ry, rz, w, d, lid_h)
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
        ins_2.color = get_color('chest_dark')
        self.closed = False
        
    def close(self):
        ins_1 = self.entities[1]
        lid = self.entities[2]
        ins_2 = self.entities[3]
        lid.rotate_x(135, lid.y_max, lid.z_min)
        ins_2.rotate_x(135, lid.y_max, lid.z_min)
        ins_1.color = get_color('chest_dark')
        ins_2.color = get_color('chest_maroon')
        self.closed = True
        
    def toggle(self):
        if self.closed: self.open()
        else: self.close()

player_style = "Regular"
class StickPlayer(CompoundEntity):
    def __init__(self, x, y, ground_z, rz):
        self.styles = ['Regular',  'Hero', 'Hulk']
        self.style = 0
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
        leg_left = Cylinder('grey', x, y - 7, hip_z, 0, 0, 0, radius=self.leg_r, height=self.leg_h, anchor='top')
        leg_right = Cylinder('grey', x, y + 7, hip_z, 0, 0, 0, radius=self.leg_r, height=self.leg_h, anchor='top')
        # Body rises upward from hip level
        body = Cylinder('orange', x, y, hip_z, 0, 0, 0, radius=self.body_r, height=self.body_h, anchor='base')
        # Arms hang down from the shoulder line
        arm_left = Cylinder('light_blue', x, y - self.shoulder_span/2, shoulder_z, 0, 0, 0, radius=self.arm_r, height=self.arm_h, anchor='top')
        arm_right = Cylinder('light_blue', x, y + self.shoulder_span/2, shoulder_z, 0, 0, 0, radius=self.arm_r, height=self.arm_h, anchor='top')
        head = Sphere('black', x, y, head_center_z, 0, 0, 0, self.head_r)
        super().__init__(leg_left, leg_right, arm_left, body, arm_right, head)

        self.on_ground_z = ground_z
        self.anim = 0.0
        self.anim_dir = 0.015
        self.speed = 1.2
        self.jump_v = 0.0
        self.health = 100
        self.damage = 10
        self.inventory = {'handgun_ammo':24, 'rifle_ammo': 30, 'keys':1,'Nourishment':0,'Aegis':0,'Shard':0,'portalgun':0}
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
            e.x += dx; e.y += dy; e.sync_bounding_box()
        self.sync_bounding_box()

    def stand_center_z(self):
        return self.on_ground_z + 0.5*self.leg_h

    def jump(self):
        if abs(self.z - self.stand_center_z()) < 0.2:
            self.jump_v = 6.5

    def physics(self):
        if self.jump_v != 0:
            self.z += self.jump_v
            for e in self.entities:
                e.z += self.jump_v; e.sync_bounding_box()
            self.jump_v -= 0.35
            if self.z <= self.stand_center_z():
                dz = self.stand_center_z() - self.z
                self.z += dz
                for e in self.entities:
                    e.z += dz; e.sync_bounding_box()
                self.jump_v = 0.0
        self.sync_bounding_box()

    def draw(self):
        hip_z = self.on_ground_z + self.leg_h
        shoulder_z = hip_z + self.body_h
        head_center_z = shoulder_z + self.head_r + 4.0

        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glRotatef(self.yaw, 0, 0, 1)

        # Legs
        glColor3f(*get_color('grey'))
        glPushMatrix()
        glTranslatef(-7, 0, hip_z - self.leg_h)
        # gluCylinder(Sphere.quadric, self.leg_r, self.leg_r, self.leg_h, 16, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef( 7, 0, hip_z - self.leg_h)
        # gluCylinder(Sphere.quadric, self.leg_r, self.leg_r, self.leg_h, 16, 1)
        glPopMatrix()

        # Body
        glColor3f(*get_color('orange'))
        glPushMatrix()
        glTranslatef(0, 0, hip_z)
        # gluCylinder(Sphere.quadric, self.body_r, self.body_r, self.body_h, 16, 1)
        glPopMatrix()

        # Arms and simple stick weapon on right hand
        # glColor3f(*get_color('light_blue'))
        glPushMatrix()
        glTranslatef(-self.shoulder_span/2, 0, shoulder_z - self.arm_h)
        # gluCylinder(Sphere.quadric, self.arm_r, self.arm_r, self.arm_h, 16, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef( self.shoulder_span/2, 0, shoulder_z - self.arm_h)
        #gluCylinder(Sphere.quadric, self.arm_r, self.arm_r, self.arm_h, 16, 1)
        
        # weapon
        if selected_slot == 2: 
            glPushMatrix()
            glTranslatef(0, 0, self.arm_h - 2)
            glRotatef(90, 0, 1, 0)
            glColor3f(0.05, 0.05, 0.05) 
            gluCylinder(Sphere.quadric, 4, 4, 60, 16, 1) 
            glPopMatrix()
        else:
            glPushMatrix()
            glTranslatef(0, 0, self.arm_h - 2)
            glRotatef(90, 0, 1, 0)
            glColor3f(0.3, 0.3, 0.3)
            gluCylinder(Sphere.quadric, 3, 3, 30, 12, 1)
            glPopMatrix()
        glPopMatrix()

        # Head
        if self.head_visible:
            glColor3f(*get_color('light_brown'))
            glPushMatrix()
            glTranslatef(0, 0, head_center_z)
            # gluSphere(Sphere.quadric, self.head_r, 10, 10)
            glPopMatrix()
        glPopMatrix()
        for i, e in enumerate(self.entities):
            if i==5 and not self.head_visible: continue
            e.draw()
    def change_style(self):
        global player_style
        self.style += 1
        self.style %= len(self.styles)
        style = self.styles[self.style]
        body = self.entities[-3]
        leg1 = self.entities[0]
        leg2 = self.entities[1]
        arm1 = self.entities[2]
        arm2 = self.entities[4]

        if style == 'Regular':
            body.radius = 20
            body.color = get_color('orange')
            leg1.color = get_color('grey')
            leg2.color = get_color('grey')
            arm1.color = get_color('light_blue')
            arm2.color = get_color('light_blue')
        elif style == 'Hero':
            body.radius = 10
            body.color = get_color('hero_red')
            leg1.color = get_color('hero_blue')
            leg2.color = get_color('hero_blue')
            arm1.color = get_color('light_blue')
            arm2.color = get_color('light_blue')
        elif style == 'Hulk':
            body.radius = 10
            body.color = get_color('hulk_green')
            leg1.color = get_color('hulk_purple')
            leg2.color = get_color('hulk_purple')
            arm1.color = get_color('hulk_green')
            arm2.color = get_color('hulk_green')
        player_style = style

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
            e.width *= s; e.depth *= s; e.height *= s; e.sync_bounding_box()
            e.width /= s; e.depth /= s; e.height /= s

        # chase (speed is 0 for now per user setting)
        dx = target.x - self.x
        dy = target.y - self.y
        d = math.hypot(dx, dy) + 1e-6
        vx = self.speed * (dx / d)
        vy = self.speed * (dy / d)
        self.x += vx; self.y += vy
        for e in self.entities:
            e.x += vx; e.y += vy; e.sync_bounding_box()
        self.sync_bounding_box()

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
    def move(self, dx, dy):
        self.x += dx; self.y += dy
        for e in self.entities:
            e.x += dx; e.y += dy; e.sync_bounding_box()
        self.sync_bounding_box()
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
    2: 'rifle',
    3: 'portalgun', 
    4: 'Nourishment',
    5: 'Aegis',
    6: 'Shard'
}

selected_slot = 1

# bullets
bullets = []

# portals
blue_portal = Portal('cyan')
red_portal  = Portal('red')

# scope
scoped = False
pre_scope_camera_mode = cam_third

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
    gluPerspective(fovY, aspect_ratio, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)

    if camera_mode == cam_third:
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
    elif camera_mode == cam_first:
        # first person from head (no smoothing for responsiveness)
        head = player.head_entity()
        ex,ey,ez = head.x, head.y, head.z
        dx = math.cos(math.radians(player.yaw))
        dy = math.sin(math.radians(player.yaw))
        cam_eye = None; cam_cen = None  # reset smoothing when switching back later
        gluLookAt(ex,ey,ez, ex+dx*50, ey+dy*50, ez, 0,0,1)
    elif camera_mode == cam_topdown:
        gluLookAt(0, 0, 2500, 0, 0, 0, 1, 0, 0)

# --------------------------- Level Setup ----------------------

def clear_level():
    enemies.clear(); chests.clear(); key_positions.clear(); pickups.clear(); walls.clear()
    bullets.clear(); blue_portal.active=False; red_portal.active=False
    checkpoints.clear()
    globals()['world_bounds'] = None
    checkpoint_tiles.clear()
    exit_tiles.clear()
    lava_tiles.clear()
    golden_tiles.clear()

def setup_level(level):
    global current_level, last_checkpoint, start_time, boss_spawned, boss_seen_alive, win_check_cooldown, level1_start_msg, level1_msg_active
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
    # keys scattered
    # Level 2: a few random keys around the origin
    if level == 2:
        for _ in range(3):
            key_positions.append((random.randint(-300,300), random.randint(-300,300)))
    # chests
    if level > 1:
        for i in range(2 if level==1 else 3):
            cx = random.randint(-250,250); cy = random.randint(-250,250)
            c = Chest(cx, cy, GRID_Z)
            c.contains = random.choice(['ammo', 'rifle_ammo', 'Nourishment','Aegis','Shard','portalgun'])
            chests.append(c)
    # enemies
    if level==1:
        field_size = 1600
        build_level3_bounds(field_size, 2000)
        place_player(-field_size + 130, 100)
        place_checkpoint_tile(-1500, -100)
        level1_start_msg = "Walk over the green tile to set your checkpoint"
        level1_msg_active = True
        place_lava_tile(-1300, 100)
        place_lava_tile(-1300, 300)
        place_lava_tile(-1300, 500)
        place_lava_tile(-1300, 700)
        place_lava_tile(-1300, 900)
        place_lava_tile(-1300, 1100)
        place_lava_tile(-1300, 1300)
        place_lava_tile(-1300, -100)
        place_lava_tile(-1300, -300)
        place_lava_tile(-1300, -500)
        place_lava_tile(-1300, -700)
        place_lava_tile(-1300, -900)
        place_lava_tile(-1300, -1100)
        place_lava_tile(-1300, -1300)
        place_golden_tile(-1500, -1500, "You found a secret!")
        place_golden_tile(-1100, -1500, "You found a secret!")
        place_lava_tile(-900, -1500)
        place_lava_tile(-900, -1300)
        place_lava_tile(-900, -1100)
        place_lava_tile(-900, -900)
        place_lava_tile(-900, -700)
        place_lava_tile(-900, -500)
        place_lava_tile(-900, -300)
        place_lava_tile(-900, -100)
        place_lava_tile(-900, 100)
        place_lava_tile(-1100, 100)
        place_golden_tile(-1100, -100, 'You found a secret!')
        place_lava_tile(100, 100)
        place_lava_tile(100, 300)
        place_lava_tile(100, 500)
        place_lava_tile(100, 700)
        place_lava_tile(100, 900)
        place_lava_tile(100, 1100)
        place_lava_tile(100, 1300)
        place_lava_tile(100, 1500)
        place_lava_tile(100, -100)
        place_lava_tile(100, -300)
        place_lava_tile(100, -500)
        place_lava_tile(100, -700)
        place_lava_tile(100, -900)
        place_lava_tile(100, -1100)
        place_lava_tile(100, -1300)

        place_golden_tile(-500, 0, "Uh oh!!! A trap")

        # positions = [(-1200, 400), (-800, 800), (-400, 1200), (0, 800), (400, 400)]
        # for pos in positions:
        #     turret = Enemy(pos[0], pos[1], GRID_Z, True)
        #     turret.hp = 40         # Weaker health
        #     turret.speed = 0       # Stationary turret
        #     turret.shoot_cool = 500  # Shoots more slowly
        #     # Optionally, scale down the boss size
        #     for e in turret.entities:
        #         if hasattr(e, 'height'):
        #             e.height *= 0.6
        #         if hasattr(e, 'radius'):
        #             e.radius *= 0.6
        #     enemies.append(turret)
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
        # Ensure equal number of keys as chests within the field
        pad = 80
        for _ in range(len(chests)):
            kx = random.randint(-field_size+pad, field_size-pad)
            ky = random.randint(-field_size+pad, field_size-pad)
            key_positions.append((kx, ky))
    # timer/score
    start_time = time.time()

def build_level3_bounds(field_size, wall_height = 800):
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
    elif name == 'rifle_ammo':
        player.inventory['rifle_ammo'] += 6 
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
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    slot_w = 85; slot_h = 50; x0 = 20; y0 = 20
    for i in range(1,10):
        x = x0 + (i-1)*(slot_w+1)
        y = y0
        if i==selected_slot:
            glColor3f(1,1,1)
        else:
            glColor3f(0.5,0.5,0.5)
        glBegin(GL_QUADS)
        glVertex2f(x,y); glVertex2f(x+slot_w,y); glVertex2f(x+slot_w,y+slot_h); glVertex2f(x,y+slot_h)
        glEnd()
        glColor3f(0,0,0)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(x, y);         glVertex2f(x+slot_w, y)         # Top
        glVertex2f(x+slot_w, y);  glVertex2f(x+slot_w, y+slot_h)  # Right
        glVertex2f(x+slot_w, y+slot_h); glVertex2f(x, y+slot_h)   # Bottom
        glVertex2f(x, y+slot_h);  glVertex2f(x, y)                # Left
        glEnd()
        draw_text(x+6, y+slot_h-18, str(i), (0, 0, 0))
        # item label
        name = inventory_slots.get(i,'')
        if name:
            draw_text(x+20, y+20, name[:6], (0, 0, 0))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_crosshair(scoped_mode):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    cx, cy = window_width/2, window_height/2 - 21
    glColor3f(1,1,1)
    glBegin(GL_LINES)
    if scoped_mode:
        # screen-wide cross shaped crosshair
        glVertex2f(cx-200, cy); glVertex2f(cx+200, cy)
        glVertex2f(cx, cy-200); glVertex2f(cx, cy+200)
    glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_radar():
    # very simple 2D circle + dots around player showing nearby objects
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    cx, cy, R = window_width-110, 110, 90
    # circle approx
    glColor3f(1,1,1)
    glBegin(GL_LINE_LOOP)
    for i in range(40):
        a = 2*math.pi*i/40
        glVertex2f(cx + R*math.cos(a), cy + R*math.sin(a))
    glEnd()
    # player icon at center (small upward-pointing triangle)
    glColor3f(1,1,1)
    glBegin(GL_TRIANGLES)
    glVertex2f(cx,     cy+8)
    glVertex2f(cx-6,   cy-4)
    glVertex2f(cx+6,   cy-4)
    glEnd()
    # plot enemies/keys/chests within 400 units
    def to_local(px,py):
        dx = px - player.x; dy = py - player.y
        d = math.hypot(dx,dy)
        if d>400: return None
        scale = R/400.0
        # rotate by (90 - yaw) so player's forward faces up (north)
        yaw_rad = math.radians(90 - player.yaw)
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
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor3f(1,1,1)
    x, y = 10, window_height - 24
    text = f"HP: {int(player.health)}  Ammo: {player.inventory['handgun_ammo']}  Rifle Ammo: {player.inventory['rifle_ammo']}  Keys: {player.inventory['keys']}  Level: {current_level}  Score: {int(score)}  Best: {int(best_score)}  Loads:{load_uses_left}"
    glRasterPos2f(x, y)
    font = globals().get('GLUT_BITMAP_HELVETICA_18', None)
    if font is not None:
        for ch in text:
            glutBitmapCharacter(font, ord(ch))

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    # Draw lava message in top-right corner if active
    if globals().get('lava_msg_timer', 0) > 0 and globals().get('lava_msg', ""):
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        draw_text(window_width - 320, window_height - 60, lava_msg, (1, 0.3, 0))
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    if globals().get('checkpoint_msg', 0) > 0:
        draw_text(window_width//2 - 80, window_height//2 + 80, "Checkpoint Saved!")
        globals()['checkpoint_msg'] -= 1
    if golden_tile_msg_timer > 0 and golden_tile_msg:
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glColor3f(0,0,0)
        glBegin(GL_QUADS)
        glVertex2f(window_width//2-200, window_height//2+120)
        glVertex2f(window_width//2+200, window_height//2+120)
        glVertex2f(window_width//2+200, window_height//2+170)
        glVertex2f(window_width//2-200, window_height//2+170)
        glEnd()
        draw_text(window_width//2 - 180, window_height//2 + 140, golden_tile_msg)
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)


# --------------------------- Drawing --------------------------

def draw_floor():
    global current_level
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

    for ct in checkpoint_tiles:
        glColor3f(*get_color('bright_green'))
        glBegin(GL_QUADS)
        glVertex3f(ct.x-100, ct.y-100, GRID_Z+0.2)
        glVertex3f(ct.x+100, ct.y-100, GRID_Z+0.2)
        glVertex3f(ct.x+100, ct.y+100, GRID_Z+0.2)
        glVertex3f(ct.x-100, ct.y+100, GRID_Z+0.2)
        glEnd()
    for et in exit_tiles:
        glColor3f(*get_color('black'))
        glBegin(GL_QUADS)
        glVertex3f(et.x-100, et.y-100, GRID_Z+0.2)
        glVertex3f(et.x+100, et.y-100, GRID_Z+0.2)
        glVertex3f(et.x+100, et.y+100, GRID_Z+0.2)
        glVertex3f(et.x-100, et.y+100, GRID_Z+0.2)
        glEnd()
    for lt in lava_tiles:
        glColor3f(1.0, 0.3, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(lt.x-100, lt.y-100, GRID_Z+0.2)
        glVertex3f(lt.x+100, lt.y-100, GRID_Z+0.2)
        glVertex3f(lt.x+100, lt.y+100, GRID_Z+0.2)
        glVertex3f(lt.x-100, lt.y+100, GRID_Z+0.2)
        glEnd()
    for gt in golden_tiles:
        glColor3f(*get_color('gold'))
        glBegin(GL_QUADS)
        glVertex3f(gt.x-100, gt.y-100, GRID_Z+0.2)
        glVertex3f(gt.x+100, gt.y-100, GRID_Z+0.2)
        glVertex3f(gt.x+100, gt.y+100, GRID_Z+0.2)
        glVertex3f(gt.x-100, gt.y+100, GRID_Z+0.2)
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
    player.ensure_head_visibility(camera_mode==cam_third)
    player.draw()

    # HUD
    draw_inventory_bar()
    draw_radar()
    draw_hud_stats()
    if scoped:
        draw_crosshair(True)
    else:
        draw_crosshair(False)
    
    if level1_msg_active and level1_start_msg:
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glColor3f(0,0,0)
        glBegin(GL_QUADS)
        glVertex2f(window_width//2-240, window_height//2+60)
        glVertex2f(window_width//2+240, window_height//2+60)
        glVertex2f(window_width//2+240, window_height//2+120)
        glVertex2f(window_width//2-240, window_height//2+120)
        glEnd()
        draw_text(window_width//2-200, window_height//2+80, level1_start_msg, (1,1,1))
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
        
    
    if level1_checkpoint_msg_active and level1_checkpoint_msg:
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glColor3f(0,0,0)
        glBegin(GL_QUADS)
        glVertex2f(window_width//2-240, window_height//2+10)
        glVertex2f(window_width//2+240, window_height//2+10)
        glVertex2f(window_width//2+240, window_height//2+70)
        glVertex2f(window_width//2-240, window_height//2+70)
        glEnd()
        draw_text(window_width//2-200, window_height//2+30, level1_checkpoint_msg, (1,1,1))
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
        
    if level1_all_enemies_msg_active and level1_all_enemies_msg:
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glColor3f(0,0,0)
        glBegin(GL_QUADS)
        glVertex2f(window_width//2-240, window_height//2-60)
        glVertex2f(window_width//2+240, window_height//2-60)
        glVertex2f(window_width//2+240, window_height//2)
        glVertex2f(window_width//2-240, window_height//2)
        glEnd()
        draw_text(window_width//2-200, window_height//2-40, level1_all_enemies_msg, (1,1,1))
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    # Menus
    if paused:
        draw_menu()
    for ct in checkpoint_tiles:
        ct.draw()
    for et in exit_tiles:
        et.draw()
    for lt in lava_tiles:
        lt.draw()
    
    glutSwapBuffers()

# --------------------------- Menus ----------------------------

def draw_menu():
    # menu_mode: 'title', 'paused', 'win', 'lose', customization
    if menu_mode == 'win':
        title = 'You Win'
    elif menu_mode == 'lose':
        title = 'You Lost'
    elif menu_mode == 'paused':
        title = 'Paused'
    elif menu_mode == 'customization':
        title = 'Player Customization'
    else:
        title = 'Demons & Portals'
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    # dark overlay
    glColor3f(0,0,0)
    glBegin(GL_QUADS)
    glVertex2f(0,0); glVertex2f(window_width,0); glVertex2f(window_width,window_height); glVertex2f(0,window_height)
    glEnd()
    draw_text(window_width/2-120, window_height-120, title)
    if menu_mode=='title':
        draw_text(window_width/2-200, window_height-170, 'Press N for New Game | F1/F2/F3 for Level Tests')
    elif menu_mode=='paused':
        draw_text(window_width/2-250, window_height-170, 'ESC Resume | L Load Checkpoint | R Restart Level')
    elif menu_mode in ('win','lose'):
        draw_text(window_width/2-140, window_height-170, f'Total Score: {int(score)}')
    elif menu_mode == 'customization':
        global player_style
        draw_text(window_width/2-200, window_height-170, f'Press F5 to toggle player style. Current style: {player_style} ')
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# --------------------------- Update ---------------------------

def animate():
    global score, best_score, paused, win_check_cooldown, level1_checkpoint_msg, level1_checkpoint_msg_active, level1_enemy_stat, level1_enemies_spawned, level1_all_enemies_msg, level1_all_enemies_msg_active, lava_msg, lava_msg_timer, golden_tile_msg, golden_tile_msg_timer, trap_triggered
    if not paused:
        # movement animation and physics
        player.physics()

        on_lava = False
        for lt in lava_tiles:
            if lt.active and math.hypot(player.x - lt.x, player.y - lt.y) < 100:
                player.health -= 0.005  # damage per frame on lava
                on_lava = True
                break
        if on_lava:
            lava_msg = "Ouch!!! Lava hurts!!!"
            lava_msg_timer = 60  # show for 60 frames (~1 second)
        elif lava_msg_timer > 0:
            lava_msg_timer -= 1
            if lava_msg_timer == 0:
                lava_msg = ""
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
        for gt in golden_tiles:
            if gt.active and not gt.triggered and math.hypot(player.x - gt.x, player.y - gt.y) < 100:
                golden_tile_msg = gt.message
                golden_tile_msg_timer = 120  # show for 2 seconds
                gt.triggered = True
                # Trap logic: spawn enemies if this is the trap tile
                if gt.message == "Uh oh!!! A trap" and not trap_triggered:
                    trap_triggered = True
                    for pos in trap_spawn_locations:
                        enemies.append(Enemy(pos[0], pos[1], GRID_Z, False))

        for ct in checkpoint_tiles:
            if ct.active and math.hypot(player.x - ct.x, player.y - ct.y) < 100:
                set_checkpoint((ct.x, ct.y))
                ct.saved = True
                # Show message (simple: set a global for a few frames)
                globals()['checkpoint_msg'] = 60  # show for 60 frames
                
                if current_level == 1:
                    level1_checkpoint_msg = "Excellent!!! Now kill the enemies!!!"
                    level1_checkpoint_msg_active = True
                    
                    if level1_enemy_stat == 0:
                        for i in range(5):
                                angle = i * (2 * math.pi / 5)
                                ex = player.x + math.cos(angle) * 300
                                ey = player.y + math.sin(angle) * 300
                                enemies.append(Enemy(ex, ey, GRID_Z, False))
                        level1_enemy_stat = 1
                        level1_enemies_spawned = True
        
        for et in exit_tiles:
            if et.active and math.hypot(player.x - et.x, player.y - et.y) < 60:
                # Advance to next level
                setup_level(current_level + 1)
                exit_tiles.clear()  # Remove exit tiles for next level
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
            for e in [player] + enemies:
                if math.hypot(e.x-blue_portal.x, e.y-blue_portal.y) < 25:
                    e.move(red_portal.x - e.x, red_portal.y - e.y)
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
        if current_level == 1 and level1_enemies_spawned:
            # Only show message if all spawned enemies are dead and message not yet shown
            if level1_all_enemies_msg_active is False and level1_enemies_spawned and all(not e.is_boss for e in enemies) and len(enemies) == 0:
                level1_all_enemies_msg = "Great job!!! Move to the next golden tile!"
                level1_all_enemies_msg_active = True
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
    global paused, menu_mode, camera_mode, scoped, fovY, selected_slot, pre_topdown_camera_mode
    k = key
    if k==b'\x1b':  # ESC
        if paused:
            paused=False; menu_mode=None
        else:
            pause_game('paused')
        return
    if k==b'o':
        if paused:
            paused=False; menu_mode=None
        else:
            pause_game('paused')
            menu_mode='customization'
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
                nearest.toggle()
    # inventory hotkeys 1..9
    if k in [bytes(str(i),'ascii') for i in range(1,10)]:
        selected_slot = int(k.decode())
    if k in (b't', b'T'):
        if camera_mode != cam_topdown:
            pre_topdown_camera_mode = camera_mode
            set_camera_mode(cam_topdown)
        else:
            set_camera_mode(pre_topdown_camera_mode)
            
    if k in (b'c', b'C'):
        load_checkpoint()


def key_up(key, x, y):
    if key in (b'w',b'a',b's',b'd'):
        moving[key.decode()] = False


def special_keys(key, x, y):
    # arrow keys adjust third-person camera in the X/Y plane (Z locked)
    global third_cam_back, third_cam_side, player, menu_mode
    if camera_mode == cam_third:
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

    # style change
    if menu_mode == 'customization' and key == GLUT_KEY_F5: player.change_style()

def clicks(button, state, x, y):
    global scoped, pre_scope_camera_mode, fovY, yaw_step, yaw_step_values
    if state != GLUT_DOWN and button != GLUT_RIGHT_BUTTON: return
    # map window x,y not used — just actions
    if button == GLUT_LEFT_BUTTON:
        # left click: shoot / place portal / use consumable depending on slot
        do_primary_action()
    if button == GLUT_RIGHT_BUTTON:
        # right click: scope
        if state == GLUT_DOWN:
            scoped = True
            pre_scope_camera_mode = camera_mode
            set_camera_mode(cam_first)
            set_fov(True)
            yaw_step = yaw_step_values[1]
        else:
            scoped = False
            set_fov(False)
            set_camera_mode(pre_scope_camera_mode)
            yaw_step = yaw_step_values[0]

    # wheel
    if button == 3:  # wheel up
        change_slot(-1)
    if button == 4:  # wheel down
        change_slot(1)

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
    if mode == cam_first:
        player.ensure_head_visibility(False)
    else:
        player.ensure_head_visibility(True)


def toggle_perspective():
    if scoped:
        return  # scoped locks to first person
    set_camera_mode(cam_first if camera_mode==cam_third else cam_third)


def change_slot(delta):
    global selected_slot
    selected_slot = ((selected_slot-1 + delta) % 9) + 1


def do_primary_action():
    # 1 = handgun, 2 = portalgun, 3.. consumables
    item = inventory_slots.get(selected_slot, '')
    if item=='handgun':
        shoot_handgun()
    elif item=='rifle':
        shoot_rifle()
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

def shoot_rifle():
    if player.inventory['rifle_ammo'] <= 0:
        return
    player.inventory['rifle_ammo'] -= 1
    head = player.head_entity()
    ang = math.radians(player.yaw)
    vx = math.cos(ang) * 28  # Faster bullet
    vy = math.sin(ang) * 28
    dmg = player.damage + 15  # More damage than handgun
    max_dist = 1600
    bullets.append(Bullet(head.x + math.cos(ang) * 55, head.y + math.sin(ang) * 55, head.z - 15, vx, vy, dmg, max_dist))

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
    global level1_msg_active, level1_checkpoint_msg_active, level1_all_enemies_msg_active, yaw_step
    
    
    # WASD planar move
    dx=0; dy=0
    sp = player.speed
    # yaw update from A/D keys (rotate while held)
    
    # Swap A/D rotation directions
    if moving['a']:
        player.yaw = (player.yaw + yaw_step) % 360
        player.rotate_z(yaw_step)
    if moving['d']:
        player.yaw = (player.yaw - yaw_step) % 360
        player.rotate_z(-yaw_step)
    # convert WASD relative to yaw
    dir_forward = math.radians(player.yaw)
    fx, fy = math.cos(dir_forward), math.sin(dir_forward)
    if moving['w']: dx += fx*sp; dy += fy*sp
    if moving['s']: dx -= fx*sp; dy -= fy*sp
    if dx or dy:
        if current_level == 1 and level1_msg_active:
            level1_msg_active = False
            
        if current_level == 1 and level1_checkpoint_msg_active:
            level1_checkpoint_msg_active = False
            
        if current_level == 1 and level1_all_enemies_msg_active:
            level1_all_enemies_msg_active = False
        # apply movement, but clamp within world bounds if defined
        new_x = player.x + dx
        new_y = player.y + dy
        player.walk_anim_tick()
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
    global aspect_ratio
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # NO DEPTH
    glutInitWindowSize(window_width, window_height)
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
    gluPerspective(fovY, aspect_ratio, 0.1, 5000)

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
