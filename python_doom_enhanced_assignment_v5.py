"""
PYTHON DOOM-STYLE FPS - ONE ORIGINAL LEVEL
-------------------------------------------
A beginner-friendly, single-file FPS made with Pygame.

Install:
    pip install pygame

Run:
    python python_doom.py

Controls:
    W / S       Move forward / backward
    A / D       Strafe left / right
    Left/Right  Turn
    Mouse       Turn
    E           Open doors / use exit
    SPACE       Jump
    Left Mouse  Shoot
    ESC         Quit

This is an original mini-level inspired by classic 1990s raycasting FPS games.
It does NOT contain original DOOM maps, sprites, sounds, or other copyrighted assets.
"""

import math
import random
import sys
import pygame

# ------------------------------------------------------------
# WEEK 2 WORLD-STATE DECISION
# This happens in the PowerShell window BEFORE the game opens.
# ------------------------------------------------------------
fuel_remaining = 15

if fuel_remaining < 20:
    print("Warning: fuel critical.")
    fight_back = input("Aliens are invading! Do you fight back? (y/n): ")

    if fight_back.lower() == "y":
        print("You grab your weapon and fight back!")
        print("Loading DOOM...")
    else:
        print("YOU DIED")
        sys.exit()
else:
    print("Fuel levels nominal.")

# ------------------------------------------------------------
# 1. BASIC SETTINGS
# ------------------------------------------------------------

WIDTH = 800
HEIGHT = 500

# The 3-D scene is rendered at a lower resolution and then
# enlarged. This gives it a chunky retro look.
VIEW_WIDTH = 400
VIEW_HEIGHT = 250

FOV = math.radians(70)
HALF_FOV = FOV / 2
MAX_DEPTH = 20

MOVE_SPEED = 3.0
TURN_SPEED = 2.2
JUMP_STRENGTH = 5.8
GRAVITY = 15.0
WEAPON_BOB_SPEED = 9.0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python DOOM-Style FPS - Enhanced Level")

view = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 64)

# ------------------------------------------------------------
# 2. THE LEVEL
# ------------------------------------------------------------
#
# # = wall
# . = empty floor
# D = RED DOOR (requires red key + all enemies defeated)
# K = red key
# E = level exit
#
# This is an ORIGINAL layout rather than a recreation of a
# DOOM map.
# ------------------------------------------------------------

LEVEL = [
    "################",
    "#..............#",
    "#.####.#####...#",
    "#.#............#",
    "#.#.####.####..#",
    "#.#.#..#.#.....#",
    "#...#..#.#.###.#",
    "###.#..#...#...#",
    "#K..#..#####.###",
    "#.###..........#",
    "#......D.......#",
    "################",
]

MAP_W = len(LEVEL[0])
MAP_H = len(LEVEL)

# ------------------------------------------------------------
# 3. PLAYER
# ------------------------------------------------------------

class Player:
    def __init__(self):
        self.x = 2.5
        self.y = 1.5

        # Angle is measured in radians.
        # 0 means looking toward the positive X direction.
        self.angle = 0.0

        self.health = 100
        self.ammo = 25
        self.has_key = False

        self.shoot_cooldown = 0.0
        self.hurt_flash = 0.0
        self.z = 0.0
        self.jump_velocity = 0.0
        self.bob_time = 0.0

player = Player()

# ------------------------------------------------------------
# 4. ENEMIES
# ------------------------------------------------------------

class Enemy:
    def __init__(self, x, y, kind="imp"):
        self.x = x
        self.y = y
        self.kind = kind
        self.max_health = 100 if kind == "imp" else 140
        self.health = self.max_health
        self.attack_timer = random.uniform(0.2, 1.0)
        self.alive = True
        self.death_timer = 0.0
        self.anim_time = random.uniform(0, math.tau)
        self.flash_timer = 0.0

def validate_enemy_positions():
    """Keep every enemy on a walkable tile and away from the player start."""
    for enemy in enemies:
        cell = cell_at(enemy.x, enemy.y)
        if cell != ".":
            raise ValueError(
                f"Enemy spawned on blocked tile at ({enemy.x:.1f}, {enemy.y:.1f})"
            )

enemies = [
    Enemy(8.5, 2.5, "imp"),
    Enemy(10.5, 3.5, "imp"),
    Enemy(12.5, 6.5, "brute"),
    Enemy(5.5, 9.5, "imp"),
    Enemy(8.5, 9.5, "brute"),
    Enemy(12.5, 9.5, "imp"),
    Enemy(6.5, 6.5, "imp"),
    Enemy(13.5, 2.5, "brute"),
]

# ------------------------------------------------------------
# VISUAL EFFECTS
# ------------------------------------------------------------

blood_particles = []
muzzle_flash_timer = 0.0
hit_marker_timer = 0.0
screen_shake_timer = 0.0
damage_vignette_timer = 0.0
game_time = 0.0
shell_particles = []
impact_sparks = []


class Particle:
    def __init__(self, x, y, z, vx, vy, vz, lifetime, size):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size


def spawn_blood(x, y, amount=18):
    """Create a burst of blood particles when an enemy is hit."""
    for _ in range(amount):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.5, 2.2)

        blood_particles.append(
            Particle(
                x, y,
                random.uniform(0.2, 0.9),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(0.5, 1.8),
                random.uniform(0.25, 0.7),
                random.uniform(0.03, 0.09),
            )
        )


def spawn_sparks(x, y, amount=8):
    for _ in range(amount):
        a = random.uniform(0, math.tau)
        speed = random.uniform(1.0, 3.0)
        impact_sparks.append(
            Particle(
                x, y, random.uniform(0.2, 1.0),
                math.cos(a) * speed,
                math.sin(a) * speed,
                random.uniform(0.5, 2.5),
                random.uniform(0.12, 0.35),
                random.uniform(0.02, 0.05),
            )
        )


def update_particles(dt):
    global muzzle_flash_timer, hit_marker_timer, screen_shake_timer
    global damage_vignette_timer, game_time

    game_time += dt

    for particle in blood_particles[:]:
        particle.lifetime -= dt
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
        particle.z += particle.vz * dt
        particle.vz -= 3.5 * dt
        if particle.lifetime <= 0 or particle.z < 0:
            blood_particles.remove(particle)

    for particle in shell_particles[:]:
        particle.lifetime -= dt
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
        particle.z += particle.vz * dt
        particle.vz -= 10.0 * dt
        if particle.lifetime <= 0 or particle.z < 0:
            shell_particles.remove(particle)

    for particle in impact_sparks[:]:
        particle.lifetime -= dt
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
        particle.z += particle.vz * dt
        particle.vz -= 5.0 * dt
        if particle.lifetime <= 0 or particle.z < 0:
            impact_sparks.remove(particle)

    for enemy in enemies:
        enemy.anim_time += dt
        enemy.flash_timer = max(0, enemy.flash_timer - dt)
        if not enemy.alive and enemy.death_timer > 0:
            enemy.death_timer = max(0, enemy.death_timer - dt)

    muzzle_flash_timer = max(0, muzzle_flash_timer - dt)
    hit_marker_timer = max(0, hit_marker_timer - dt)
    screen_shake_timer = max(0, screen_shake_timer - dt)
    damage_vignette_timer = max(0, damage_vignette_timer - dt)


# ------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ------------------------------------------------------------

def normalize_angle(angle):
    """Keep an angle between -PI and +PI."""
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    return angle


def cell_at(x, y):
    """Return the character stored at a map position."""
    mx = int(x)
    my = int(y)

    if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
        return "#"

    return LEVEL[my][mx]


def is_blocking(x, y):
    """Check whether a position contains something solid."""
    cell = cell_at(x, y)

    # Closed doors behave like walls.
    if cell == "#" or cell == "D":
        return True

    return False


def can_move_to(x, y):
    """Collision detection with a small player radius."""
    radius = 0.18

    checks = [
        (x - radius, y - radius),
        (x + radius, y - radius),
        (x - radius, y + radius),
        (x + radius, y + radius),
    ]

    for cx, cy in checks:
        if is_blocking(cx, cy):
            return False

    return True


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def has_line_of_sight(x1, y1, x2, y2):
    """Simple ray test used by enemies."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)

    if length == 0:
        return True

    steps = int(length * 12)

    for i in range(1, steps):
        t = i / steps
        x = x1 + dx * t
        y = y1 + dy * t

        if is_blocking(x, y):
            return False

    return True


# ------------------------------------------------------------
# 6. PLAYER MOVEMENT
# ------------------------------------------------------------

def update_player(dt):
    keys = pygame.key.get_pressed()

    forward_x = math.cos(player.angle)
    forward_y = math.sin(player.angle)
    right_x = -math.sin(player.angle)
    right_y = math.cos(player.angle)

    move_x = 0
    move_y = 0

    if keys[pygame.K_w]:
        move_x += forward_x
        move_y += forward_y
    if keys[pygame.K_s]:
        move_x -= forward_x
        move_y -= forward_y
    if keys[pygame.K_d]:
        move_x += right_x
        move_y += right_y
    if keys[pygame.K_a]:
        move_x -= right_x
        move_y -= right_y

    length = math.hypot(move_x, move_y)
    moving = length > 0

    if moving:
        move_x /= length
        move_y /= length
        new_x = player.x + move_x * MOVE_SPEED * dt
        new_y = player.y + move_y * MOVE_SPEED * dt
        if can_move_to(new_x, player.y):
            player.x = new_x
        if can_move_to(player.x, new_y):
            player.y = new_y
        player.bob_time += dt * WEAPON_BOB_SPEED
    else:
        player.bob_time += dt * 2.0

    if keys[pygame.K_LEFT]:
        player.angle -= TURN_SPEED * dt
    if keys[pygame.K_RIGHT]:
        player.angle += TURN_SPEED * dt

    mouse_x, _ = pygame.mouse.get_rel()
    player.angle += mouse_x * 0.0025
    player.angle = normalize_angle(player.angle)

    # Gravity and jump physics.
    if player.z > 0 or player.jump_velocity > 0:
        player.z += player.jump_velocity * dt
        player.jump_velocity -= GRAVITY * dt
        if player.z <= 0:
            player.z = 0
            player.jump_velocity = 0


# ------------------------------------------------------------
# 7. PICKUPS AND DOORS
# ------------------------------------------------------------

def update_interactions():
    # Look for the key.
    if not player.has_key:
        if distance(player.x, player.y, 1.5, 8.5) < 0.7:
            player.has_key = True
            print("You picked up the red key!")

    # The E key is handled as an event below.
    # This function is left here to keep game logic organized.


def all_enemies_dead():
    return all(not enemy.alive for enemy in enemies)


def use_action():
    """Open the red door only after getting the red key and killing every enemy."""
    for y in range(max(0, int(player.y) - 1), min(MAP_H, int(player.y) + 2)):
        for x in range(max(0, int(player.x) - 1), min(MAP_W, int(player.x) + 2)):
            cell = LEVEL[y][x]

            if cell == "D":
                d = distance(player.x, player.y, x + 0.5, y + 0.5)

                if d < 1.5:
                    if not player.has_key:
                        print("The RED DOOR is locked. Find the RED KEY.")
                    elif not all_enemies_dead():
                        print("The RED DOOR is locked. Kill every enemy first!")
                    else:
                        # Opening the red door immediately ends the level.
                        print("The RED DOOR opens...")
                        print("#1 victory royale")
                        return "win"
                    return

    return None


# ------------------------------------------------------------
# 8. SHOOTING
# ------------------------------------------------------------

def shoot():
    global muzzle_flash_timer, hit_marker_timer, screen_shake_timer

    if player.shoot_cooldown > 0 or player.ammo <= 0:
        return

    player.ammo -= 1
    player.shoot_cooldown = 0.35
    muzzle_flash_timer = 0.10
    screen_shake_timer = 0.08
    shell_particles.append(
        Particle(player.x, player.y, 0.8,
                 random.uniform(0.4, 1.0), random.uniform(-0.8, 0.8),
                 random.uniform(1.0, 2.0), 0.55, 0.05)
    )

    best_enemy = None
    best_score = 999

    for enemy in enemies:
        if not enemy.alive:
            continue

        dx = enemy.x - player.x
        dy = enemy.y - player.y
        enemy_angle = math.atan2(dy, dx)
        difference = abs(normalize_angle(enemy_angle - player.angle))
        enemy_distance = math.hypot(dx, dy)

        if difference < math.radians(5) and enemy_distance < 12:
            if has_line_of_sight(player.x, player.y, enemy.x, enemy.y):
                score = difference + enemy_distance * 0.002

                if score < best_score:
                    best_score = score
                    best_enemy = enemy

    if best_enemy:
        best_enemy.health -= 50
        best_enemy.flash_timer = 0.12
        hit_marker_timer = 0.18

        spawn_blood(best_enemy.x, best_enemy.y, 20)
        spawn_sparks(best_enemy.x, best_enemy.y, 10)

        if best_enemy.health <= 0:
            best_enemy.alive = False
            best_enemy.death_timer = 0.55
            spawn_blood(best_enemy.x, best_enemy.y, 55)
            spawn_sparks(best_enemy.x, best_enemy.y, 18)
            screen_shake_timer = 0.16


# ------------------------------------------------------------
# 9. ENEMY AI
# ------------------------------------------------------------

def update_enemies(dt):
    for enemy in enemies:
        if not enemy.alive:
            continue

        enemy.attack_timer -= dt

        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.hypot(dx, dy)

        # Enemies move toward the player if reasonably close.
        if dist < 8 and dist > 1.0:
            if has_line_of_sight(enemy.x, enemy.y, player.x, player.y):
                direction_x = dx / dist
                direction_y = dy / dist

                speed = 0.8

                new_x = enemy.x + direction_x * speed * dt
                new_y = enemy.y + direction_y * speed * dt

                if not is_blocking(new_x, enemy.y):
                    enemy.x = new_x

                if not is_blocking(enemy.x, new_y):
                    enemy.y = new_y

        # Attack when close enough.
        if dist < 1.2 and enemy.attack_timer <= 0:
            player.health -= 10
            player.hurt_flash = 0.15
            global damage_vignette_timer
            damage_vignette_timer = 0.30
            enemy.attack_timer = 1.0

            if player.health <= 0:
                player.health = 0


# ------------------------------------------------------------
# 10. RAYCASTING
# ------------------------------------------------------------

def cast_ray(angle):
    """
    Cast a ray into the 2-D map and return the distance to the
    first wall/door.

    This is the main trick that creates the 3-D effect.

    We use many tiny steps instead of a more advanced DDA
    algorithm because the simpler version is easier to learn.
    """
    step_size = 0.025

    x = player.x
    y = player.y

    for depth in range(int(MAX_DEPTH / step_size)):
        x += math.cos(angle) * step_size
        y += math.sin(angle) * step_size

        if is_blocking(x, y):
            return math.hypot(x - player.x, y - player.y)

    return MAX_DEPTH


def render_world():
    # Animated atmospheric sky and floor gradient.
    for y in range(VIEW_HEIGHT):
        if y < VIEW_HEIGHT // 2:
            depth = y / max(1, VIEW_HEIGHT // 2)
            c = int(22 + 18 * depth)
            pygame.draw.line(view, (c, c, c + 10), (0, y), (VIEW_WIDTH, y))
        else:
            depth = (y - VIEW_HEIGHT // 2) / max(1, VIEW_HEIGHT // 2)
            c = int(48 - 22 * depth)
            pygame.draw.line(view, (c + 8, c, max(18, c - 6)),
                             (0, y), (VIEW_WIDTH, y))

    wall_distances = []

    for column in range(VIEW_WIDTH):
        camera_x = column / VIEW_WIDTH
        ray_angle = player.angle - HALF_FOV + camera_x * FOV
        raw_distance = cast_ray(ray_angle)
        corrected_distance = raw_distance * math.cos(
            normalize_angle(ray_angle - player.angle)
        )
        corrected_distance = max(corrected_distance, 0.001)
        wall_distances.append(corrected_distance)

        wall_height = int(VIEW_HEIGHT / corrected_distance)
        jump_offset = int(player.z * 28)
        top = VIEW_HEIGHT // 2 - wall_height // 2 - jump_offset
        bottom = VIEW_HEIGHT // 2 + wall_height // 2 - jump_offset

        shade = max(28, int(225 - corrected_distance * 11))

        # Identify what the ray hit so the red door can be rendered red.
        hit_x = player.x + math.cos(ray_angle) * raw_distance
        hit_y = player.y + math.sin(ray_angle) * raw_distance
        hit_cell = cell_at(hit_x, hit_y)

        if hit_cell == "D":
            # Bright red metal door with darker distance shading.
            stripe = 1 if (column // 9) % 2 else 0
            wall_color = (
                min(255, int(shade * 1.05) + 18 * stripe),
                max(18, int(shade * 0.18)),
                max(18, int(shade * 0.12))
            )
        else:
            # Subtle animated industrial color variation.
            stripe = 1 if (column // 9) % 2 else 0
            wall_color = (
                min(255, shade + 10 * stripe),
                max(0, shade - 8),
                max(0, shade - 15)
            )

        pygame.draw.line(view, wall_color, (column, top), (column, bottom))

        # Small wall highlights give surfaces more visual structure.
        if column % 13 == 0 and corrected_distance < 12:
            pygame.draw.line(
                view,
                (min(255, shade + 25), min(255, shade + 18), min(255, shade + 12)),
                (column, top), (column, bottom), 1
            )

    return wall_distances


# ------------------------------------------------------------
# 11. RENDER ENEMIES
# ------------------------------------------------------------

def render_enemies(wall_distances):
    visible_enemies = []

    for enemy in enemies:
        if not enemy.alive and enemy.death_timer <= 0:
            continue

        dx = enemy.x - player.x
        dy = enemy.y - player.y
        enemy_distance = math.hypot(dx, dy)
        if enemy_distance < 0.1:
            continue

        angle_to_enemy = math.atan2(dy, dx)
        relative_angle = normalize_angle(angle_to_enemy - player.angle)

        if abs(relative_angle) < HALF_FOV + 0.2:
            visible_enemies.append((enemy_distance, enemy, relative_angle))

    visible_enemies.sort(reverse=True, key=lambda item: item[0])

    for enemy_distance, enemy, relative_angle in visible_enemies:
        screen_x = (
            VIEW_WIDTH / 2
            + math.tan(relative_angle)
            * (VIEW_WIDTH / 2)
            / math.tan(HALF_FOV)
        )

        base_height = 1.15 if enemy.kind == "brute" else 0.95
        anim = math.sin(enemy.anim_time * 6.0)
        sprite_height = max(8, int(VIEW_HEIGHT / enemy_distance * base_height))
        sprite_width = max(7, int(sprite_height * 0.58))
        jump_offset = int(player.z * 28)

        # Death animation: sink and rotate visually by shrinking.
        if not enemy.alive:
            death_ratio = enemy.death_timer / 0.55
            sprite_height = max(3, int(sprite_height * death_ratio))
            sprite_width = max(3, int(sprite_width * death_ratio))
            top = VIEW_HEIGHT // 2 - sprite_height + int((1 - death_ratio) * 12) - jump_offset
        else:
            bob = int(anim * max(1, sprite_height * 0.025))
            top = VIEW_HEIGHT // 2 - sprite_height // 2 + bob - jump_offset

        left = int(screen_x - sprite_width / 2)
        sample_x = max(0, min(VIEW_WIDTH - 1, int(screen_x)))

        if enemy_distance > wall_distances[sample_x]:
            continue

        # Shadow.
        pygame.draw.ellipse(
            view, (15, 10, 10),
            (left, VIEW_HEIGHT // 2 + sprite_height // 2 - 2,
             sprite_width, max(2, sprite_width // 4))
        )

        # Enemy colors/types.
        if enemy.kind == "brute":
            body = (92, 35, 25)
            head = (145, 90, 55)
            accent = (255, 80, 35)
        else:
            body = (135, 38, 28)
            head = (180, 112, 70)
            accent = (255, 205, 45)

        if enemy.flash_timer > 0:
            body = (255, 235, 210)
            head = (255, 255, 240)

        body_top = top + sprite_height // 4
        body_h = max(4, sprite_height * 3 // 4)

        pygame.draw.ellipse(
            view, body,
            (left, body_top, sprite_width, body_h)
        )

        # Shoulders/arms.
        arm_w = max(2, sprite_width // 4)
        pygame.draw.rect(view, body,
                         (left - arm_w // 2, body_top + body_h // 5, arm_w, body_h // 2))
        pygame.draw.rect(view, body,
                         (left + sprite_width - arm_w // 2, body_top + body_h // 5,
                          arm_w, body_h // 2))

        # Head.
        head_w = max(5, int(sprite_width * 0.62))
        head_h = max(5, int(sprite_height * 0.30))
        head_x = int(screen_x - head_w / 2)
        pygame.draw.ellipse(view, head,
                            (head_x, top, head_w, head_h))

        # Horns for brutes.
        if enemy.kind == "brute":
            pygame.draw.polygon(view, accent, [
                (head_x + 1, top + 3),
                (head_x - max(2, head_w // 5), top - max(3, head_h // 3)),
                (head_x + head_w // 4, top + 5)
            ])
            pygame.draw.polygon(view, accent, [
                (head_x + head_w - 1, top + 3),
                (head_x + head_w + max(2, head_w // 5), top - max(3, head_h // 3)),
                (head_x + head_w * 3 // 4, top + 5)
            ])

        # Eyes and mouth.
        eye_y = top + head_h // 3
        eye_w = max(2, head_w // 7)
        for ex in (head_x + head_w // 4, head_x + head_w * 3 // 5):
            pygame.draw.rect(view, accent, (ex, eye_y, eye_w, max(2, eye_w)))

        pygame.draw.line(
            view, (35, 10, 8),
            (head_x + head_w // 3, top + head_h * 2 // 3),
            (head_x + head_w * 2 // 3, top + head_h * 2 // 3),
            max(1, head_w // 12)
        )

        # Health bar when damaged.
        if enemy.health < enemy.max_health and enemy.alive:
            bar_w = sprite_width
            bar_y = max(0, top - 5)
            pygame.draw.rect(view, (25, 25, 25), (left, bar_y, bar_w, 3))
            fill = int(bar_w * max(0, enemy.health) / enemy.max_health)
            pygame.draw.rect(view, (210, 35, 30), (left, bar_y, fill, 3))


def render_particles():
    """Render blood and impact particles in the 3-D view."""
    particles = [(blood_particles, (190, 35, 35)),
                 (impact_sparks, (255, 210, 80))]

    for particle_list, base_color in particles:
        for particle in particle_list:
            dx = particle.x - player.x
            dy = particle.y - player.y
            distance = math.hypot(dx, dy)
            if distance < 0.05 or distance > MAX_DEPTH:
                continue

            rel = normalize_angle(math.atan2(dy, dx) - player.angle)
            if abs(rel) >= HALF_FOV:
                continue

            screen_x = VIEW_WIDTH / 2 + math.tan(rel) * (VIEW_WIDTH / 2) / math.tan(HALF_FOV)
            screen_y = (VIEW_HEIGHT / 2
                        - int((particle.z / distance) * VIEW_HEIGHT)
                        - int(player.z * 28))

            scale = max(1, int((particle.size * 90) / distance))
            alpha = max(0.15, particle.lifetime / particle.max_lifetime)
            color = tuple(max(0, min(255, int(c * alpha))) for c in base_color)

            pygame.draw.circle(view, color,
                               (int(screen_x), int(screen_y)), scale)


def render_shells():
    for particle in shell_particles:
        dx = particle.x - player.x
        dy = particle.y - player.y
        d = math.hypot(dx, dy)
        if d < 0.1:
            continue
        rel = normalize_angle(math.atan2(dy, dx) - player.angle)
        if abs(rel) >= HALF_FOV:
            continue
        sx = VIEW_WIDTH / 2 + math.tan(rel) * (VIEW_WIDTH / 2) / math.tan(HALF_FOV)
        sy = VIEW_HEIGHT // 2 - int(particle.z / d * VIEW_HEIGHT) - int(player.z * 28)
        size = max(1, int(3 / d))
        pygame.draw.rect(view, (205, 170, 55), (int(sx), int(sy), size + 1, size + 2))


# ------------------------------------------------------------
# 12. WEAPON / HUD
# ------------------------------------------------------------

def render_weapon():
    bob_x = int(math.sin(player.bob_time * 1.8) * 5)
    bob_y = int(abs(math.cos(player.bob_time * 1.8)) * 4)
    recoil = int(muzzle_flash_timer * 80)
    center_x = WIDTH // 2 + bob_x
    base_y = HEIGHT - 30 + bob_y + recoil

    if muzzle_flash_timer > 0:
        flash_size = 70 + int(muzzle_flash_timer * 220)
        pygame.draw.polygon(
            screen, (255, 205, 60),
            [
                (center_x, base_y - 145),
                (center_x - flash_size // 2, base_y - 35),
                (center_x + flash_size // 2, base_y - 35),
            ],
        )
        pygame.draw.circle(
            screen, (255, 245, 190),
            (center_x, base_y - 115),
            max(7, flash_size // 5)
        )

    # More detailed homemade sci-fi pistol.
    pygame.draw.polygon(
        screen, (28, 28, 32),
        [
            (center_x - 48, base_y),
            (center_x - 30, base_y - 105),
            (center_x + 25, base_y - 105),
            (center_x + 45, base_y),
        ]
    )
    pygame.draw.polygon(
        screen, (75, 75, 82),
        [
            (center_x - 17, base_y - 120),
            (center_x + 17, base_y - 120),
            (center_x + 25, base_y - 58),
            (center_x - 25, base_y - 58),
        ]
    )
    pygame.draw.rect(screen, (12, 12, 15),
                     (center_x - 10, base_y - 140, 20, 30))
    pygame.draw.rect(screen, (130, 130, 140),
                     (center_x - 7, base_y - 136, 14, 8))
    pygame.draw.line(screen, (150, 150, 160),
                     (center_x - 25, base_y - 80),
                     (center_x + 25, base_y - 80), 3)

    # Small animated weapon light.
    glow = int(100 + 80 * (0.5 + 0.5 * math.sin(game_time * 8)))
    pygame.draw.circle(screen, (glow, glow, 40),
                       (center_x, base_y - 65), 4)

    # Shell ejection is visual only.


def render_hud():
    # Bottom HUD bar.
    pygame.draw.rect(
        screen,
        (15, 15, 18),
        (0, HEIGHT - 70, WIDTH, 70)
    )

    health_text = font.render(
        f"HEALTH: {player.health}",
        True,
        (220, 220, 220)
    )

    ammo_text = font.render(
        f"AMMO: {player.ammo}",
        True,
        (220, 220, 220)
    )

    key_text = font.render(
        "RED KEY: YES" if player.has_key else "RED KEY: NO",
        True,
        (220, 220, 220)
    )

    screen.blit(health_text, (20, HEIGHT - 55))
    screen.blit(ammo_text, (220, HEIGHT - 55))
    screen.blit(key_text, (420, HEIGHT - 55))

    enemy_text = font.render(
        f"ENEMIES: {sum(1 for e in enemies if e.alive)}",
        True,
        (220, 220, 220)
    )
    screen.blit(enemy_text, (600, HEIGHT - 55))

    # ENEMY RADAR: shows arrows toward living enemies that are outside the
    # current view or hidden behind a wall, so every required target can be found.
    living = [e for e in enemies if e.alive]
    radar_font = pygame.font.Font(None, 22)
    for enemy in living:
        dx = enemy.x - player.x
        dy = enemy.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.01:
            continue
        rel = math.atan2(dy, dx) - player.angle
        rel = (rel + math.pi) % (2 * math.pi) - math.pi

        # Only show radar markers for enemies outside the central view.
        if abs(rel) > FOV * 0.42:
            side = -1 if rel < 0 else 1
            arrow_x = WIDTH // 2 + side * (WIDTH // 2 - 45)
            arrow_y = 45
            label = radar_font.render(
                "ENEMY", True, (255, 90, 90)
            )
            screen.blit(label, (arrow_x - label.get_width() // 2, arrow_y))
        elif dist > 7.0:
            # Distant enemies get a small top-center warning.
            label = radar_font.render(
                f"ENEMY {int(dist)}m", True, (255, 90, 90)
            )
            screen.blit(label, (WIDTH // 2 - label.get_width() // 2, 45))

    # Crosshair.
    cx = WIDTH // 2
    cy = HEIGHT // 2

    pygame.draw.line(screen, (230, 230, 230),
                     (cx - 7, cy), (cx + 7, cy), 1)

    pygame.draw.line(screen, (230, 230, 230),
                     (cx, cy - 7), (cx, cy + 7), 1)

    # Red X confirms that the shot connected with an enemy.
    if hit_marker_timer > 0:
        size = 12
        pygame.draw.line(
            screen, (255, 80, 80),
            (cx - size, cy - size),
            (cx + size, cy + size), 3
        )
        pygame.draw.line(
            screen, (255, 80, 80),
            (cx + size, cy - size),
            (cx - size, cy + size), 3
        )


def render_minimap():
    """A small top-down map useful while learning."""
    scale = 8
    offset_x = 10
    offset_y = 10

    for y in range(MAP_H):
        for x in range(MAP_W):
            cell = LEVEL[y][x]

            if cell == "D":
                color = (190, 25, 25)
            elif cell == "#":
                color = (100, 100, 100)
            else:
                color = (30, 30, 30)

            pygame.draw.rect(
                screen,
                color,
                (
                    offset_x + x * scale,
                    offset_y + y * scale,
                    scale - 1,
                    scale - 1
                )
            )

    # Player.
    pygame.draw.circle(
        screen,
        (0, 255, 0),
        (
            int(offset_x + player.x * scale),
            int(offset_y + player.y * scale)
        ),
        3
    )


# ------------------------------------------------------------
# 13. GAME OVER / WIN SCREEN
# ------------------------------------------------------------

def show_end_screen(title, message):
    screen.fill((10, 10, 10))

    title_surface = big_font.render(title, True, (220, 220, 220))
    message_surface = font.render(message, True, (200, 200, 200))

    screen.blit(
        title_surface,
        (
            WIDTH // 2 - title_surface.get_width() // 2,
            HEIGHT // 2 - 60
        )
    )

    screen.blit(
        message_surface,
        (
            WIDTH // 2 - message_surface.get_width() // 2,
            HEIGHT // 2 + 10
        )
    )

    pygame.display.flip()

    waiting = True

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_RETURN:
                    waiting = False


# ------------------------------------------------------------
# 14. MAIN GAME LOOP
# ------------------------------------------------------------

pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

running = True
won = False

while running:
    dt = clock.tick(60) / 1000.0
    dt = min(dt, 0.05)

    # ----------------------------
    # Events
    # ----------------------------

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shoot()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE and player.z <= 0.001:
                player.jump_velocity = JUMP_STRENGTH

            elif event.key == pygame.K_e:
                result = use_action()

                if result == "win":
                    won = True
                    running = False

    # ----------------------------
    # Updates
    # ----------------------------

    if player.health <= 0:
        running = False
        continue

    update_player(dt)
    update_enemies(dt)
    update_interactions()
    update_particles(dt)

    player.shoot_cooldown = max(
        0,
        player.shoot_cooldown - dt
    )

    player.hurt_flash = max(
        0,
        player.hurt_flash - dt
    )

    # ----------------------------
    # Rendering
    # ----------------------------

    wall_distances = render_world()
    render_enemies(wall_distances)
    render_particles()
    render_shells()

    # Scale the low-resolution 3-D view to the actual window.
    scaled_view = pygame.transform.scale(
        view,
        (WIDTH, HEIGHT)
    )

    if screen_shake_timer > 0:
        shake_x = random.randint(-3, 3)
        shake_y = random.randint(-2, 2)
    else:
        shake_x = 0
        shake_y = 0

    screen.blit(scaled_view, (shake_x, shake_y))

    render_weapon()
    render_hud()

    # Minimap can be toggled off by commenting out this line.
    render_minimap()

    # Instructions.
    instructions = font.render(
        "WASD Move | Mouse/Arrows Turn | SPACE Jump | LMB Shoot | E Use",
        True,
        (220, 220, 220)
    )

    screen.blit(
        instructions,
        (WIDTH // 2 - instructions.get_width() // 2, 5)
    )

    # Damage flash + subtle red vignette.
    if player.hurt_flash > 0:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((255, 0, 0, 80))
        screen.blit(flash, (0, 0))

    if damage_vignette_timer > 0:
        edge = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(edge, (180, 0, 0, 45), (0, 0, WIDTH, HEIGHT), 18)
        screen.blit(edge, (0, 0))

    pygame.display.flip()

# ------------------------------------------------------------
# 15. ENDING
# ------------------------------------------------------------

pygame.mouse.set_visible(True)
pygame.event.set_grab(False)

if won:
    show_end_screen(
        "LEVEL COMPLETE!",
        "You found the key and escaped. Press ENTER to quit."
    )
else:
    show_end_screen(
        "YOU DIED",
        "Press ENTER to quit."
    )

pygame.quit()
sys.exit()
