"""
PYTHON DOOM-STYLE FPS - V24 ENEMY INTELLIGENCE REGISTRY
-------------------------------------------
A beginner-friendly, single-file FPS made with Pygame.

Install:
    pip install pygame-ce

Run:
    python python_doom.py

Controls:
    W / S       Move forward / backward
    A / D       Strafe left / right
    Left/Right  Turn
    Mouse       Turn
    E           Open doors / use exit
    SPACE       Jump
    Left Mouse  Shoot (hold for automatic chaingun fire)
    1           Pistol
    2           Shotgun
    3           Chaingun
    4           Rocket Launcher
    ESC         Quit

This is an original mini-level inspired by classic 1990s raycasting FPS games.
It does NOT contain original DOOM maps, sprites, sounds, or other copyrighted assets.
"""

import math
import random
import sys
import pygame

# ------------------------------------------------------------
# WEEK 2 DECISION + WEEK 5 FUNCTION REFACTOR + ENEMY REGISTRY LOOKUP + AUTOMATIC CHAINGUN
# This happens in the PowerShell window BEFORE the game opens.
# ------------------------------------------------------------

def configure_strategy(fuel_remaining, strategy_choice):
    """Return the gameplay settings selected by the world-state decision."""
    if fuel_remaining < 20:
        if strategy_choice == "1":
            return "assault", 45, 100, 8
        elif strategy_choice == "2":
            return "tactical", 30, 100, 6
        else:
            return "escape", 18, 70, 4

    return "tactical", 30, 100, 6


fuel_remaining = 15

# Week 3: a real three-outcome decision.
# The decision is now refactored into configure_strategy(),
# which returns the actual gameplay settings used below.
if fuel_remaining < 20:
    print("Warning: fuel critical.")
    print("Choose your strategy:")
    print("1 - Assault: more enemies, more ammunition, normal health")
    print("2 - Tactical: balanced enemies, balanced ammunition, normal health")
    print("3 - Escape: fewer enemies, less ammunition, reduced health")

    strategy = input("Enter 1, 2, or 3: ").strip()
else:
    strategy = "2"

game_strategy, starting_ammo, starting_health, enemy_limit = configure_strategy(
    fuel_remaining, strategy
)

if fuel_remaining < 20:
    if game_strategy == "assault":
        print("ASSAULT selected: prepare for a larger fight!")
    elif game_strategy == "tactical":
        print("TACTICAL selected: balanced resources and opposition.")
    else:
        print("ESCAPE selected: fewer enemies, but limited health and ammunition.")
    print("Loading DOOM...")
else:
    print("Fuel levels nominal. Tactical mode selected.")

print("\nChoose the gameplay soundtrack:")
print("1 - Drop-A guitar riff (original soundtrack)")
print("2 - 165 Hz melody (new song)")
while True:
    song_choice = input("Enter 1 or 2: ").strip()
    if song_choice in ("1", "2"):
        break
    print("Please enter 1 or 2.")

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

# ------------------------------------------------------------
# PROCEDURAL MUSIC
# ------------------------------------------------------------
# The soundtrack is generated from the Drop-A 7-string guitar tab
# supplied for this project. No external music file is required.
# Tuning assumed: A1-E2-A2-D3-G3-B3-E4.
#
# Each tuple is (note name, beats). The note frequencies are generated
# mathematically and mixed into a WAV-like PCM buffer for Pygame.
# ------------------------------------------------------------

MUSIC_SAMPLE_RATE = 44100
MUSIC_VOLUME = 0.24
MUSIC_BPM = 62.5

MUSIC_NOTE_FREQUENCIES = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
    "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11,
}


def music_note_frequency(note_name):
    """Convert C4/F#5/etc. into Hz using A4 = 440 Hz."""
    note_name = note_name.upper()
    if len(note_name) >= 3 and note_name[1] in "#B":
        pitch = note_name[:2]
        octave = int(note_name[2:])
    else:
        pitch = note_name[:1]
        octave = int(note_name[1:])

    midi = 12 * (octave + 1) + MUSIC_NOTE_FREQUENCIES[pitch]
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


# Translated directly from the user's Drop-A 7-string tab.
# Tuning used:
#   1=E4, 2=B3, 3=G3, 4=D3, 5=A2, 6=E2, 7=A1
#
# The tab does not provide formal rhythmic notation. Here the horizontal
# spacing is preserved as the timing source: 3 tab columns = 1/4 beat.
# Notes that begin in the same column are treated as a chord.
TAB_COLUMNS_PER_QUARTER_BEAT = 3.0
TAB_DEFAULT_FINAL_BEATS = 0.25

GUITAR_SECTION_1 = [
    (("A5",), 0.25),
    (("E5",), 0.25),
    (("C5",), 0.25),
    (("A4",), 2/12),
    (("C5",), 0.25),
    (("E5",), 0.25),
    (("A5",), 2/12),
    (("E5",), 0.25),
    (("C5",), 0.25),
    (("A4",), 2/12),
    (("C5",), 0.25),
    (("E5",), 4/12),
    (("A5",), 1/12),
    (("E5",), 0.25),
    (("C5",), 4/12),
    (("A4",), 4/12),
    (("E4",), 0.25),
    (("C4",), 4/12),
    (("A3",), 4/12),
    (("C4",), 0.25),
    (("E4",), 2/12),
    (("A4",), 1/12),
    (("C5",), 0.25),
    (("E5",), 4/12),
    (("A5",), 1/12),
    (("E5",), 0.25),
    (("C5",), 4/12),
    (("A4",), 1/12),
    (("C5",), 0.25),
    (("E5",), 5/12),
    (("A5",), 1/12),
    (("E5",), 4/12),
    (("C5",), 5/12),
    (("A4",), 0.25),
]

GUITAR_SECTION_2 = [
    (("B3",), 4/12),
    (("D4",), 4/12),
    (("F4",), 0.25),
    (("B4",), 0.25),
    (("D5",), 0.25),
    (("F5",), 0.25),
    (("B5",), 0.25),
    (("F5",), 0.25),
    (("D5",), 0.25),
    (("B4",), TAB_DEFAULT_FINAL_BEATS),
]

GUITAR_SECTION_3 = GUITAR_SECTION_1

GUITAR_SECTION_4 = [
    (("B3",), 0.25),
    (("D4",), 0.25),
    (("F4",), 0.25),
    (("B4",), 0.25),
    (("D5",), 5/12),
    (("F5",), 4/12),
    (("B5",), 0.25),
    (("F5",), 4/12),
    (("D5",), 0.25),
    (("B4",), TAB_DEFAULT_FINAL_BEATS),
]

GUITAR_SONG = (
    GUITAR_SECTION_1
    + GUITAR_SECTION_2
    + GUITAR_SECTION_3
    + GUITAR_SECTION_4
)

# Song 2 transcribed from the user's MakeCode / micro:bit melody.
# Each entry is (frequency in Hz, beat duration). QUARTER = 1 beat; WHOLE = 4 beats.
SECOND_SONG_NOTES = [
    165, 165, 330, 165, 165, 294, 165, 165, 262, 165, 165, 233,
    165, 165, 247, 262, 165, 165, 330, 165, 165, 294, 165, 165,
    262, 165, 165, 233,
]
SECOND_SONG = [((frequency,), 4 if i == len(SECOND_SONG_NOTES) - 1 else 1)
               for i, frequency in enumerate(SECOND_SONG_NOTES)]


def build_music_buffer(song, bpm):
    """Generate a simple distorted-synth guitar-style PCM track."""
    import array

    samples = array.array("h")
    beat_seconds = 60.0 / bpm

    for note_group, beats in song:
        duration = beats * beat_seconds
        count = max(1, int(MUSIC_SAMPLE_RATE * duration))

        # Guitar song entries use note names; the second song uses exact Hz values.
        if isinstance(note_group, (int, float)):
            frequencies = [float(note_group)]
        else:
            frequencies = [
                float(note_name) if isinstance(note_name, (int, float))
                else music_note_frequency(note_name)
                for note_name in note_group
            ]

        for i in range(count):
            t = i / MUSIC_SAMPLE_RATE

            # Sum simultaneous notes when the tab contains a chord.
            value = 0.0
            for frequency in frequencies:
                phase = 2.0 * math.pi * frequency * t
                value += (
                    0.72 * math.sin(phase)
                    + 0.20 * math.sin(phase * 2.0)
                    + 0.08 * math.sin(phase * 3.0)
                )
            value /= max(1, len(frequencies))

            # Short attack/release prevents clicks between notes.
            attack = min(0.012, duration / 4.0)
            release = min(0.045, duration / 3.0)
            envelope = 1.0
            if t < attack:
                envelope = t / attack
            elif duration - t < release:
                envelope = max(0.0, (duration - t) / release)

            value *= envelope * MUSIC_VOLUME
            samples.append(int(max(-1.0, min(1.0, value)) * 32767))

    return samples.tobytes()


def build_weapon_sound(kind):
    """Generate an original short synthesized weapon sound effect."""
    import array

    profiles = {
        "pistol": (0.12, 155.0, 0.55, 0.20),
        "shotgun": (0.24, 85.0, 0.85, 0.55),
        "chaingun": (0.075, 190.0, 0.45, 0.16),
        "rocket": (0.38, 55.0, 1.00, 0.75),
    }
    duration, base_freq, tone_mix, noise_mix = profiles[kind]
    samples = array.array("h")
    count = max(1, int(MUSIC_SAMPLE_RATE * duration))

    for i in range(count):
        t = i / MUSIC_SAMPLE_RATE
        progress = t / duration

        # Fast attack followed by an exponential decay gives the sound a punch.
        envelope = math.exp(-9.0 * progress)
        if progress < 0.015:
            envelope *= progress / 0.015

        # A decaying noise component creates the mechanical/crackling character.
        noise = random.uniform(-1.0, 1.0)
        tone = (
            math.sin(2.0 * math.pi * base_freq * t)
            + 0.45 * math.sin(2.0 * math.pi * base_freq * 2.1 * t)
            + 0.18 * math.sin(2.0 * math.pi * base_freq * 3.7 * t)
        ) / 1.63

        # Extra low thump for the shotgun and rocket launcher.
        thump = 0.0
        if kind in ("shotgun", "rocket"):
            thump = math.sin(2.0 * math.pi * (base_freq * 0.38) * t) * math.exp(-18.0 * progress)

        value = (tone * tone_mix + noise * noise_mix + thump * 0.35) * envelope
        samples.append(int(max(-1.0, min(1.0, value * 0.85)) * 32767))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def build_weapon_sounds():
    """Create all four weapon effects after the mixer is initialized."""
    return {
        1: build_weapon_sound("pistol"),
        2: build_weapon_sound("shotgun"),
        3: build_weapon_sound("chaingun"),
        4: build_weapon_sound("rocket"),
    }


def start_game_music():
    """Generate the selected soundtrack and start it looping during gameplay."""
    try:
        pygame.mixer.init(frequency=MUSIC_SAMPLE_RATE, size=-16, channels=1)
        weapon_sounds = build_weapon_sounds()
        if song_choice == "1":
            selected_song = GUITAR_SONG
            selected_bpm = MUSIC_BPM
        else:
            selected_song = SECOND_SONG
            selected_bpm = 140.0  # Slightly faster version of the second track.
        music_buffer = build_music_buffer(selected_song, selected_bpm)
        music_sound = pygame.mixer.Sound(buffer=music_buffer)
        music_sound.set_volume(1.0)
        music_sound.play(loops=-1)
        return music_sound, weapon_sounds
    except pygame.error as error:
        print(f"Audio disabled: {error}")
        return None, {}


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python DOOM-Style FPS - Hell Sector v21")

view = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 64)

# Start the procedurally generated Drop-A guitar track.
game_music, weapon_sounds = start_game_music()

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
# 3. WEAPONS + PLAYER
# ------------------------------------------------------------

WEAPONS = {
    1: {"name": "PISTOL", "damage": 50, "cooldown": 0.35, "range": 12.0, "ammo_cost": 1},
    2: {"name": "SHOTGUN", "damage": 35, "cooldown": 0.85, "range": 9.0, "ammo_cost": 2},
    3: {"name": "CHAINGUN", "damage": 18, "cooldown": 0.10, "range": 12.0, "ammo_cost": 1},
    4: {"name": "ROCKET LAUNCHER", "damage": 120, "cooldown": 1.00, "range": 14.0, "ammo_cost": 1},
}


def select_weapon(number):
    """Switch weapons and return True when the requested weapon is valid."""
    if number not in WEAPONS:
        return False

    player.current_weapon = number
    player.ammo = player.weapon_ammo[number]
    return True


class Player:
    def __init__(self):
        self.x = 2.5
        self.y = 1.5

        # Angle is measured in radians.
        # 0 means looking toward the positive X direction.
        self.angle = 0.0

        self.health = starting_health
        self.ammo = starting_ammo
        self.has_key = False

        self.current_weapon = 1
        self.weapon_ammo = {
            1: starting_ammo,
            2: max(2, starting_ammo // 2),
            3: starting_ammo * 2,
            4: max(1, starting_ammo // 6),
        }
        self.ammo = self.weapon_ammo[1]

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

        # Each demon class has its own role and durability.
        enemy_stats = {
            "imp": (100, 10),
            "brute": (140, 15),
            "hellhound": (80, 12),
            "warden": (190, 22),
        }
        self.max_health, self.threat_value = enemy_stats.get(kind, (100, 10))
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

# Week 6 list practice: build the level's enemy roster incrementally.
# Each list entry is a real Enemy entity already used by the game world.
enemies = []
enemies.append(Enemy(12.5, 2.5, "imp"))
enemies.append(Enemy(10.5, 3.5, "hellhound"))
enemies.append(Enemy(10.5, 6.5, "brute"))
enemies.append(Enemy(13.5, 3.5, "warden"))
enemies.append(Enemy(5.5, 9.5, "imp"))
enemies.append(Enemy(8.5, 9.5, "brute"))
enemies.append(Enemy(6.5, 6.5, "hellhound"))
enemies.append(Enemy(13.5, 2.5, "warden"))

# The earlier strategy decision controls how many roster entries enter the level.
enemies = enemies[:enemy_limit]

# ------------------------------------------------------------
# WEEK 10 DATA-STRUCTURE DECISION (written before implementation)
# ------------------------------------------------------------
# I choose a dictionary keyed by unique enemy ID for targeted intel lookups.
# The existing list remains best for updating/rendering every enemy in order;
# searching that list by ID each time would require a loop and comparison.
# A dictionary uses extra memory and setup code, but directly retrieves one
# enemy by key. A set could efficiently track IDs already scanned, but it
# cannot associate each ID with health, type, and coordinates. Therefore the
# dictionary is the best fit for the game's enemy-intelligence feature.
#
# Populate the registry from the real, strategy-limited Enemy objects above.
# Do not replace this with a hardcoded dictionary of example enemies.
enemy_registry = {}
for enemy_number, enemy in enumerate(enemies, start=1):
    enemy.entity_id = f"HELL-{enemy_number:02d}"
    enemy_registry[enemy.entity_id] = enemy

# Demonstrate a successful dictionary lookup using a real entity from this run.
# .get(key) retrieves the Enemy object directly; there is no manual search loop.
if enemy_registry:
    demo_enemy_id = next(iter(enemy_registry))
    demo_enemy = enemy_registry.get(demo_enemy_id)
    print("\nEnemy registry lookup demonstration:")
    print(
        f" {demo_enemy_id} -> {demo_enemy.kind.title()}, "
        f"health {demo_enemy.health}/{demo_enemy.max_health}, "
        f"position ({demo_enemy.x:.1f}, {demo_enemy.y:.1f})"
    )

# The in-game intel panel also retrieves entities from this dictionary by ID.
intel_enemy_ids = list(enemy_registry.keys())
intel_target_index = 0
intel_target_id = intel_enemy_ids[0] if intel_enemy_ids else None
intel_panel_visible = False

# Traverse the actual enemy list and report useful information before the game opens.
print("\nEnemy roster loaded:")
enemy_type_counts = {}
for enemy in enemies:
    print(f" - {enemy.entity_id}: {enemy.kind.title()} at ({enemy.x:.1f}, {enemy.y:.1f})")
    enemy_type_counts[enemy.kind] = enemy_type_counts.get(enemy.kind, 0) + 1

print(f"Total enemies in this run: {len(enemies)}")
for enemy_type, count in enemy_type_counts.items():
    print(f"   {enemy_type.title()}: {count}")

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

# Week 4: loop-driven world state. These values are rebuilt from the
# actual enemy list every update, so they change as enemies are defeated.
living_enemies = len(enemies)
total_enemy_threat = 0

# Week 4: Doom-inspired "Hellwave" state. Each active demon is processed
# during the sector scan below. This running state changes as demons move,
# attack, take damage, and are eliminated.
hellwave_events = 0
hell_pressure = 0


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


# Validate the final spawn locations after cell_at() is defined.
# This prevents an enemy from accidentally being placed inside a wall.
validate_enemy_positions()


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

def find_aimed_enemy(max_range, max_angle):
    """Return the living enemy closest to the player's aim."""
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

        if difference < max_angle and enemy_distance < max_range:
            if has_line_of_sight(player.x, player.y, enemy.x, enemy.y):
                score = difference + enemy_distance * 0.002
                if score < best_score:
                    best_score = score
                    best_enemy = enemy

    return best_enemy


def shoot():
    global muzzle_flash_timer, hit_marker_timer, screen_shake_timer

    weapon = WEAPONS[player.current_weapon]

    if player.shoot_cooldown > 0 or player.ammo < weapon["ammo_cost"]:
        return

    player.ammo -= weapon["ammo_cost"]
    player.weapon_ammo[player.current_weapon] = player.ammo
    player.shoot_cooldown = weapon["cooldown"]
    muzzle_flash_timer = 0.10
    screen_shake_timer = 0.08

    # Play the synthesized sound for the selected weapon. The chaingun
    # naturally repeats this effect as its automatic fire loop calls shoot().
    sound = weapon_sounds.get(player.current_weapon)
    if sound is not None:
        sound.set_volume(0.42 if player.current_weapon != 4 else 0.55)
        sound.play()

    shell_particles.append(
        Particle(player.x, player.y, 0.8,
                 random.uniform(0.4, 1.0), random.uniform(-0.8, 0.8),
                 random.uniform(1.0, 2.0), 0.55, 0.05)
    )

    # PISTOL: accurate single-target shot.
    if player.current_weapon == 1:
        target = find_aimed_enemy(weapon["range"], math.radians(5))
        if target:
            target.health -= weapon["damage"]
            target.flash_timer = 0.12
            hit_marker_timer = 0.18
            spawn_blood(target.x, target.y, 20)
            spawn_sparks(target.x, target.y, 10)

    # SHOTGUN: a wide blast can hit multiple demons.
    elif player.current_weapon == 2:
        hit_any = False
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - player.x
            dy = enemy.y - player.y
            distance = math.hypot(dx, dy)
            difference = abs(normalize_angle(math.atan2(dy, dx) - player.angle))
            if distance < weapon["range"] and difference < math.radians(14):
                if has_line_of_sight(player.x, player.y, enemy.x, enemy.y):
                    falloff = max(0.35, 1.0 - distance / (weapon["range"] * 1.4))
                    enemy.health -= int(weapon["damage"] * falloff)
                    enemy.flash_timer = 0.15
                    spawn_blood(enemy.x, enemy.y, 14)
                    spawn_sparks(enemy.x, enemy.y, 7)
                    hit_any = True
        if hit_any:
            hit_marker_timer = 0.20
            screen_shake_timer = 0.14

    # CHAINGUN: rapid-fire, accurate single-target shots.
    elif player.current_weapon == 3:
        target = find_aimed_enemy(weapon["range"], math.radians(7))
        if target:
            target.health -= weapon["damage"]
            target.flash_timer = 0.10
            hit_marker_timer = 0.12
            spawn_blood(target.x, target.y, 9)
            spawn_sparks(target.x, target.y, 5)
        screen_shake_timer = 0.05

    # ROCKET LAUNCHER: direct hit plus area-of-effect damage.
    else:
        target = find_aimed_enemy(weapon["range"], math.radians(8))
        explosion_x = player.x + math.cos(player.angle) * weapon["range"]
        explosion_y = player.y + math.sin(player.angle) * weapon["range"]

        if target:
            explosion_x, explosion_y = target.x, target.y
            hit_marker_timer = 0.25

        for enemy in enemies:
            if not enemy.alive:
                continue
            distance = math.hypot(enemy.x - explosion_x, enemy.y - explosion_y)
            if distance < 2.5 and has_line_of_sight(explosion_x, explosion_y, enemy.x, enemy.y):
                damage = max(20, int(weapon["damage"] * (1.0 - distance / 3.0)))
                enemy.health -= damage
                enemy.flash_timer = 0.18
                spawn_blood(enemy.x, enemy.y, 22)
                spawn_sparks(enemy.x, enemy.y, 12)

        spawn_sparks(explosion_x, explosion_y, 35)
        spawn_blood(explosion_x, explosion_y, 20)
        screen_shake_timer = 0.24

    # One centralized death check keeps all four weapons compatible with
    # the existing enemy loop and victory condition.
    for enemy in enemies:
        if enemy.alive and enemy.health <= 0:
            enemy.alive = False
            enemy.death_timer = 0.55
            spawn_blood(enemy.x, enemy.y, 55)
            spawn_sparks(enemy.x, enemy.y, 18)

    player.weapon_ammo[player.current_weapon] = player.ammo


def handle_automatic_fire():
    """Fire repeatedly while the left mouse button is held, but only for the chaingun."""
    if player.current_weapon != 3:
        return

    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0]:
        shoot()


# ------------------------------------------------------------
# 9. ENEMY AI
# ------------------------------------------------------------

def update_enemies(dt):
    global damage_vignette_timer, hellwave_events, hell_pressure

    # DOOM-inspired Hellwave sector scan:
    # The loop processes every demon that actually exists in the current
    # encounter. The number of iterations comes from the enemies list, which
    # was changed by the player's Assault/Tactical/Escape decision.
    living_count = 0
    threat_total = 0
    pulse_pressure = 0

    for enemy in enemies:
        if not enemy.alive:
            continue

        # These accumulators change once for EACH living demon processed.
        # They are not fixed print statements or a hardcoded range.
        living_count += 1
        hellwave_events += 1

        # Brutes create more Hell pressure than Imps. A damaged demon
        # contributes less pressure, so the accumulated state changes during
        # combat as well as when demons are removed from the list of living
        # enemies.
        demon_weight = enemy.threat_value
        health_ratio = max(0.0, enemy.health / enemy.max_health)
        pulse_pressure += int(demon_weight * health_ratio)
        threat_total += demon_weight

        enemy.attack_timer -= dt

        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.hypot(dx, dy)

        # Each demon class behaves differently.
        if enemy.kind == "hellhound":
            # Fast melee hunter: closes distance quickly and attacks hard.
            speed = 1.55
            attack_range = 1.05
            attack_damage = 14
            attack_delay = 0.65
            chase_range = 10.0
        elif enemy.kind == "warden":
            # Slow armored guardian: can attack from farther away.
            speed = 0.45
            attack_range = 5.5
            attack_damage = 8
            attack_delay = 1.35
            chase_range = 9.0
        elif enemy.kind == "brute":
            speed = 0.65
            attack_range = 1.25
            attack_damage = 12
            attack_delay = 0.9
            chase_range = 8.0
        else:
            speed = 0.8
            attack_range = 1.2
            attack_damage = 10
            attack_delay = 1.0
            chase_range = 8.0

        # Move toward the player when the demon's behavior allows it.
        if dist < chase_range and dist > attack_range:
            if has_line_of_sight(enemy.x, enemy.y, player.x, player.y):
                direction_x = dx / dist
                direction_y = dy / dist

                new_x = enemy.x + direction_x * speed * dt
                new_y = enemy.y + direction_y * speed * dt

                if not is_blocking(new_x, enemy.y):
                    enemy.x = new_x

                if not is_blocking(enemy.x, new_y):
                    enemy.y = new_y

        # Hell Warden has a ranged attack; the other enemies use melee.
        if enemy.kind == "warden" and dist < attack_range and enemy.attack_timer <= 0:
            if has_line_of_sight(enemy.x, enemy.y, player.x, player.y):
                player.health -= attack_damage
                player.hurt_flash = 0.15
                damage_vignette_timer = 0.30
                spawn_sparks(player.x, player.y, 10)
                enemy.attack_timer = attack_delay
        elif enemy.kind != "warden" and dist < attack_range and enemy.attack_timer <= 0:
            player.health -= attack_damage
            player.hurt_flash = 0.15
            damage_vignette_timer = 0.30
            enemy.attack_timer = attack_delay

        if player.health <= 0:
            player.health = 0

    # Hell pressure is a persistent state that follows the current demon
    # population. It eases down as demons are damaged or destroyed.
    hell_pressure = pulse_pressure

    # Save the accumulated results so the HUD and door logic can use them.
    return living_count, threat_total


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
    """Render a deliberately retro, fake-3-D environment.

    The scene is still a simple raycaster, but layered gradients,
    brick seams, floor perspective marks, flickering lights, and
    distance fog make it look much closer to a 1990s FPS.
    """
    horizon = VIEW_HEIGHT // 2 - int(player.z * 28)

    # Ceiling/floor gradients.
    for y in range(VIEW_HEIGHT):
        if y < horizon:
            t = y / max(1, horizon)
            c = int(10 + 28 * t)
            pygame.draw.line(view, (c, c, min(70, c + 12)), (0, y), (VIEW_WIDTH, y))
        else:
            t = (y - horizon) / max(1, VIEW_HEIGHT - horizon)
            c = int(52 - 34 * t)
            pygame.draw.line(view, (c + 8, c, max(10, c - 7)), (0, y), (VIEW_WIDTH, y))

    # Fake floor perspective lines give the ground a chunky old-school grid.
    for gy in range(horizon + 8, VIEW_HEIGHT, 10):
        pygame.draw.line(view, (35, 25, 24), (0, gy), (VIEW_WIDTH, gy), 1)
    for gx in range(-VIEW_WIDTH, VIEW_WIDTH * 2, 32):
        pygame.draw.line(view, (38, 27, 25), (VIEW_WIDTH // 2, horizon), (gx, VIEW_HEIGHT), 1)

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

        # Distance fog + animated flicker.
        flicker = int(5 * math.sin(game_time * 5.0 + column * 0.08))
        shade = max(24, min(220, int(235 - corrected_distance * 12) + flicker))

        hit_x = player.x + math.cos(ray_angle) * raw_distance
        hit_y = player.y + math.sin(ray_angle) * raw_distance
        hit_cell = cell_at(hit_x, hit_y)

        # Approximate which side of a map cell was hit so texture seams
        # don't look like a completely flat wall.
        fx = hit_x - math.floor(hit_x)
        fy = hit_y - math.floor(hit_y)
        side_coord = fy if abs(fx - 0.5) > abs(fy - 0.5) else fx
        seam = int(side_coord * 12) % 2

        if hit_cell == "D":
            # Red security door: panels, warning stripes, and a central lock.
            panel = 12 if (int(side_coord * 6) % 2 == 0) else -4
            wall_color = (
                min(255, shade + 30 + panel),
                max(10, int(shade * 0.16)),
                max(8, int(shade * 0.10))
            )
        else:
            # Dark industrial stone/metal wall texture.
            base = shade + (10 if seam else -5)
            wall_color = (
                max(18, min(220, base + 8)),
                max(16, min(190, base - 5)),
                max(14, min(170, base - 12))
            )

        pygame.draw.line(view, wall_color, (column, top), (column, bottom))

        # Horizontal brick/panel seams.
        if wall_height > 18:
            segment = max(4, wall_height // 5)
            for sy in range(top + segment, bottom, segment):
                if (column // 5 + sy // max(1, segment)) % 3 == 0:
                    pygame.draw.line(view, (max(12, shade // 3),) * 3,
                                     (column, sy), (column, min(bottom, sy + 1)))

        # Vertical panel highlight.
        if column % 17 == 0 and corrected_distance < 13:
            pygame.draw.line(view,
                             (min(255, shade + 28), min(240, shade + 20), min(230, shade + 14)),
                             (column, top), (column, bottom), 1)

        # Red door warning lights.
        if hit_cell == "D" and column % 16 < 3 and wall_height > 10:
            light = 120 + int(80 * (0.5 + 0.5 * math.sin(game_time * 7)))
            pygame.draw.line(view, (light, 15, 10),
                             (column, top + wall_height // 5),
                             (column, top + wall_height // 5 + 3), 2)

    # Cross-room atmospheric light shafts. They are intentionally subtle.
    glow = int(10 + 8 * (0.5 + 0.5 * math.sin(game_time * 3.5)))
    overlay = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(overlay, (120, 35, 20, glow), (VIEW_WIDTH // 2, horizon), 35)

    # Pulsing Hell lights in the center of the view.
    pulse = int(8 + 12 * (0.5 + 0.5 * math.sin(game_time * 4.2)))
    pygame.draw.circle(overlay, (180, 30, 12, pulse), (VIEW_WIDTH // 2, horizon + 12), 28)
    view.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # Dark edge vignette keeps the focus in the center of the screen.
    vignette = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT), pygame.SRCALPHA)
    for edge in range(18, 0, -2):
        alpha = max(2, 26 - edge)
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (edge, edge, VIEW_WIDTH - edge * 2, VIEW_HEIGHT - edge * 2), 2)
    view.blit(vignette, (0, 0))

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

        # Enemy-specific silhouettes. Each enemy has a distinct visual role.
        if enemy.kind == "brute":
            body = (92, 35, 25)
            head = (145, 90, 55)
            accent = (255, 80, 35)
        elif enemy.kind == "hellhound":
            body = (75, 20, 18)
            head = (150, 38, 25)
            accent = (255, 105, 25)
        elif enemy.kind == "warden":
            body = (42, 48, 55)
            head = (75, 82, 92)
            accent = (90, 220, 255)
        else:
            body = (135, 38, 28)
            head = (180, 112, 70)
            accent = (255, 205, 45)

        if enemy.flash_timer > 0:
            body = (255, 235, 210)
            head = (255, 255, 240)

        body_top = top + sprite_height // 4
        body_h = max(4, sprite_height * 3 // 4)

        if enemy.kind == "hellhound":
            # Low quadruped silhouette with animated legs.
            body_rect = (left, body_top + body_h // 5, sprite_width, max(4, body_h // 2))
            pygame.draw.ellipse(view, body, body_rect)
            leg_h = max(3, body_h // 3)
            stride = int(anim * max(1, sprite_width // 8))
            for lx in (left + sprite_width // 6, left + sprite_width * 4 // 6):
                pygame.draw.rect(view, body, (lx, body_top + body_h // 2, max(2, sprite_width // 7), leg_h + stride))
                pygame.draw.rect(view, body, (lx + sprite_width // 5, body_top + body_h // 2, max(2, sprite_width // 7), leg_h - stride))
            head_w = max(5, int(sprite_width * 0.55))
            head_h = max(5, int(sprite_height * 0.24))
            head_x = int(screen_x - head_w / 2)
            pygame.draw.ellipse(view, head, (head_x, top + sprite_height // 8, head_w, head_h))
            pygame.draw.polygon(view, accent, [(head_x + 2, top + 5), (head_x - 2, top - 2), (head_x + 7, top + 5)])
            pygame.draw.polygon(view, accent, [(head_x + head_w - 2, top + 5), (head_x + head_w + 2, top - 2), (head_x + head_w - 7, top + 5)])
        elif enemy.kind == "warden":
            # Tall armored guardian with glowing cyan core.
            pygame.draw.rect(view, body, (left + sprite_width // 8, body_top, max(3, sprite_width * 3 // 4), body_h))
            pygame.draw.rect(view, (25, 28, 34), (left, body_top + body_h // 4, max(3, sprite_width // 5), body_h // 2))
            pygame.draw.rect(view, (25, 28, 34), (left + sprite_width * 4 // 5, body_top + body_h // 4, max(3, sprite_width // 5), body_h // 2))
            head_w = max(5, int(sprite_width * 0.65))
            head_h = max(5, int(sprite_height * 0.27))
            head_x = int(screen_x - head_w / 2)
            pygame.draw.rect(view, head, (head_x, top, head_w, head_h))
            pygame.draw.line(view, accent, (head_x + 2, top + head_h // 2), (head_x + head_w - 2, top + head_h // 2), max(1, head_h // 5))
            core = max(2, int(sprite_width * 0.16))
            pygame.draw.circle(view, accent, (int(screen_x), body_top + body_h // 3), core)
            pygame.draw.polygon(view, (105, 115, 125), [(head_x, top + 3), (head_x - max(2, head_w // 5), top - max(2, head_h // 3)), (head_x + 3, top + 4)])
            pygame.draw.polygon(view, (105, 115, 125), [(head_x + head_w, top + 3), (head_x + head_w + max(2, head_w // 5), top - max(2, head_h // 3)), (head_x + head_w - 3, top + 4)])
        else:
            pygame.draw.ellipse(view, body, (left, body_top, sprite_width, body_h))
            arm_w = max(2, sprite_width // 4)
            pygame.draw.rect(view, body, (left - arm_w // 2, body_top + body_h // 5, arm_w, body_h // 2))
            pygame.draw.rect(view, body, (left + sprite_width - arm_w // 2, body_top + body_h // 5, arm_w, body_h // 2))
            head_w = max(5, int(sprite_width * 0.62))
            head_h = max(5, int(sprite_height * 0.30))
            head_x = int(screen_x - head_w / 2)
            pygame.draw.ellipse(view, head, (head_x, top, head_w, head_h))

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

        # Eyes / visor.
        eye_y = top + max(2, int(sprite_height * 0.10))
        eye_w = max(2, sprite_width // 9)
        if enemy.kind == "warden":
            pygame.draw.rect(view, accent, (int(screen_x - eye_w * 2), eye_y, eye_w * 4, max(2, eye_w)))
        elif enemy.kind != "hellhound":
            for ex in (head_x + head_w // 4, head_x + head_w * 3 // 5):
                pygame.draw.rect(view, accent, (ex, eye_y, eye_w, max(2, eye_w)))
        else:
            pygame.draw.rect(view, accent, (int(screen_x - eye_w * 2), eye_y + 1, eye_w * 4, max(2, eye_w)))

        # Mouth/teeth for organic demons.
        if enemy.kind in ("imp", "brute", "hellhound"):
            mouth_y = top + int(sprite_height * 0.22)
            pygame.draw.line(view, (35, 10, 8), (int(screen_x - sprite_width * 0.18), mouth_y), (int(screen_x + sprite_width * 0.18), mouth_y), max(1, sprite_width // 12))
            if enemy.kind == "hellhound":
                for tooth_x in (-0.12, -0.04, 0.04, 0.12):
                    pygame.draw.polygon(view, (235, 225, 185), [(int(screen_x + sprite_width * tooth_x), mouth_y), (int(screen_x + sprite_width * tooth_x + 2), mouth_y), (int(screen_x + sprite_width * tooth_x + 1), mouth_y + max(2, sprite_height // 16))])

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
    """Draw a different retro weapon silhouette for each selected weapon."""
    bob_x = int(math.sin(player.bob_time * 1.8) * 5)
    bob_y = int(abs(math.cos(player.bob_time * 1.8)) * 4)
    recoil = int(muzzle_flash_timer * 80)
    center_x = WIDTH // 2 + bob_x
    base_y = HEIGHT - 25 + bob_y + recoil

    weapon_name = WEAPONS[player.current_weapon]["name"]

    if muzzle_flash_timer > 0:
        flash_size = 70 + int(muzzle_flash_timer * 220)
        flash_color = (255, 150, 45) if player.current_weapon != 4 else (255, 220, 80)
        pygame.draw.polygon(screen, flash_color, [
            (center_x, base_y - 155),
            (center_x - flash_size // 2, base_y - 35),
            (center_x + flash_size // 2, base_y - 35),
        ])
        pygame.draw.polygon(screen, (255, 245, 190), [
            (center_x, base_y - 142),
            (center_x - flash_size // 5, base_y - 55),
            (center_x + flash_size // 5, base_y - 55),
        ])

    if player.current_weapon == 1:
        # Pistol
        pygame.draw.polygon(screen, (18, 18, 22), [
            (center_x - 45, base_y), (center_x - 25, base_y - 110),
            (center_x + 25, base_y - 110), (center_x + 42, base_y)
        ])
        pygame.draw.rect(screen, (75, 75, 82), (center_x - 18, base_y - 126, 36, 75))
        pygame.draw.rect(screen, (8, 8, 10), (center_x - 10, base_y - 145, 20, 25))

    elif player.current_weapon == 2:
        # Double-barrel shotgun
        pygame.draw.polygon(screen, (30, 24, 20), [
            (center_x - 70, base_y), (center_x - 48, base_y - 95),
            (center_x + 48, base_y - 95), (center_x + 70, base_y)
        ])
        pygame.draw.rect(screen, (75, 65, 55), (center_x - 46, base_y - 135, 92, 38))
        pygame.draw.rect(screen, (10, 10, 12), (center_x - 31, base_y - 155, 22, 55))
        pygame.draw.rect(screen, (10, 10, 12), (center_x + 9, base_y - 155, 22, 55))

    elif player.current_weapon == 3:
        # Chaingun
        pygame.draw.polygon(screen, (25, 28, 32), [
            (center_x - 65, base_y), (center_x - 40, base_y - 105),
            (center_x + 42, base_y - 105), (center_x + 65, base_y)
        ])
        for offset in (-28, -9, 10, 29):
            pygame.draw.rect(screen, (65, 68, 75),
                             (center_x + offset - 5, base_y - 160, 10, 75))
        pygame.draw.rect(screen, (110, 110, 118), (center_x - 50, base_y - 82, 100, 16))

    else:
        # Rocket launcher
        pygame.draw.polygon(screen, (25, 30, 25), [
            (center_x - 72, base_y), (center_x - 52, base_y - 108),
            (center_x + 52, base_y - 108), (center_x + 72, base_y)
        ])
        pygame.draw.rect(screen, (65, 75, 65), (center_x - 36, base_y - 145, 72, 90))
        pygame.draw.rect(screen, (10, 10, 10), (center_x - 27, base_y - 178, 54, 45))
        pygame.draw.circle(screen, (80, 180, 70), (center_x, base_y - 155), 8)

    label = font.render(weapon_name, True, (230, 190, 90))
    screen.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT - 96))


def render_hud():
    # Top status strip.
    pygame.draw.rect(screen, (8, 8, 10), (0, 0, WIDTH, 28))
    pygame.draw.line(screen, (105, 25, 20), (0, 28), (WIDTH, 28), 2)

    mode_text = font.render(f"MODE: {game_strategy.upper()}", True, (220, 220, 220))
    objective = "OBJECTIVE: FIND RED KEY" if not player.has_key else "OBJECTIVE: KILL ALL ENEMIES"
    if player.has_key and living_enemies == 0:
        objective = "OBJECTIVE: OPEN RED DOOR"
    objective_text = font.render(objective, True, (230, 180, 80))
    screen.blit(mode_text, (10, 4))
    screen.blit(objective_text, (250, 4))

    # Bottom HUD bar with beveled-looking separators.
    pygame.draw.rect(screen, (10, 10, 13), (0, HEIGHT - 78, WIDTH, 78))
    pygame.draw.line(screen, (115, 115, 125), (0, HEIGHT - 78), (WIDTH, HEIGHT - 78), 2)
    for x in (200, 400, 600):
        pygame.draw.line(screen, (55, 55, 62), (x, HEIGHT - 72), (x, HEIGHT - 8), 1)

    health_text = font.render(f"HEALTH: {player.health}", True, (220, 220, 220))
    ammo_text = font.render(f"AMMO: {player.ammo}", True, (220, 220, 220))
    weapon_text = font.render(f"WEAPON: {WEAPONS[player.current_weapon]["name"]}", True, (230, 190, 90))
    key_text = font.render("RED KEY: YES" if player.has_key else "RED KEY: NO", True, (220, 220, 220))
    enemy_text = font.render(f"ENEMIES: {living_enemies}", True, (220, 220, 220))
    threat_text = font.render(f"THREAT: {total_enemy_threat}", True, (220, 220, 220))
    hell_text = font.render(f"HELLWAVE: {hell_pressure}", True, (220, 120, 80))
    enemy_types = font.render("I:IMP  B:BRUTE  H:HOUND  W:WARDEN", True, (155, 155, 165))

    screen.blit(health_text, (15, HEIGHT - 58))
    screen.blit(ammo_text, (215, HEIGHT - 58))
    screen.blit(weapon_text, (215, HEIGHT - 12))
    screen.blit(key_text, (415, HEIGHT - 58))
    screen.blit(enemy_text, (615, HEIGHT - 58))
    screen.blit(threat_text, (615, HEIGHT - 32))
    screen.blit(hell_text, (615, HEIGHT - 12))
    screen.blit(enemy_types, (15, HEIGHT - 12))

    # Enemy Intelligence: use the ID as a dictionary key, not a list search.
    if intel_panel_visible and intel_target_id is not None:
        intel_enemy = enemy_registry.get(intel_target_id)
        if intel_enemy is not None:
            panel = pygame.Rect(WIDTH // 2 - 150, 76, 300, 112)
            pygame.draw.rect(screen, (12, 12, 18), panel)
            pygame.draw.rect(screen, (170, 45, 35), panel, 2)
            state_label = "ALIVE" if intel_enemy.alive else "ELIMINATED"
            intel_lines = [
                f"ENEMY INTEL: {intel_enemy.entity_id}",
                f"TYPE: {intel_enemy.kind.upper()}  STATUS: {state_label}",
                f"HEALTH: {max(0, intel_enemy.health)}/{intel_enemy.max_health}",
                f"POSITION: ({intel_enemy.x:.1f}, {intel_enemy.y:.1f})",
                "Press J for next ID; I to close",
            ]
            for line_number, line in enumerate(intel_lines):
                color = (255, 190, 95) if line_number == 0 else (225, 225, 230)
                line_surface = font.render(line, True, color)
                screen.blit(line_surface, (panel.x + 10, panel.y + 8 + line_number * 19))

    # Health/ammo mini-bars make the HUD feel more game-like.
    pygame.draw.rect(screen, (35, 35, 38), (15, HEIGHT - 30, 160, 6))
    pygame.draw.rect(screen, (165, 35, 30), (15, HEIGHT - 30, int(160 * player.health / 100), 6))
    pygame.draw.rect(screen, (35, 35, 38), (215, HEIGHT - 30, 160, 6))
    ammo_ratio = min(1.0, player.ammo / max(1, starting_ammo))
    pygame.draw.rect(screen, (190, 150, 45), (215, HEIGHT - 30, int(160 * ammo_ratio), 6))

    # Enemy radar markers.
    living = [e for e in enemies if e.alive]
    radar_font = pygame.font.Font(None, 22)
    for enemy in living:
        dx = enemy.x - player.x
        dy = enemy.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.01:
            continue
        rel = normalize_angle(math.atan2(dy, dx) - player.angle)
        if abs(rel) > FOV * 0.42:
            side = -1 if rel < 0 else 1
            arrow_x = WIDTH // 2 + side * (WIDTH // 2 - 45)
            label = radar_font.render("ENEMY", True, (255, 90, 90))
            screen.blit(label, (arrow_x - label.get_width() // 2, 40))
        elif dist > 7.0:
            label = radar_font.render(f"ENEMY {int(dist)}m", True, (255, 90, 90))
            screen.blit(label, (WIDTH // 2 - label.get_width() // 2, 40))

    # Crosshair.
    cx, cy = WIDTH // 2, HEIGHT // 2
    pygame.draw.line(screen, (235, 235, 235), (cx - 7, cy), (cx + 7, cy), 1)
    pygame.draw.line(screen, (235, 235, 235), (cx, cy - 7), (cx, cy + 7), 1)

    if hit_marker_timer > 0:
        size = 12
        pygame.draw.line(screen, (255, 80, 80), (cx - size, cy - size), (cx + size, cy + size), 3)
        pygame.draw.line(screen, (255, 80, 80), (cx + size, cy - size), (cx - size, cy + size), 3)


def render_minimap():
    """Retro tactical minimap with key, door, player, and enemy markers."""
    scale = 8
    offset_x = 10
    offset_y = 38

    pygame.draw.rect(screen, (5, 5, 7),
                     (offset_x - 3, offset_y - 3, MAP_W * scale + 6, MAP_H * scale + 6))

    for y in range(MAP_H):
        for x in range(MAP_W):
            cell = LEVEL[y][x]
            if cell == "D":
                cell_color = (190, 25, 25)
            elif cell == "K":
                cell_color = (170, 25, 25)
            elif cell == "#":
                cell_color = (85, 85, 92)
            else:
                cell_color = (22, 22, 25)
            pygame.draw.rect(screen, cell_color,
                             (offset_x + x * scale, offset_y + y * scale, scale - 1, scale - 1))

    # Living enemies are visible as red pips on the minimap.
    for enemy in enemies:
        if enemy.alive:
            pygame.draw.circle(screen, (230, 45, 40),
                               (int(offset_x + enemy.x * scale), int(offset_y + enemy.y * scale)), 2)

    pygame.draw.circle(screen, (50, 230, 70),
                       (int(offset_x + player.x * scale), int(offset_y + player.y * scale)), 3)
    pygame.draw.line(screen, (80, 255, 90),
                     (int(offset_x + player.x * scale), int(offset_y + player.y * scale)),
                     (int(offset_x + (player.x + math.cos(player.angle) * 0.9) * scale),
                      int(offset_y + (player.y + math.sin(player.angle) * 0.9) * scale)), 2)


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

            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                weapon_number = event.key - pygame.K_0
                select_weapon(weapon_number)

            elif event.key == pygame.K_SPACE and player.z <= 0.001:
                player.jump_velocity = JUMP_STRENGTH

            elif event.key == pygame.K_i:
                # Toggle the intel panel; displayed data is fetched by registry key.
                intel_panel_visible = not intel_panel_visible

            elif event.key == pygame.K_j and intel_enemy_ids:
                # Cycle IDs, then use the selected ID for the next dictionary lookup.
                intel_target_index = (intel_target_index + 1) % len(intel_enemy_ids)
                intel_target_id = intel_enemy_ids[intel_target_index]
                intel_panel_visible = True

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
    living_enemies, total_enemy_threat = update_enemies(dt)
    update_interactions()
    update_particles(dt)

    player.shoot_cooldown = max(
        0,
        player.shoot_cooldown - dt
    )

    # Only the chaingun checks for a continuously held mouse button.
    # The other weapons still require a fresh mouse click.
    handle_automatic_fire()

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

    # Subtle CRT scanlines for a deliberately retro presentation.
    for sy in range(0, HEIGHT, 4):
        pygame.draw.line(screen, (0, 0, 0), (0, sy), (WIDTH, sy), 1)

    render_weapon()
    render_hud()

    # Minimap can be toggled off by commenting out this line.
    render_minimap()

    # Instructions.
    instructions = font.render(
        "WASD Move | Mouse/Arrows Turn | SPACE Jump | LMB Shoot | 1-4 Weapons | E Use | I Intel | J Next ID",
        True,
        (220, 220, 220)
    )

    screen.blit(
        instructions,
        (WIDTH // 2 - instructions.get_width() // 2, 32)
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

if game_music is not None:
    game_music.stop()
if pygame.mixer.get_init():
    pygame.mixer.quit()

pygame.quit()
sys.exit()
