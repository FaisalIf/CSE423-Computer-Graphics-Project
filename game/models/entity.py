from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

from palette import get_color

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
