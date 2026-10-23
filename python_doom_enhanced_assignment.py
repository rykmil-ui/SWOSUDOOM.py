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
    SPACE       Shoot
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

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python DOOM-Style FPS - One Level")

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
# D = closed door
# K = key
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

player = Player()

# ------------------------------------------------------------
# 4. ENEMIES
# ------------------------------------------------------------

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100
        self.attack_timer = 0.0
        self.alive = True

enemies = [
    Enemy(10.5, 3.5),
    Enemy(12.5, 6.5),
    Enemy(5.5, 9.5),
]

# ------------------------------------------------------------
# VISUAL EFFECTS
# ------------------------------------------------------------

blood_particles = []
muzzle_flash_timer = 0.0
hit_marker_timer = 0.0
screen_shake_timer = 0.0


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


def update_particles(dt):
    global muzzle_flash_timer, hit_marker_timer, screen_shake_timer

    for particle in blood_particles[:]:
        particle.lifetime -= dt
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
        particle.z += particle.vz * dt
        particle.vz -= 3.5 * dt

        if particle.lifetime <= 0 or particle.z < 0:
            blood_particles.remove(particle)

    muzzle_flash_timer = max(0, muzzle_flash_timer - dt)
    hit_marker_timer = max(0, hit_marker_timer - dt)
    screen_shake_timer = max(0, screen_shake_timer - dt)


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

    # Forward/backward direction.
    forward_x = math.cos(player.angle)
    forward_y = math.sin(player.angle)

    # Right/left direction is perpendicular to forward.
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

    # Normalize diagonal movement so W+D isn't faster than W.
    length = math.hypot(move_x, move_y)

    if length > 0:
        move_x /= length
        move_y /= length

        new_x = player.x + move_x * MOVE_SPEED * dt
        new_y = player.y + move_y * MOVE_SPEED * dt

        # Check X and Y separately so the player can slide along walls.
        if can_move_to(new_x, player.y):
            player.x = new_x

        if can_move_to(player.x, new_y):
            player.y = new_y

    # Keyboard turning.
    if keys[pygame.K_LEFT]:
        player.angle -= TURN_SPEED * dt

    if keys[pygame.K_RIGHT]:
        player.angle += TURN_SPEED * dt

    # Mouse turning.
    mouse_x, _ = pygame.mouse.get_rel()
    player.angle += mouse_x * 0.0025

    player.angle = normalize_angle(player.angle)


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


def use_action():
    """Open a nearby door or activate the exit."""
    # Check cells in a small radius around the player.
    for y in range(max(0, int(player.y) - 1), min(MAP_H, int(player.y) + 2)):
        for x in range(max(0, int(player.x) - 1), min(MAP_W, int(player.x) + 2)):
            cell = LEVEL[y][x]

            if cell == "D":
                d = distance(player.x, player.y, x + 0.5, y + 0.5)

                if d < 1.5:
                    if player.has_key:
                        # Replace the door with floor.
                        row = list(LEVEL[y])
                        row[x] = "."
                        LEVEL[y] = "".join(row)
                        print("Door opened!")
                    else:
                        print("The door is locked. Find the key.")
                    return

    # Exit is near the upper-right side of the map.
    # We use a small invisible exit trigger at this location.
    if player.has_key and distance(player.x, player.y, 14.0, 10.0) < 1.2:
        return "win"

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
        hit_marker_timer = 0.18

        # Blood spray on every successful hit.
        spawn_blood(best_enemy.x, best_enemy.y, 14)

        if best_enemy.health <= 0:
            best_enemy.alive = False

            # Larger blood burst when the enemy dies.
            spawn_blood(best_enemy.x, best_enemy.y, 32)


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
    # Sky.
    view.fill((35, 35, 45))

    # Floor.
    pygame.draw.rect(
        view,
        (55, 45, 35),
        (0, VIEW_HEIGHT // 2, VIEW_WIDTH, VIEW_HEIGHT // 2)
    )

    wall_distances = []

    for column in range(VIEW_WIDTH):
        # Convert screen X into an angle across the FOV.
        camera_x = column / VIEW_WIDTH
        ray_angle = player.angle - HALF_FOV + camera_x * FOV

        raw_distance = cast_ray(ray_angle)

        # Fish-eye correction.
        corrected_distance = raw_distance * math.cos(
            normalize_angle(ray_angle - player.angle)
        )

        corrected_distance = max(corrected_distance, 0.001)

        wall_distances.append(corrected_distance)

        # Calculate projected wall height.
        wall_height = int(VIEW_HEIGHT / corrected_distance)

        top = VIEW_HEIGHT // 2 - wall_height // 2
        bottom = VIEW_HEIGHT // 2 + wall_height // 2

        # Simple distance shading.
        shade = max(25, int(210 - corrected_distance * 12))

        wall_color = (shade, shade, shade)

        pygame.draw.line(
            view,
            wall_color,
            (column, top),
            (column, bottom)
        )

    return wall_distances


# ------------------------------------------------------------
# 11. RENDER ENEMIES
# ------------------------------------------------------------

def render_enemies(wall_distances):
    # Draw far-away enemies first.
    visible_enemies = []

    for enemy in enemies:
        if not enemy.alive:
            continue

        dx = enemy.x - player.x
        dy = enemy.y - player.y

        enemy_distance = math.hypot(dx, dy)
        angle_to_enemy = math.atan2(dy, dx)
        relative_angle = normalize_angle(angle_to_enemy - player.angle)

        # Only draw enemies inside the player's FOV.
        if abs(relative_angle) < HALF_FOV + 0.2:
            visible_enemies.append(
                (enemy_distance, enemy, relative_angle)
            )

    visible_enemies.sort(reverse=True, key=lambda item: item[0])

    for enemy_distance, enemy, relative_angle in visible_enemies:
        screen_x = (
            VIEW_WIDTH / 2
            + math.tan(relative_angle)
            * (VIEW_WIDTH / 2)
            / math.tan(HALF_FOV)
        )

        sprite_height = int(VIEW_HEIGHT / enemy_distance * 0.75)
        sprite_width = max(5, sprite_height // 2)

        top = VIEW_HEIGHT // 2 - sprite_height // 2
        left = int(screen_x - sprite_width / 2)

        # Don't draw an enemy if a wall is closer at its screen column.
        sample_x = max(0, min(VIEW_WIDTH - 1, int(screen_x)))

        if enemy_distance > wall_distances[sample_x]:
            continue

        # Body.
        pygame.draw.rect(
            view,
            (130, 45, 35),
            (left, top + sprite_height // 4,
             sprite_width, sprite_height * 3 // 4)
        )

        # Head.
        head_size = max(4, sprite_width // 2)
        pygame.draw.rect(
            view,
            (185, 130, 85),
            (int(screen_x - head_size / 2),
             top,
             head_size,
             head_size)
        )

        # Eyes.
        eye_size = max(1, head_size // 6)

        pygame.draw.rect(
            view,
            (255, 220, 40),
            (int(screen_x - head_size * 0.28),
             top + head_size // 3,
             eye_size,
             eye_size)
        )

        pygame.draw.rect(
            view,
            (255, 220, 40),
            (int(screen_x + head_size * 0.12),
             top + head_size // 3,
             eye_size,
             eye_size)
        )


def render_particles():
    """Project blood particles into the first-person view."""
    for particle in blood_particles:
        dx = particle.x - player.x
        dy = particle.y - player.y
        particle_distance = math.hypot(dx, dy)

        if particle_distance < 0.1:
            continue

        angle_to_particle = math.atan2(dy, dx)
        relative_angle = normalize_angle(angle_to_particle - player.angle)

        if abs(relative_angle) >= HALF_FOV:
            continue

        screen_x = (
            VIEW_WIDTH / 2
            + math.tan(relative_angle)
            * (VIEW_WIDTH / 2)
            / math.tan(HALF_FOV)
        )

        size = max(
            1,
            int(VIEW_HEIGHT / particle_distance * particle.size * 3)
        )

        screen_y = VIEW_HEIGHT // 2 - int(
            particle.z / max(particle_distance, 0.1) * VIEW_HEIGHT
        )

        fade = particle.lifetime / particle.max_lifetime
        color = (
            int(150 + 80 * fade),
            int(20 * fade),
            int(15 * fade),
        )

        pygame.draw.circle(
            view,
            color,
            (int(screen_x), int(screen_y)),
            size
        )


# ------------------------------------------------------------
# 12. WEAPON / HUD
# ------------------------------------------------------------

def render_weapon():
    # Bright muzzle flash appears briefly after every shot.
    if muzzle_flash_timer > 0:
        flash_size = 55 + int(muzzle_flash_timer * 180)

        pygame.draw.polygon(
            screen,
            (255, 220, 80),
            [
                (WIDTH // 2, HEIGHT - 150),
                (WIDTH // 2 - flash_size // 2, HEIGHT - 35),
                (WIDTH // 2 + flash_size // 2, HEIGHT - 35),
            ],
        )

        pygame.draw.circle(
            screen,
            (255, 245, 180),
            (WIDTH // 2, HEIGHT - 115),
            max(5, flash_size // 5),
        )

    # Very simple homemade pistol silhouette.
    center_x = WIDTH // 2
    base_y = HEIGHT - 30

    pygame.draw.polygon(
        screen,
        (45, 45, 45),
        [
            (center_x - 35, base_y),
            (center_x - 18, base_y - 90),
            (center_x + 18, base_y - 90),
            (center_x + 35, base_y),
        ]
    )

    pygame.draw.rect(
        screen,
        (80, 80, 80),
        (center_x - 12, base_y - 105, 24, 65)
    )

    # Muzzle.
    pygame.draw.rect(
        screen,
        (15, 15, 15),
        (center_x - 8, base_y - 120, 16, 20)
    )


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
        "KEY: YES" if player.has_key else "KEY: NO",
        True,
        (220, 220, 220)
    )

    screen.blit(health_text, (20, HEIGHT - 55))
    screen.blit(ammo_text, (220, HEIGHT - 55))
    screen.blit(key_text, (420, HEIGHT - 55))

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

            if cell in "#D":
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

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                shoot()

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
        "WASD Move | Mouse/Arrows Turn | SPACE Shoot | E Use",
        True,
        (220, 220, 220)
    )

    screen.blit(
        instructions,
        (WIDTH // 2 - instructions.get_width() // 2, 5)
    )

    # Red flash when damaged.
    if player.hurt_flash > 0:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((255, 0, 0, 70))
        screen.blit(flash, (0, 0))

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
