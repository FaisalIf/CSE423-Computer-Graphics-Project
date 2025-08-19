from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from palette import get_color

class Entity:
    """Create a basic entity with bounding box and collision logic"""
    def __init__(self, x, y, z, width, depth, height):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.depth = depth
        self.height = height
        # Bounding box
        self.x_min = x - width/2
        self.y_min = y - depth/2
        self.z_min = z - height/2
        self.x_max = self.x_min + width
        self.y_max = self.y_min + depth
        self.z_max = self.z_min + height

    def check_collision(self, other):
        """Return True if this entity collides with another"""
        return (self.x_min <= other.x_max and self.x_max >= other.x_min and
                self.y_min <= other.y_max and self.y_max >= other.y_min and
                self.z_min <= other.z_max and self.z_max >= other.z_min)

    def draw(self):
        """Draw the entity. Must be implemented by subclasses"""
        raise NotImplementedError("Each entity must implement draw()")

class Shape3D(Entity):
    quadric = gluNewQuadric()

class Sphere(Shape3D):
        def __init__(self, color, x, y, z, width, depth, height):
            super().__init__(x, y, z, width, depth, height)
            self.color = get_color(color)
        
        def draw(self):
            glColor3f(*self.color)
            glPushMatrix()
            glTranslatef(self.x, self.y, self.z)
            glScalef(self.width, self.depth, self.height)
            gluSphere(self.quadric, 1, 10, 25)
            glPopMatrix()
            
class CompoundEntity:
    def __init__(self, *entities):
        if len(entities) < 2:
            raise ValueError("Compound entities must have atleast two child entities")

        self.entities = entities
            
        self.x = sum(e.x for e in entities)/len(entities)
        self.y = sum(e.y for e in entities)/len(entities)
        self.z = sum(e.z for e in entities)/len(entities)

        # Bounding Box
        self.x_min = min(e.x_min for e in entities)
        self.y_min = min(e.y_min for e in entities)
        self.z_min = min(e.z_min for e in entities)
        self.x_max = max(e.x_max for e in entities)
        self.y_max = max(e.y_max for e in entities)
        self.z_max = max(e.z_max for e in entities)

    def check_collision(self, other): 
        # Quick bounding box rejection
        if not (
            self.x_min <= other.x_max and self.x_max >= other.x_min and
            self.y_min <= other.y_max and self.y_max >= other.y_min and
            self.z_min <= other.z_max and self.z_max >= other.z_min
        ):
            return False
            
        # Fine-grained: Compound-Compound
        if isinstance(other, CompoundEntity):
            for e in self.entities:
                for o in other.entities:
                    if e.check_collision(o):
                        return True
        
        # Fine-grained: Compound-Simple
        return any(e.check_collision(other) for e in self.entities)

    def draw(self):
        for e in self.entities: e.draw()
