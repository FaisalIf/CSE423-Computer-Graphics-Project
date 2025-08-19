from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from palette import get_color

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glutSwapBuffers()
    
def animate():
    glutPostRedisplay()
    
def keys(key, x, y):
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
    
    # Event Listners
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keys)
    glutSpecialFunc(keys)
    glutMouseFunc(clicks)

    # Camera Setup
    fov_y, aspect_ratio, near, far = 130, (win_w/win_h), 0.1, 5000
    glMatrixMode(GL_PROJECTION)
    gluPerspective(fov_y, aspect_ratio, near, far)

    # Clear Setup
    background_color = get_color('dark_grey')
    glClearColor(*background_color, 1)

    glutMainLoop()
    
if __name__ == "__main__":
    main()
