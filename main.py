from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from game.models.models import *

class Cam3rd:
    def __init__(self, ex, ey, ez, cx, cy, cz, ux=0, uy=0, uz=1):
        self.eye_x = ex
        self.eye_y = ey
        self.eye_z = ez
        self.cen_x = cx
        self.cen_y = cy
        self.cen_z = cz
        self.up_x = ux
        self.up_y = uy
        self.up_z = uz
    def move(self, dx, dy, dz):
        self.eye_x += dx
        self.eye_y += dy
        self.eye_z += dz
        self.cen_x += dx
        self.cen_y += dy
        self.cen_z += dz
    def get_cam(self):
        return (self.eye_x, self.eye_y, self.eye_z,
                self.cen_x, self.cen_y, self.cen_z,
                self.up_x,  self.up_y,  self.up_z)

#def Cam1st:
#    def __init__(self, entity):
#        self.entity = entity
#    def get_cam(self):
#        ex, ey, ez = self.entity.x, self.entity.y, self.entity.z
#        rx, ry, rz = self.entity.rx, self.entity.ry, self.entity.rz
#        cx = ex + math.cos(math.radians(rx))
#        cy = ex + math.sin(math.radians(ry))
#        cz = ex + math.cos(math.radians(rx))
#
#        return (self.entity.x, self.entity.y, self.entity.z,
#                self.cen_x, self.cen_y, self.cen_z,
#                self.up_x,  self.up_y,  self.up_z)

def camera(cam):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    view = cam.get_cam()
    gluLookAt(*view)

def display():
    global floor, cam1, chest, player
    glClear(GL_COLOR_BUFFER_BIT)
    camera(cam1)
    floor.draw()
    chest.draw()
    player.draw()
    glutSwapBuffers()
    
def animate():
    global player
    player.walk()
    glutPostRedisplay()
    
def keys(key, x, y):
    global cam1, chest
    if key == b'w':
        cam1.move(0, 1, 0)
    if key == b'a':
        cam1.move(-1, 0, 0)
    if key == b's':
        cam1.move(0, -1, 0)
    if key == b'd':
        cam1.move(1, 0, 0)
    if key == b'k':
        chest.toggle() 
        

def special_keys(key, x, y):
    pass
    
def clicks(button, state, x, y):
    pass

def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)

    # Window
    win_w, win_h, win_x, win_y = 1000, 800, 0, 0
    window_title = b'Demons & Portals'
    glutInitWindowSize(win_w, win_h)
    glutInitWindowPosition(win_x, win_y)
    glutCreateWindow(window_title)

    # Entities
    global floor, cam1, chest, player
    floor = Box('toothpaste', 0, 0, 5, 0, 0, 0, 200, 800, 10)
    cam1 = Cam3rd(50, -200, 200, 0, 0, 0, 0, 0, 1)
    chest = Chest(0, 100, 10)
    player = Player(0, 0, 10, 0)
    
    # Event Listners
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keys)
    glutSpecialFunc(special_keys)
    glutMouseFunc(clicks)

    # Camera Setup
    fov_y, aspect_ratio, near, far = 77.3, (win_w/win_h), 0.1, 5000
    glMatrixMode(GL_PROJECTION)
    gluPerspective(fov_y, aspect_ratio, near, far)

    # Clear Setup
    background_color = get_color('dark_grey')
    glClearColor(*background_color, 1)

    glutMainLoop()
    
if __name__ == "__main__":
    main()
