import arcade
import math
import random

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Space Shooter"

PLAYER_SPEED = 340
PLAYER_MAX_HEALTH = 120
PLAYER_RADIUS = 22

PLAYER_BULLET_SPEED = 760
ENEMY_BULLET_SPEED = 360

ENEMY_MIN_SPEED = 36
ENEMY_MAX_SPEED = 72

ENEMY_SPAWN_BASE = 1.0
BOSS_SPAWN_SCORE = 300

STAR_COUNT = 80


def make_sprite(path, scale, x, y, fallback_size, fallback_color):
    try:
        return arcade.Sprite(path, scale=scale, center_x=x, center_y=y)
    except Exception:
        sprite = arcade.SpriteSolidColor(fallback_size, fallback_size, fallback_color)
        sprite.center_x = x
        sprite.center_y = y
        return sprite


def draw_sprite_compat(sprite):
    if hasattr(sprite, "draw"):
        sprite.draw()
    else:
        arcade.draw_sprite(sprite)


class Bullet:
    def __init__(self, x, y, dx, dy, speed, damage, enemy=False):
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.damage = damage
        self.enemy = enemy
        self.radius = 6 if enemy else 5

        if enemy:
            self.sprite = make_sprite(
                ":resources:images/space_shooter/laserRed01.png",
                0.65,
                x,
                y,
                8,
                arcade.color.ORANGE_RED,
            )
        else:
            self.sprite = make_sprite(
                ":resources:images/space_shooter/laserBlue01.png",
                0.65,
                x,
                y,
                8,
                arcade.color.AQUA,
            )

        self.sprite.angle = math.degrees(math.atan2(dy, dx)) - 90

    @property
    def x(self):
        return self.sprite.center_x

    @property
    def y(self):
        return self.sprite.center_y

    def update(self, dt):
        self.sprite.center_x += self.dx * self.speed * dt
        self.sprite.center_y += self.dy * self.speed * dt

    def draw(self):
        draw_sprite_compat(self.sprite)

    def off_screen(self):
        return self.x < -30 or self.x > SCREEN_WIDTH + 30 or self.y < -30 or self.y > SCREEN_HEIGHT + 30


class Enemy:
    def __init__(self, x, y, health, speed):
        self.health = health
        self.max_health = health
        self.speed = speed
        self.radius = 22
        self.shoot_timer = random.uniform(0.8, 1.8)
        enemy_skin = random.choice(
            [
                ":resources:images/space_shooter/playerShip1_green.png",
                ":resources:images/space_shooter/playerShip2_orange.png",
                ":resources:images/space_shooter/playerShip3_orange.png",
            ]
        )
        self.sprite = make_sprite(
            enemy_skin,
            0.5,
            x,
            y,
            36,
            (223, 66, 74),
        )

    @property
    def x(self):
        return self.sprite.center_x

    @property
    def y(self):
        return self.sprite.center_y

    def update(self, dt, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(1, math.hypot(dx, dy))
        self.sprite.center_x += dx / dist * self.speed * dt
        self.sprite.center_y += dy / dist * self.speed * dt
        self.sprite.angle = math.degrees(math.atan2(dy, dx)) - 90
        self.shoot_timer -= dt

    def draw(self):
        draw_sprite_compat(self.sprite)


class BossEnemy:
    def __init__(self):
        self.health = 700
        self.max_health = 700
        self.radius = 52
        self.phase = 0.0
        self.shoot_timer = 0.45
        self.sprite = make_sprite(
            ":resources:images/space_shooter/playerShip1_green.png",
            1.1,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 110,
            86,
            (107, 33, 159),
        )

    @property
    def x(self):
        return self.sprite.center_x

    @property
    def y(self):
        return self.sprite.center_y

    def update(self, dt):
        self.phase += dt
        self.sprite.center_x = SCREEN_WIDTH / 2 + math.sin(self.phase * 0.9) * 300
        self.sprite.center_y = SCREEN_HEIGHT - 115 + math.sin(self.phase * 2.1) * 20
        self.sprite.angle = math.sin(self.phase * 2.0) * 10
        self.shoot_timer -= dt

    def draw(self):
        draw_sprite_compat(self.sprite)


class PowerUp:
    def __init__(self, x, y, kind):
        self.kind = kind
        self.radius = 16
        self.fall_speed = 95
        self.time_left = 10.0

        texture_path = ":resources:images/items/gemBlue.png"
        fallback_color = (113, 202, 255)
        if kind == "heal":
            texture_path = ":resources:images/items/gemGreen.png"
            fallback_color = (72, 230, 134)
        elif kind == "rapid":
            texture_path = ":resources:images/items/gemYellow.png"
            fallback_color = (255, 212, 76)

        self.sprite = make_sprite(texture_path, 0.7, x, y, 24, fallback_color)

    @property
    def x(self):
        return self.sprite.center_x

    @property
    def y(self):
        return self.sprite.center_y

    def update(self, dt):
        self.sprite.center_y -= self.fall_speed * dt
        self.sprite.angle += 80 * dt
        self.time_left -= dt

    def draw(self):
        draw_sprite_compat(self.sprite)

    def expired(self):
        return self.time_left <= 0 or self.y < -40


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color((10, 14, 28))
        self.space_bg = make_sprite(
            ":resources:images/backgrounds/stars.png",
            2.2,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            SCREEN_WIDTH,
            (10, 14, 28),
        )

        self.snd_shoot = self._try_load_sound(":resources:sounds/laser2.wav")
        self.snd_hit = self._try_load_sound(":resources:sounds/hit5.wav")
        self.snd_enemy_down = self._try_load_sound(":resources:sounds/explosion2.wav")
        self.snd_pickup = self._try_load_sound(":resources:sounds/upgrade5.wav")
        self.snd_player_hit = self._try_load_sound(":resources:sounds/lose4.wav")
        self.snd_boss_down = self._try_load_sound(":resources:sounds/gameover1.wav")
        self._reset_game_state()

    def _reset_game_state(self):
        self.player_x = SCREEN_WIDTH / 2
        self.player_y = 100
        self.player_angle = 0.0
        self.player_health = PLAYER_MAX_HEALTH
        self.player_radius = PLAYER_RADIUS
        self.player_sprite = make_sprite(
            ":resources:images/space_shooter/playerShip1_orange.png",
            0.55,
            self.player_x,
            self.player_y,
            42,
            (83, 232, 255),
        )

        self.score = 0
        self.game_over = False
        self.win = False

        self.keys_pressed = set()
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.powerups = []
        self.boss = None

        self.fire_cooldown = 0.0
        self.enemy_spawn_timer = 0.8

        self.rapid_fire_time = 0.0
        self.shield_time = 0.0

        self.mouse_x = self.player_x
        self.mouse_y = self.player_y + 100

        self.stars = [
            [random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT), random.uniform(10, 42)]
            for _ in range(STAR_COUNT)
        ]

    def _try_load_sound(self, path):
        try:
            return arcade.load_sound(path)
        except Exception:
            return None

    def _play_sound(self, snd, volume=0.4):
        if snd is None:
            return
        try:
            arcade.play_sound(snd, volume=volume)
        except Exception:
            pass

    def _spawn_enemy(self):
        edge = random.choice(["top", "left", "right"])
        if edge == "top":
            x = random.uniform(40, SCREEN_WIDTH - 40)
            y = SCREEN_HEIGHT + 30
        elif edge == "left":
            x = -30
            y = random.uniform(120, SCREEN_HEIGHT - 50)
        else:
            x = SCREEN_WIDTH + 30
            y = random.uniform(120, SCREEN_HEIGHT - 50)

        hp = random.randint(26, 44)
        speed = random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)
        self.enemies.append(Enemy(x, y, hp, speed))

    def _maybe_drop_powerup(self, x, y):
        if random.random() > 0.24:
            return

        r = random.random()
        if r < 0.40:
            kind = "heal"
        elif r < 0.74:
            kind = "rapid"GameWindow
        else:
            kind = "shield"

        self.powerups.append(PowerUp(x, y, kind))

    def _aim_direction(self):
        dx = self.mouse_x - self.player_x
        dy = self.mouse_y - self.player_y
        dist = max(1, math.hypot(dx, dy))
        return dx / dist, dy / dist

    def _apply_damage(self, dmg):
        if self.shield_time > 0:
            dmg *= 0.18
        self.player_health -= dmg
        self._play_sound(self.snd_player_hit, 0.23)

    def on_draw(self):
        self.clear()
        draw_sprite_compat(self.space_bg)

        for star in self.stars:
            arcade.draw_circle_filled(star[0], star[1], 1.4, (170, 205, 255, 180))

        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, 72, (9, 12, 20, 220))

        for bullet in self.player_bullets:
            bullet.draw()
        for bullet in self.enemy_bullets:
            bullet.draw()

        for p in self.powerups:
            p.draw()

        for enemy in self.enemies:
            enemy.draw()
            bar_w = 40
            ratio = max(0.0, enemy.health / enemy.max_health)
            left = enemy.x - bar_w / 2
            bottom = enemy.y + enemy.radius + 8
            arcade.draw_lrbt_rectangle_filled(left, left + bar_w, bottom, bottom + 5, (50, 50, 50, 220))
            arcade.draw_lrbt_rectangle_filled(left, left + bar_w * ratio, bottom, bottom + 5, (70, 220, 130, 240))

        if self.boss is not None:
            self.boss.draw()
            bw = 470
            bh = 18
            bx = SCREEN_WIDTH / 2 - bw / 2
            by = SCREEN_HEIGHT - 30
            ratio = max(0.0, self.boss.health / self.boss.max_health)
            arcade.draw_lrbt_rectangle_filled(bx, bx + bw, by, by + bh, (45, 35, 58, 230))
            arcade.draw_lrbt_rectangle_filled(bx, bx + bw * ratio, by, by + bh, (197, 70, 255, 235))
            arcade.draw_text("BOSS", bx - 58, by + 1, arcade.color.WHITE, 14, bold=True)

        if self.shield_time > 0:
            arcade.draw_circle_outline(self.player_x, self.player_y, self.player_radius + 10, (113, 202, 255), 3)

        draw_sprite_compat(self.player_sprite)

        arcade.draw_text(f"Score: {self.score}", 20, SCREEN_HEIGHT - 30, arcade.color.WHITE, 18, bold=True)
        arcade.draw_text(
            f"Health: {max(0, int(self.player_health))}/{PLAYER_MAX_HEALTH}",
            20,
            SCREEN_HEIGHT - 54,
            (110, 255, 150),
            16,
            bold=True,
        )

        info_y = SCREEN_HEIGHT - 78
        if self.rapid_fire_time > 0:
            arcade.draw_text(f"Rapid Fire: {self.rapid_fire_time:0.1f}s", 20, info_y, (255, 220, 96), 14, bold=True)
            info_y -= 20
        if self.shield_time > 0:
            arcade.draw_text(f"Shield: {self.shield_time:0.1f}s", 20, info_y, (136, 218, 255), 14, bold=True)

        arcade.draw_text("WASD Move | Mouse Aim | SPACE Shoot", 650, SCREEN_HEIGHT - 35, arcade.color.LIGHT_GRAY, 12)

        if self.game_over:
            msg = "You Win" if self.win else "Game Over"
            arcade.draw_text(msg, SCREEN_WIDTH / 2 - 110, SCREEN_HEIGHT / 2 + 24, arcade.color.WHITE, 42, bold=True)
            arcade.draw_text("Press R to Restart", SCREEN_WIDTH / 2 - 96, SCREEN_HEIGHT / 2 - 16, arcade.color.LIGHT_GRAY, 18)

    def on_update(self, dt):
        if self.game_over:
            return

        self.rapid_fire_time = max(0.0, self.rapid_fire_time - dt)
        self.shield_time = max(0.0, self.shield_time - dt)

        for star in self.stars:
            star[1] -= star[2] * dt
            if star[1] < -5:
                star[0] = random.uniform(0, SCREEN_WIDTH)
                star[1] = SCREEN_HEIGHT + 5

        vx = 0
        vy = 0
        if arcade.key.W in self.keys_pressed:
            vy += 1
        if arcade.key.S in self.keys_pressed:
            vy -= 1
        if arcade.key.A in self.keys_pressed:
            vx -= 1
        if arcade.key.D in self.keys_pressed:
            vx += 1

        if vx or vy:
            length = math.hypot(vx, vy)
            vx /= length
            vy /= length
            self.player_x += vx * PLAYER_SPEED * dt
            self.player_y += vy * PLAYER_SPEED * dt

        self.player_x = max(20, min(SCREEN_WIDTH - 20, self.player_x))
        self.player_y = max(20, min(SCREEN_HEIGHT - 20, self.player_y))

        dx, dy = self._aim_direction()
        self.player_angle = math.degrees(math.atan2(dy, dx))
        self.player_sprite.center_x = self.player_x
        self.player_sprite.center_y = self.player_y
        self.player_sprite.angle = self.player_angle - 90

        self.fire_cooldown -= dt
        fire_delay = 0.045 if self.rapid_fire_time > 0 else 0.095
        if arcade.key.SPACE in self.keys_pressed and self.fire_cooldown <= 0:
            self.player_bullets.append(
                Bullet(self.player_x + dx * 18, self.player_y + dy * 18, dx, dy, PLAYER_BULLET_SPEED, 21, enemy=False)
            )
            self._play_sound(self.snd_shoot, 0.25)
            self.fire_cooldown = fire_delay

        self.enemy_spawn_timer -= dt
        if self.boss is None and self.enemy_spawn_timer <= 0:
            self._spawn_enemy()
            self.enemy_spawn_timer = max(0.35, ENEMY_SPAWN_BASE - self.score / 850)

        if self.boss is None and self.score >= BOSS_SPAWN_SCORE:
            self.boss = BossEnemy()

        for bullet in self.player_bullets:
            bullet.update(dt)
        for bullet in self.enemy_bullets:
            bullet.update(dt)
        for p in self.powerups:
            p.update(dt)

        for enemy in self.enemies:
            enemy.update(dt, self.player_x, self.player_y)
            if enemy.shoot_timer <= 0:
                ex = self.player_x - enemy.x
                ey = self.player_y - enemy.y
                dist = max(1, math.hypot(ex, ey))
                self.enemy_bullets.append(Bullet(enemy.x, enemy.y, ex / dist, ey / dist, ENEMY_BULLET_SPEED, 10, enemy=True))
                enemy.shoot_timer = random.uniform(1.0, 2.0)

        if self.boss is not None:
            self.boss.update(dt)
            if self.boss.shoot_timer <= 0:
                base = math.atan2(self.player_y - self.boss.y, self.player_x - self.boss.x)
                for ang in (base - 0.18, base, base + 0.18):
                    self.enemy_bullets.append(
                        Bullet(self.boss.x, self.boss.y, math.cos(ang), math.sin(ang), ENEMY_BULLET_SPEED + 110, 12, enemy=True)
                    )
                self.boss.shoot_timer = 0.45

        for bullet in self.player_bullets[:]:
            hit = False
            for enemy in self.enemies[:]:
                if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) <= enemy.radius + bullet.radius:
                    enemy.health -= bullet.damage
                    hit = True
                    self._play_sound(self.snd_hit, 0.18)
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.score += 25
                        self._play_sound(self.snd_enemy_down, 0.25)
                        self._maybe_drop_powerup(enemy.x, enemy.y)
                    break

            if self.boss is not None and not hit:
                if math.hypot(bullet.x - self.boss.x, bullet.y - self.boss.y) <= self.boss.radius + bullet.radius:
                    self.boss.health -= bullet.damage
                    hit = True
                    self.score += 2
                    self._play_sound(self.snd_hit, 0.12)
                    if self.boss.health <= 0:
                        self.score += 600
                        self._play_sound(self.snd_boss_down, 0.45)
                        self.win = True
                        self.game_over = True

            if hit or bullet.off_screen():
                self.player_bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            if math.hypot(bullet.x - self.player_x, bullet.y - self.player_y) <= self.player_radius + bullet.radius:
                self._apply_damage(bullet.damage)
                self.enemy_bullets.remove(bullet)
            elif bullet.off_screen():
                self.enemy_bullets.remove(bullet)

        for enemy in self.enemies:
            if math.hypot(enemy.x - self.player_x, enemy.y - self.player_y) <= enemy.radius + self.player_radius:
                self._apply_damage(25 * dt)

        if self.boss is not None:
            if math.hypot(self.boss.x - self.player_x, self.boss.y - self.player_y) <= self.boss.radius + self.player_radius:
                self._apply_damage(40 * dt)

        for p in self.powerups[:]:
            if p.expired():
                self.powerups.remove(p)
                continue

            if math.hypot(p.x - self.player_x, p.y - self.player_y) <= self.player_radius + p.radius + 2:
                if p.kind == "heal":
                    self.player_health = min(PLAYER_MAX_HEALTH, self.player_health + 35)
                elif p.kind == "rapid":
                    self.rapid_fire_time = 8.0
                else:
                    self.shield_time = 7.0
                self._play_sound(self.snd_pickup, 0.33)
                self.powerups.remove(p)

        if self.player_health <= 0:
            self.player_health = 0
            self.game_over = True

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)
        if key == arcade.key.R and self.game_over:
            self._reset_game_state()

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

def main():
    GameWindow()
    arcade.run()

if __name__ == "__main__":
    main()