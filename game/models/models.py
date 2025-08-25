from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

# ================================= Colors =====================================

COLORS = {
    "dark_grey": (0.1, 0.1, 0.1),
    'brown': (0.396, 0.067, 0),
    'dark_brown': (0.251, 0.059, 0.024),
    'gold': (0.996, 0.839, 0),
    'red': (1, 0, 0),
    'toothpaste': (0.788, 0.933, 0.973),
    'dark_blue': (0.149, 0.278, 0.51)
}

def get_color(name):
    return COLORS[name]

# ==============================================================================

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
        self.x = x
        self.y = y
        self.z = z
        self.rx = rx
        self.ry = ry
        self.rz = rz


        # Bounding box
        self.x_min = x - self.width/2
        self.y_min = y - self.depth/2
        self.z_min = z - self.height/2
        self.x_max = self.x_min + self.width
        self.y_max = self.y_min + self.depth
        self.z_max = self.z_min + self.height
        

    def check_collision(self, other):
        return (self.x_min <= other.x_max and self.x_max >= other.x_min and
                self.y_min <= other.y_max and self.y_max >= other.y_min and
                self.z_min <= other.z_max and self.z_max >= other.z_min)

    def rotate_x(self, rx, ay=0, az=0):
        self.rx += rx
        dy = self.y - ay
        dz = self.z - az
        rad = math.radians(rx)
        self.y = ay + dy * math.cos(rad) - dz * math.sin(rad)
        self.z = az + dy * math.sin(rad) + dz * math.cos(rad)

    def rotate_y(self, ry, ax=0, az=0):
        self.ry += ry
        dx = self.x - ax
        dz = self.z - az
        rad = math.radians(ry)
        self.x = ax + dx * math.cos(rad) + dz * math.sin(rad)
        self.z = az - dx * math.sin(rad) + dz * math.cos(rad)

    def rotate_z(self, rz, ax=0, ay=0):
        self.rz += rz
        dx = self.x - ax
        dy = self.y - ay
        rad = math.radians(rz)
        self.x = ax + dx * math.cos(rad) - dy * math.sin(rad)
        self.y = ay + dx * math.sin(rad) + dy * math.cos(rad)


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
            gluSphere(self.quadric, 1, 10, 25)
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

class CompoundEntity(Entity):
    def __init__(self, *entities):
        # Center
        x = sum(e.x for e in entities)/len(entities)
        y = sum(e.y for e in entities)/len(entities)
        z = sum(e.z for e in entities)/len(entities)
            
        # Bounding Box
        x_min = min(e.x_min for e in entities)
        y_min = min(e.y_min for e in entities)
        z_min = min(e.z_min for e in entities)
        x_max = max(e.x_max for e in entities)
        y_max = max(e.y_max for e in entities)
        z_max = max(e.z_max for e in entities)

        rx = 0
        ry = 0
        rz = 0
        
        width = x_max - x_min
        depth = y_max - y_min
        height = z_max - z_min

        super().__init__(x, y, z, rx, ry, rz, width, depth, height)

        self.x_min = x_min
        self.y_min = y_min
        self.z_min = z_min
        self.x_max = x_max
        self.y_max = y_max
        self.z_max = z_max   
        self.entities = entities

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

class Player(CompoundEntity):
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
        hip = Box('dark_blue', x, y, hip_z, 0, 0, 0, hip_w, hip_h, hip_h)
        body = Box('dark_blue', x, y, body_z, 0, 0, 0, body_w, body_h)
        sho = Box('dark_blue', x, y, sho_z, 0, 0, 0, sho_w, hip_h, hip_h)
        arm1 = Box('dark_blue', x-leg_off, y, arm_z, 0, 0, 0, leg_w, arm_h)
        arm2 = Box('dark_blue', x+leg_off, y, arm_z, 0, 0, 0, leg_w, arm_h)
        head = Sphere('dark_blue', x, y, head_z, 0, 0, 0, head_h)
        super().__init__(leg1, leg2, hip, body, sho, arm1, arm2, head)
        self.anim = 0
        self.anim_dir = 0.000001

    def walk(self):
        leg1 = self.entities[0]
        leg2 = self.entities[1]

        if self.anim > 1 or self.anim < -1:
            self.anim_dir *= -1
        self.anim += self.anim_dir
        ay1 = (leg1.y_max + leg1.y_min)/2
        ay2 = (leg2.y_max + leg2.y_min)/2

        leg1.rotate_x(7*self.anim, ay1, leg1.z_max)
        leg2.rotate_x(-7*self.anim, ay2, leg2.z_max)


    
