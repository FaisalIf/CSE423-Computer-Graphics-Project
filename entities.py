from palette import get_color

class Shape:
    def __init__(self, x, y, z, l, b, h):
        # Center position
        self.x = x
        self.y = y
        self.z = z

        # Bounding box
        self.x_min = x - l/2
        self.y_min = y - b/2
        self.z_min = z - h/2
        self.x_max = self.x_min+l
        self.y_max = self.y_min+b
        self.z_max = self.z_min+h

    def check_collision(self, other):
        # AABB       
        return (self.x_min <= other.x_max and self.x_max >= other.x_min and
                self.y_min <= other.y_max and self.y_max >= other.y_min and
                self.z_min <= other.z_max and self.z_max >= other.z_min)

    def draw(self):
        raise NotImplementedError("Each shape must implement draw()")

class 3DShape(Shape):
    quadric = gluNewQuadric()

class Sphere(3DShape):
        def __init__(self, color, x, y, z, l, b, h):
            super().__init__(x, y, z, l, b, h)
            self.color = get_color(color)
        def draw(self):
            glColor3f(*self.color)
            glPushMatrix()
            glScalef(l, b, h)
            glSphere(self.quadric, 1, 10, 25)
            glPopMatrix()
class CompoundShape:
    def __init__(self, *shapes):
        self.shapes = shapes

        if len(shapes) == 0:
            raise ValueError("CompoundShape must have atleast one child shape")
            
        self.x = sum(s.x for s in shapes)/len(shapes)
        self.y = sum(s.x for s in shapes)/len(shapes)
        self.z = sum(s.x for s in shapes)/len(shapes)


        # Bounding Box
        self.x_min = min(s.x_min for s in shapes)
        self.y_min = min(s.y_min for s in shapes)
        self.z_min = min(s.z_min for s in shapes)
        self.x_max = max(s.x_max for s in shapes)
        self.y_max = max(s.y_max for s in shapes)
        self.z_max = max(s.z_max for s in shapes)

    def check_collision(self, other): 
        # Quick bounding box rejection
        if not (
            self.x_min <= other.x_max and self.x_max >= other.x_min and
            self.y_min <= other.y_max and self.y_max >= other.y_min and
            self.z_min <= other.z_max and self.z_max >= other.z_min
        ):
            return False
        # Fine-grained: Compound-Compound
        if isInstance(other, CompoundShape):
            for s in self.shapes:
                for o in other.shapes:
                    if s.check_collision(o):
                        return True
        
        # Fine-grained: Compound-Simple
        return any(s.check_collision(other) for s in self.shapes)
