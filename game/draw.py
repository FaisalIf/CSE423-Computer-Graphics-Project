from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Only using allowed GL/GLU/GLUT calls

def text2d(x, y, text, font=None):
    if font is None:
        # try to get font attributes from GLUT module
        font = getattr(__import__('OpenGL.GLUT', fromlist=['']), 'GLUT_BITMAP_HELVETICA_18', None)
        if font is None:
            font = getattr(__import__('OpenGL.GLUT', fromlist=['']), 'GLUT_BITMAP_8_BY_13', None)
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

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


def draw_stickman(scale=1.0, color=(1, 1, 1)):
    glPushMatrix()
    # Simple manual scaling by adjusting sizes
    head_r = 8 * scale
    body_h = 30 * scale
    limb_h = 20 * scale
    glColor3f(*color)
    # head
    gluSphere(gluNewQuadric(), head_r, 10, 10)
    # body
    glTranslatef(0, 0, -20)
    gluCylinder(gluNewQuadric(), 2*scale, 2*scale, body_h, 8, 1)
    # legs
    glPushMatrix()
    glTranslatef(-3, 0, -30)
    gluCylinder(gluNewQuadric(), 1.5*scale, 1.5*scale, limb_h, 6, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(3, 0, -30)
    gluCylinder(gluNewQuadric(), 1.5*scale, 1.5*scale, limb_h, 6, 1)
    glPopMatrix()
    # arms
    glTranslatef(0, 0, -10)
    glPushMatrix()
    glTranslatef(-8, 0, 10)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 1.3*scale, 1.3*scale, 15*scale, 6, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(8, 0, 10)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 1.3*scale, 1.3*scale, 15*scale, 6, 1)
    glPopMatrix()
    glPopMatrix()


def draw_enemy(pulse=0.0, color=(1, 0, 0)):
    glPushMatrix()
    s = 12 + 2 * pulse
    glColor3f(*color)
    gluSphere(gluNewQuadric(), s, 10, 10)
    glTranslatef(0, 0, -s - (6 + pulse))
    gluSphere(gluNewQuadric(), 6 + pulse, 10, 10)
    glPopMatrix()


def draw_chest():
    glPushMatrix()
    glColor3f(0.7, 0.4, 0.2)
    glutSolidCube(20)
    glTranslatef(0, 0, 12)
    glColor3f(0.8, 0.5, 0.3)
    gluCylinder(gluNewQuadric(), 10, 10, 6, 10, 1)
    glPopMatrix()


def draw_portal(elliptical_scale=(1.0, 1.5), color=(0, 0, 1)):
    glPushMatrix()
    glColor3f(*color)
    # Approximate an ellipse portal using stacked thin cylinders
    h = 0.5 * elliptical_scale[1]
    r = 6 * elliptical_scale[0]
    gluCylinder(gluNewQuadric(), r, r, h, 10, 1)
    glPopMatrix()


def draw_bullet(radius=2.0, color=(1, 0, 0)):
    glPushMatrix()
    glColor3f(*color)
    gluSphere(gluNewQuadric(), radius, 8, 8)
    glPopMatrix()


def draw_floor(grid=600):
    glBegin(GL_QUADS)

    glColor3f(1, 1, 1)
    glVertex3f(-grid, grid, 0)
    glVertex3f(0, grid, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(-grid, 0, 0)

    glVertex3f(grid, -grid, 0)
    glVertex3f(0, -grid, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(grid, 0, 0)

    glColor3f(0.7, 0.5, 0.95)
    glVertex3f(-grid, -grid, 0)
    glVertex3f(-grid, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, -grid, 0)

    glVertex3f(grid, grid, 0)
    glVertex3f(grid, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, grid, 0)
    glEnd()
