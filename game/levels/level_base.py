from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ..engine import Scene
from ..ui.hud import HUD
from ..entities.player import Player
from ..entities.enemy import Enemy
from ..weapons.handgun import Handgun
from ..weapons.portalgun import PortalGun
from ..items.items import Chest, Item
from .world import World


class LevelScene(Scene):
    def __init__(self, difficulty=1, boss=False):
        self.hud = HUD()
        self.world = World()
        self.player = Player()
        self.world.player = self.player
        self.handgun = Handgun(self.player)
        self.portalgun = PortalGun(self.player)
        self.world.portalgun = self.portalgun
        self.keys_down = set()
        self.difficulty = difficulty
        self.boss = boss
        self.scope = False
        self.perspective_third = True
        self.checkpoint_uses = 3
        self.cam_offset = [0, -200, 120]

        self._setup_level()

    def _setup_level(self):
        # Populate enemies
        enemy_count = 3 if self.difficulty == 1 else (6 if self.difficulty == 2 else 10)
        for i in range(enemy_count):
            e = Enemy(boss=False)
            e.pos = [i * 80 - 200, 200 + 40 * (i % 3), 12]
            self.world.enemies.append(e)
        if self.boss:
            boss = Enemy(boss=True)
            boss.pos = [0, 400, 12]
            self.world.enemies.append(boss)

        # Chests and items
        c1 = Chest()
        c1.pos = [-150, 150, 10]
        c1.contents = [Item('Vitae')]
        c2 = Chest()
        c2.pos = [200, 100, 10]
        c2.contents = [Item('Aegis')]
        c3 = Chest()
        c3.pos = [0, 250, 10]
        c3.contents = [Item('Shard')]
        self.world.chests.extend([c1, c2, c3])

        # Checkpoints
        self.world.checkpoints = [[0, 0, 20], [0, 200, 20], [0, 400, 20]]

    def update(self, dt):
        # input handled on key press; no continuous key state to avoid sticky move
        self.player.update(dt)

        # weapon updates
        self.handgun.update(dt)
        self.portalgun.update(dt)

        # world updates
        self.world.update(dt)

        # bullet collisions
        for b in list(self.world.bullets):
            # enemy bullets hit player
            if not b.friendly:
                dx = b.pos[0] - self.player.pos[0]
                dy = b.pos[1] - self.player.pos[1]
                dz = b.pos[2] - self.player.pos[2]
                if (dx*dx + dy*dy + dz*dz) ** 0.5 < (b.radius + 6):
                    self.player.take_damage(15)
                    b.alive = False
            else:
                for e in list(self.world.enemies):
                    dx = b.pos[0] - e.pos[0]
                    dy = b.pos[1] - e.pos[1]
                    dz = b.pos[2] - e.pos[2]
                    if (dx*dx + dy*dy + dz*dz) ** 0.5 < (b.radius + e.radius):
                        e.alive = False
                        self.hud.score += 10
                        b.alive = False

        # Pickup items
        for it in list(self.world.items):
            dx = it.pos[0] - self.player.pos[0]
            dy = it.pos[1] - self.player.pos[1]
            if (dx*dx + dy*dy) ** 0.5 < 20:
                if it.name == 'Vitae':
                    self.player.heal(20)
                elif it.name == 'Aegis':
                    # simple instant shield: heal small chunk
                    self.player.heal(10)
                elif it.name == 'Shard':
                    self.player.damage += 10
                self.world.items.remove(it)

    def camera_hook(self, camera):
        # scope narrows fov and forces first-person
        if self.scope:
            camera.fovY = 60.0
            camera.pos = [self.player.pos[0], self.player.pos[1] - 10, self.player.pos[2] + 5]
        else:
            camera.fovY = 120.0
            if self.perspective_third:
                camera.pos = [self.player.pos[0] + self.cam_offset[0], self.player.pos[1] + self.cam_offset[1], self.player.pos[2] + self.cam_offset[2]]
            else:
                camera.pos = [self.player.pos[0], self.player.pos[1] - 10, self.player.pos[2] + 5]
        camera.look = [self.player.pos[0], self.player.pos[1] + 50, self.player.pos[2]]

    def draw(self):
        # world
        self.world.draw()
        # player
        self.player.draw()
        # HUD
        self.player.render_ui()
        self.hud.draw_inventory(self.player)
        self.hud.draw_score()
        self.hud.draw_radar()
        self.hud.draw_menu()
        self.hud.draw_crosshair(scoped=self.scope)

    def on_key(self, key):
        self.keys_down.add(key)
        if key == b'\x1b':  # ESC handled by engine pause
            self.hud.paused = not self.hud.paused
        if key == b' ':
            self.player.jump()
        if key == b'r':
            self.handgun.reload()
        if key == b'p':
            self.perspective_third = not self.perspective_third
        # WASD discrete movement per press
        step = 20
        if key == b'w':
            self.player.pos[1] += step
        if key == b's':
            self.player.pos[1] -= step
        if key == b'a':
            self.player.pos[0] -= step
        if key == b'd':
            self.player.pos[0] += step
        # number keys 1-9
        if key in [bytes(str(i), 'utf-8') for i in range(1, 10)]:
            self.player.inventory.select(int(key.decode()) - 1)
        # checkpoint quick save
        if key == b'c':
            self.world.save_checkpoint()
        # quick load uses
        if key == b'l' and self.checkpoint_uses > 0:
            self.world.load_checkpoint()
            self.checkpoint_uses -= 1

    def on_special(self, key):
        # camera arrows -> pan camera target when third person
        if self.perspective_third and not self.scope:
            if key == GLUT_KEY_LEFT:
                self.cam_offset[0] -= 5
            if key == GLUT_KEY_RIGHT:
                self.cam_offset[0] += 5
            if key == GLUT_KEY_UP:
                self.cam_offset[2] += 5
            if key == GLUT_KEY_DOWN:
                self.cam_offset[2] -= 5

    def on_mouse(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            # fire depends on selected: 0 handgun, 1 portalgun
            if self.player.inventory.selected == 0:
                self.handgun.fire(self.world)
            else:
                self.portalgun.place_portal(self.world)
        if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            self.scope = not self.scope
            self.player.scoped = self.scope
        # mouse wheel (common GLUT mapping)
        if state == GLUT_DOWN and (button == 3 or button == 4):
            step = -1 if button == 3 else 1
            self.player.inventory.next(step)
