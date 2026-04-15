import os
import pygame
import math
import sys
import random

# GAME SETTINGS
WIDTH, HEIGHT   = 800, 600
HALF_W, HALF_H  = WIDTH // 2, HEIGHT // 2
FPS             = 60
FOV             = math.pi / 3          # 60° field of view
HALF_FOV        = FOV / 2
NUM_RAYS        = WIDTH                # one ray per column
MAX_DEPTH       = 20.0                 # max render distance (world units)
MOVE_SPEED      = 0.05                 # world-units per frame
ROT_SPEED       = 0.03                 # radians per frame (keyboard)
MOUSE_SENS      = 0.002               # radians per pixel
PLAYER_RADIUS   = 0.25                 # collision circle radius

# Camera pitch (vertical look) – purely cosmetic, shifts horizon up/down
PITCH_STEP      = 0.02
PITCH_MAX       = 0.45

# Minimap
MINIMAP_RADIUS  = 8                   # tiles shown each direction from player
MINIMAP_SCALE   = 4                   # pixels per tile
MINIMAP_MARGIN  = 10

# Enemy constants
ENEMY_HIT_RADIUS    = 0.4            # how close a bullet needs to be to kill
ENEMY_ATTACK_RANGE  = 12.0           # tiles; beyond this enemies are idle
ENEMY_DAMAGE        = 5              # HP per hit
ENEMY_ATTACK_RATE   = 0.6            # seconds between enemy attacks
ENEMY_DEATH_DISPLAY = 0.7            # seconds the corpse remains visible
BULLET_SPEED        = 0.18           # world-units per frame

# Scoring
KILL_SCORE      = 100
LEVEL_SCORE     = 1000               # score needed to advance (increases per level)

# COLOURS
C_CEILING   = (20,  20,  20)
C_FLOOR     = (15,  15,  15)
C_WALL      = (190, 40,  40)         # wall base colour (shaded per distance)
C_TEXT      = (255, 255, 255)
C_CROSSHAIR = (255, 255, 255)
C_HEALTH    = (255,  60,  60)
C_INFO      = (  0, 200, 255)

# GLOBALS (populated by generate_map / spawn_*)
WORLD_MAP    = []    # list of rows; 0 = open, 1 = wall
MAP_W        = 0
MAP_H        = 0
ROOM_CENTERS = []    # list of (cx, cy) open-floor tile centres
enemies      = []
bullets      = []

MUSIC_END = pygame.USEREVENT + 1


# TINY MAP HELPERS
def tile_is_wall(mx, my):
    #True if (mx,my) is outside the map bounds or is a wall tile. 
    if my < 0 or my >= MAP_H or mx < 0 or mx >= MAP_W:
        return True
    return WORLD_MAP[my][mx] != 0


def tile_is_open(mx, my):
    return not tile_is_wall(mx, my)


# MAP GENERATION (maze + rooms + corridors)
def carve_maze(size):
        #Recursive-backtracker maze on a grid where every other cell is open.  
    maze = [[1] * size for _ in range(size)]
    for y in range(1, size - 1, 2):
        for x in range(1, size - 1, 2):
            maze[y][x] = 0

    stack   = [(1, 1)]
    visited = {(1, 1)}
    while stack:
        x, y    = stack[-1]
        neighbors = [(x+dx, y+dy)
                        for dx, dy in ((2,0),(-2,0),(0,2),(0,-2))
                        if 1 <= x+dx < size-1 and 1 <= y+dy < size-1
                        and (x+dx, y+dy) not in visited]
        if not neighbors:
            stack.pop()
            continue
        nx, ny = random.choice(neighbors)
        maze[(y+ny)//2][(x+nx)//2] = 0
        maze[ny][nx] = 0
        visited.add((nx, ny))
        stack.append((nx, ny))
    return maze


def carve_rect(rx, ry, rw, rh):
    for y in range(ry, ry+rh):
        for x in range(rx, rx+rw):
            WORLD_MAP[y][x] = 0


def carve_corridor(x1, y1, x2, y2):
        #Two-tile-wide L-shaped corridor so it is always walkable.   
    if random.random() < 0.5:
        for x in range(min(x1,x2), max(x1,x2)+1):
            WORLD_MAP[y1][x] = 0
            if y1+1 < MAP_H: WORLD_MAP[y1+1][x] = 0
        for y in range(min(y1,y2), max(y1,y2)+1):
            WORLD_MAP[y][x2] = 0
            if x2+1 < MAP_W: WORLD_MAP[y][x2+1] = 0
    else:
        for y in range(min(y1,y2), max(y1,y2)+1):
            WORLD_MAP[y][x1] = 0
            if x1+1 < MAP_W: WORLD_MAP[y][x1+1] = 0
        for x in range(min(x1,x2), max(x1,x2)+1):
            WORLD_MAP[y2][x] = 0
            if y2+1 < MAP_H: WORLD_MAP[y2+1][x] = 0


def bfs_connected(sx, sy, gx, gy):
    #Return True if (sx,sy) can reach (gx,gy) through open tiles.
    if (sx,sy) == (gx,gy): return True
    visited, stack = set(), [(sx,sy)]
    while stack:
        x, y = stack.pop()
        if (x,y) == (gx,gy): return True
        if (x,y) in visited: continue
        visited.add((x,y))
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if tile_is_open(nx, ny) and (nx,ny) not in visited:
                stack.append((nx, ny))
    return False


def generate_map():
    #Build a fresh procedural map and populate ROOM_CENTERS.
    global WORLD_MAP, MAP_W, MAP_H, ROOM_CENTERS

    size       = 50
    WORLD_MAP  = carve_maze(size)
    MAP_W      = size
    MAP_H      = size
    ROOM_CENTERS = []

    # Try to place ~6 rectangular rooms without overlap
    placed = []
    for _ in range(30):             # 30 attempts to place 6 rooms
        if len(placed) >= 6: break
        rw = random.randint(6, 10)
        rh = random.randint(6, 10)
        rx = random.randint(2, size - rw - 2)
        ry = random.randint(2, size - rh - 2)
        overlap = any(rx < ox+ow+2 and ox < rx+rw+2 and
                        ry < oy+oh+2 and oy < ry+rh+2
                        for ox,oy,ow,oh in placed)
        if not overlap:
            carve_rect(rx, ry, rw, rh)
            placed.append((rx, ry, rw, rh))
            ROOM_CENTERS.append((rx + rw//2, ry + rh//2))

    # Connect rooms with corridors (minimum spanning tree order)
    if len(ROOM_CENTERS) >= 2:
        connected = [ROOM_CENTERS[0]]
        remaining = ROOM_CENTERS[1:]
        while remaining:
            best_dist, best_a, best_b = float('inf'), None, None
            for a in connected:
                for b in remaining:
                    d = (a[0]-b[0])**2 + (a[1]-b[1])**2
                    if d < best_dist:
                        best_dist, best_a, best_b = d, a, b
            carve_corridor(best_a[0], best_a[1], best_b[0], best_b[1])
            connected.append(best_b)
            remaining.remove(best_b)

        # A few extra cross-links for variety
        for _ in range(min(3, len(ROOM_CENTERS)-1)):
            a, b = random.sample(ROOM_CENTERS, 2)
            carve_corridor(a[0], a[1], b[0], b[1])

    # Ensure all rooms are actually reachable from room 0
    if len(ROOM_CENTERS) >= 2:
        src = ROOM_CENTERS[0]
        for dst in ROOM_CENTERS[1:]:
            if not bfs_connected(src[0], src[1], dst[0], dst[1]):
                carve_corridor(src[0], src[1], dst[0], dst[1])

    # Fallback: if no rooms were placed, guarantee at least one open area
    if not ROOM_CENTERS:
        carve_rect(2, 2, 8, 8)
        ROOM_CENTERS.append((6, 6))


# COLLISION HELPERS
def position_free(px, py):

    # Centre tile
    if tile_is_wall(int(px), int(py)):
        return False
    # Cardinal probe points
    for dx, dy in ((PLAYER_RADIUS, 0), (-PLAYER_RADIUS, 0),
                    (0, PLAYER_RADIUS), (0, -PLAYER_RADIUS)):
        if tile_is_wall(int(px+dx), int(py+dy)):
            return False
    return True


def slide_move(px, py, dx, dy):

    nx, ny = px+dx, py+dy
    if position_free(nx, ny):
        return nx, ny
    if position_free(px+dx, py):
        return px+dx, py
    if position_free(px, py+dy):
        return px, py+dy
    return px, py   # fully blocked – stay put


# SPAWN HELPERS
def find_open_tile():

    for _ in range(2000):
        x = random.randint(1, MAP_W-2)
        y = random.randint(1, MAP_H-2)
        if WORLD_MAP[y][x] != 0:
            continue
        open_nb = sum(1 for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),
                                        (-1,-1),(1,-1),(-1,1),(1,1))
                        if tile_is_open(x+dx, y+dy))
        if open_nb >= 5:
            return x+0.5, y+0.5
    # Hard fallback
    for y in range(1, MAP_H-1):
        for x in range(1, MAP_W-1):
            if WORLD_MAP[y][x] == 0:
                return x+0.5, y+0.5
    return 2.5, 2.5


def best_facing_angle(px, py, steps=16):

    best_angle, best_score = 0.0, -1.0
    for i in range(steps):
        angle = i * (2*math.pi / steps)
        total = 0.0
        for j in range(7):
            ray = angle + (j/6 - 0.5) * FOV
            cos_r, sin_r = math.cos(ray), math.sin(ray)
            for k in range(1, 150):
                tx = px + cos_r * (k*0.1)
                ty = py + sin_r * (k*0.1)
                if tile_is_wall(int(tx), int(ty)):
                    total += k*0.1
                    break
            else:
                total += MAX_DEPTH
        avg = total / 7
        if avg > best_score:
            best_score  = avg
            best_angle  = angle
    return best_angle


def find_spawn(min_dist_from=None, min_dist=8.0):

    if ROOM_CENTERS:
        shuffled = list(ROOM_CENTERS)
        random.shuffle(shuffled)
        for cx, cy in shuffled:
            if tile_is_wall(cx, cy):
                continue
            if min_dist_from is not None:
                if math.hypot(cx-min_dist_from[0], cy-min_dist_from[1]) < min_dist:
                    continue
            px, py = cx+0.5, cy+0.5
            if position_free(px, py):
                return px, py
    # Fall back to any open tile
    return find_open_tile()


# ENEMY
class Enemy:
    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.alive = True             # still fighting
        self.dead  = False            # playing death animation
        self.state = 'idle'           # 'idle' | 'attack' | 'dead'
        self.dmg_timer   = 0.0       # countdown between attacks
        self.death_timer = 0.0       # countdown before corpse is removed


def spawn_enemies(count, avoid_x, avoid_y):
    #Spawn `count` enemies, each far from (avoid_x, avoid_y).
    for _ in range(count * 50):      # generous attempt budget
        if sum(1 for e in enemies if not e.dead) >= count:
            break
        px, py = find_spawn(min_dist_from=(avoid_x, avoid_y), min_dist=8.0)
        enemies.append(Enemy(px, py))


# BULLET
class Bullet:
    def __init__(self, x, y, angle):
        self.x     = x
        self.y     = y
        self.dx    = math.cos(angle) * BULLET_SPEED
        self.dy    = math.sin(angle) * BULLET_SPEED
        self.alive = True

    def update(self):
        self.x += self.dx
        self.y += self.dy

        # Kill bullet if it hits a wall
        if tile_is_wall(int(self.x), int(self.y)):
            self.alive = False
            return

        # Check enemy hits
        for enemy in enemies:
            if enemy.alive and math.hypot(enemy.x-self.x, enemy.y-self.y) < ENEMY_HIT_RADIUS:
                enemy.alive      = False
                enemy.dead       = True
                enemy.state      = 'dead'
                enemy.death_timer = ENEMY_DEATH_DISPLAY
                self.alive       = False
                return


# PLAYER
class Player:
    def __init__(self):
        self.x      = 2.5
        self.y      = 2.5
        self.angle  = 0.0
        self.pitch  = 0.0            # shifts horizon up/down (cosmetic)
        self.health = 100
        self.score  = 0
        self.levels_cleared = 0
        self.target_score   = LEVEL_SCORE
        self.dmg_cooldown   = 0.0   # seconds of post-hit invincibility

        # Audio (optional – game runs fine without it)
        self.has_audio = False
        pygame.mixer.init()
        try:
            self.snd_shoot = pygame.mixer.Sound('dspistol.wav')
            pygame.mixer.music.load('01._Hell_On_Earth.mp3')
            pygame.mixer.music.play(0)
            pygame.mixer.music.set_endevent(MUSIC_END)
            self.has_audio = True
        except Exception:
            pass

    def shoot(self):
        if self.has_audio:
            self.snd_shoot.play()
        bullets.append(Bullet(self.x, self.y, self.angle))

    def move(self, keys, dt):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        # Build movement vector from WASD
        fwd  = ( MOVE_SPEED if keys[pygame.K_w] else
                -MOVE_SPEED if keys[pygame.K_s] else 0)
        side = ( MOVE_SPEED if keys[pygame.K_d] else
                -MOVE_SPEED if keys[pygame.K_a] else 0)

        # fwd  = along facing direction
        # side = perpendicular to facing direction (strafe)
        dx = cos_a * fwd - sin_a * side
        dy = sin_a * fwd + cos_a * side

        self.x, self.y = slide_move(self.x, self.y, dx, dy)

        # Arrow-key rotation
        if keys[pygame.K_LEFT]:  self.angle -= ROT_SPEED
        if keys[pygame.K_RIGHT]: self.angle += ROT_SPEED

        # Q/E or PageUp/PageDown for vertical pitch
        if keys[pygame.K_q] or keys[pygame.K_PAGEUP]:
            self.pitch = min(PITCH_MAX, self.pitch + PITCH_STEP)
        if keys[pygame.K_e] or keys[pygame.K_PAGEDOWN]:
            self.pitch = max(-PITCH_MAX, self.pitch - PITCH_STEP)

        # Keep angle in [0, 2π) to prevent float drift over long sessions
        self.angle %= (2 * math.pi)

    def apply_mouse(self, rel_x):
        #Rotate by mouse X delta (called once per frame).
        self.angle += rel_x * MOUSE_SENS
        self.angle %= (2 * math.pi)

    def tick_damage(self, dt):
        if self.dmg_cooldown > 0:
            self.dmg_cooldown = max(0.0, self.dmg_cooldown - dt)

    def take_hit(self, amount):
        # Deal damage only if the invincibility window has expired.
        if self.dmg_cooldown <= 0:
            self.health       = max(0, self.health - amount)
            self.dmg_cooldown = 0.5    # 0.5 s invincibility


# RAYCASTER  (DDA – Digital Differential Analysis)

def cast_rays(screen, player):

    vertical_shift = int(player.pitch * HALF_H)

    # Ceiling and floor as two solid rects (fast)
    pygame.draw.rect(screen, C_CEILING, (0, 0, WIDTH, HALF_H + vertical_shift))
    pygame.draw.rect(screen, C_FLOOR,   (0, HALF_H + vertical_shift, WIDTH, HEIGHT))

    z_buffer = [MAX_DEPTH] * WIDTH    # stores per-column wall distance for sprite occlusion

    for col in range(WIDTH):
        # camera_x: -1 at left edge, 0 at centre, +1 at right edge
        camera_x = 2.0 * col / WIDTH - 1.0

        # Ray direction in world space
        # dir_x/dir_y is the player's facing vector;
        # plane_x/plane_y is the camera plane (perpendicular, scaled by tan(HALF_FOV))
        plane_len = math.tan(HALF_FOV)
        dir_x  = math.cos(player.angle)
        dir_y  = math.sin(player.angle)
        plane_x = -dir_y * plane_len    # perpendicular, pointing right
        plane_y =  dir_x * plane_len

        ray_dx = dir_x + plane_x * camera_x
        ray_dy = dir_y + plane_y * camera_x

        # Current map tile under the player
        map_x = int(player.x)
        map_y = int(player.y)

        # DDA step lengths: distance the ray must travel along itself to
        # cross one full tile boundary in X or Y respectively.
        # Guard against zero direction (1e30 = effectively infinity).
        delta_x = abs(1.0 / ray_dx) if ray_dx != 0.0 else 1e30
        delta_y = abs(1.0 / ray_dy) if ray_dy != 0.0 else 1e30

        # Initialise side distances (distance to FIRST X or Y boundary)
        # and step direction (+1 or -1 in map coordinates)
        if ray_dx < 0:
            step_x  = -1
            side_dx = (player.x - map_x) * delta_x
        else:
            step_x  = 1
            side_dx = (map_x + 1.0 - player.x) * delta_x

        if ray_dy < 0:
            step_y  = -1
            side_dy = (player.y - map_y) * delta_y
        else:
            step_y  = 1
            side_dy = (map_y + 1.0 - player.y) * delta_y

        # DDA march until we hit a wall 
        hit  = False
        side = 0    # 0 = hit an X-face (east/west wall), 1 = hit a Y-face (north/south)
        for _ in range(int(MAX_DEPTH * 3)):   # enough steps for any map diagonal
            # Advance whichever boundary is nearer
            if side_dx < side_dy:
                side_dx += delta_x
                map_x   += step_x
                side     = 0
            else:
                side_dy += delta_y
                map_y   += step_y
                side     = 1

            # Off-map check
            if map_y < 0 or map_y >= MAP_H or map_x < 0 or map_x >= MAP_W:
                break

            if WORLD_MAP[map_y][map_x] != 0:
                hit = True
                break

        if not hit:
            continue   # ray escaped the map – column stays as ceiling/floor

        # Perpendicular distance (fisheye-free)
        if side == 0:
            perp_dist = (map_x - player.x + (1 - step_x) / 2) / ray_dx
        else:
            perp_dist = (map_y - player.y + (1 - step_y) / 2) / ray_dy

        # Clamp to a small positive value – should never reach zero with DDA,
        # but this guards against floating-point edge cases.
        perp_dist       = max(perp_dist, 0.05)
        z_buffer[col]   = perp_dist

        # Wall slice
        wall_h   = int(HEIGHT / perp_dist)
        draw_top = max(0, HALF_H - wall_h // 2 + vertical_shift)
        draw_bot = min(HEIGHT-1, HALF_H + wall_h // 2 + vertical_shift)

        # Shading: Y-side (north/south) walls slightly darker for 3-D feel;
        # further walls are darker too.
        shade_factor = 0.65 if side == 1 else 1.0
        dist_factor  = max(0.0, 1.0 - perp_dist / MAX_DEPTH)
        brightness   = shade_factor * dist_factor

        color = (
            max(0, min(255, int(C_WALL[0] * brightness))),
            max(0, min(255, int(C_WALL[1] * brightness))),
            max(0, min(255, int(C_WALL[2] * brightness))),
        )

        pygame.draw.line(screen, color, (col, draw_top), (col, draw_bot))

    return z_buffer


# ENEMY BILLBOARD SPRITE
def draw_enemy_sprite(screen, cx, cy, size, state):
    #Simple humanoid silhouette sized by projected height `size`.
    if state == 'dead':
        body_col = (60, 0, 0)
    elif state == 'attack':
        body_col = (240, 50, 50)
    else:
        body_col = (140, 20, 20)

    bw = max(14, int(size * 0.32))
    bh = max(24, int(size * 0.65))
    hr = max(8,  int(size * 0.15))   # head radius
    lh = max(8,  int(size * 0.18))   # leg height

    bx = int(cx - bw/2)
    by = int(cy + hr)

    pygame.draw.rect(screen, body_col, (bx, by, bw, bh))
    head_col = tuple(min(255, c+70) for c in body_col)
    pygame.draw.circle(screen, head_col, (int(cx), int(cy + hr)), hr)
    pygame.draw.circle(screen, (255,255,255), (int(cx), int(cy + hr)), max(2, hr//4))
    # Legs
    pygame.draw.line(screen, (30,0,0), (bx+4, by+bh), (bx+4, by+bh+lh), 2)
    pygame.draw.line(screen, (30,0,0), (bx+bw-4, by+bh), (bx+bw-4, by+bh+lh), 2)


# ENEMY RENDERING + AI UPDATE
def update_and_draw_enemies(screen, player, z_buffer, dt):

    for enemy in list(enemies):

        # Death countdown 
        if enemy.dead:
            enemy.death_timer -= dt
            if enemy.death_timer <= 0:
                enemies.remove(enemy)
                continue
            # Fall through to render the corpse

        else:
            # Range check
            dx   = enemy.x - player.x
            dy   = enemy.y - player.y
            dist = math.hypot(dx, dy)

            if dist > ENEMY_ATTACK_RANGE:
                enemy.state    = 'idle'
                enemy.dmg_timer = 0.0
            else:
                # Line-of-sight walk 
                # Walk from player toward enemy in small steps.  If any step
                # lands in a wall tile, LOS is blocked.
                steps   = max(1, int(dist / 0.15))
                cos_dir = dx / dist
                sin_dir = dy / dist
                blocked = False
                for k in range(1, steps):
                    tx = player.x + cos_dir * (k * 0.15)
                    ty = player.y + sin_dir * (k * 0.15)
                    if tile_is_wall(int(tx), int(ty)):
                        blocked = True
                        break

                if blocked:
                    enemy.state    = 'idle'
                    enemy.dmg_timer = 0.0
                else:
                    enemy.state    = 'attack'
                    enemy.dmg_timer -= dt
                    if enemy.dmg_timer <= 0:
                        player.take_hit(ENEMY_DAMAGE)
                        # Award score for surviving close combat? – or just when killed.
                        enemy.dmg_timer = ENEMY_ATTACK_RATE

        # 2-D → screen projection 
        dx = enemy.x - player.x
        dy = enemy.y - player.y

        angle_to   = math.atan2(dy, dx)
        diff_angle = (angle_to - player.angle + math.pi) % (2*math.pi) - math.pi

        # Skip enemies behind the camera (outside FOV + small margin)
        if abs(diff_angle) > HALF_FOV + 0.3:
            continue

        # Perpendicular distance removes sprite fisheye (same correction as walls)
        perp_dist = math.hypot(dx, dy) * math.cos(diff_angle)
        if perp_dist < 0.1:
            continue

        # Horizontal screen position
        screen_x = int(HALF_W + math.tan(diff_angle) * (WIDTH / (2 * math.tan(HALF_FOV))))

        # Rough occlusion: if a wall at this column is closer than the enemy, skip
        z_col = max(0, min(WIDTH-1, screen_x))
        if z_buffer[z_col] < perp_dist:
            continue

        sprite_h = max(1, int(HEIGHT / perp_dist))
        sprite_w = max(1, int(sprite_h * 0.5))

        # Off-screen cull
        if screen_x + sprite_w//2 < 0 or screen_x - sprite_w//2 >= WIDTH:
            continue

        vertical_shift = int(player.pitch * HALF_H)
        sprite_y = HALF_H - sprite_h // 2 + vertical_shift

        state = 'dead' if enemy.dead else enemy.state
        draw_enemy_sprite(screen, screen_x, sprite_y, sprite_h, state)

        # Award score when enemy was just killed (death_timer freshly set)
        if enemy.dead and abs(enemy.death_timer - ENEMY_DEATH_DISPLAY) < dt + 0.001:
            player.score += KILL_SCORE


# BULLET RENDERING
def draw_bullets(screen, player, z_buffer):
    vertical_shift = int(player.pitch * HALF_H)
    for b in bullets:
        dx = b.x - player.x
        dy = b.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            continue

        angle_to   = math.atan2(dy, dx)
        diff_angle = (angle_to - player.angle + math.pi) % (2*math.pi) - math.pi

        if abs(diff_angle) > HALF_FOV + 0.1:
            continue

        perp_dist = dist * math.cos(diff_angle)
        if perp_dist < 0.1:
            continue

        screen_x = int(HALF_W + math.tan(diff_angle) * (WIDTH / (2 * math.tan(HALF_FOV))))
        if not (0 <= screen_x < WIDTH):
            continue
        if z_buffer[screen_x] < perp_dist:
            continue

        size     = max(3, int(HEIGHT / perp_dist * 0.3))
        screen_y = HALF_H + vertical_shift
        pygame.draw.circle(screen, (255, 220, 50), (screen_x, screen_y), size)


# MINIMAP
def draw_minimap(screen, player):
    r    = MINIMAP_RADIUS
    sc   = MINIMAP_SCALE
    mm   = (r*2+1) * sc
    surf = pygame.Surface((mm, mm), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 160))

    cx, cy = int(player.x), int(player.y)
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            tx, ty = cx+dx, cy+dy
            px, py = (dx+r)*sc, (dy+r)*sc
            if 0 <= ty < MAP_H and 0 <= tx < MAP_W:
                color = (160, 30, 30, 220) if WORLD_MAP[ty][tx] != 0 else (40, 40, 40, 180)
            else:
                color = (10, 10, 10, 220)
            surf.fill(color, (px, py, sc, sc))

    # Enemy dots (green)
    for enemy in enemies:
        if not enemy.dead:
            ex = int((enemy.x - cx + r) * sc)
            ey = int((enemy.y - cy + r) * sc)
            if 0 <= ex < mm and 0 <= ey < mm:
                pygame.draw.rect(surf, (0, 255, 0, 220), (ex-2, ey-2, 5, 5))

    # Player position + facing line
    ppx, ppy = r*sc, r*sc
    pygame.draw.circle(surf, (255, 255, 255, 255), (ppx, ppy), 3)
    lx = int(ppx + math.cos(player.angle) * 5 * sc)
    ly = int(ppy + math.sin(player.angle) * 5 * sc)
    pygame.draw.line(surf, (255, 255, 255, 200), (ppx, ppy), (lx, ly), 1)

    screen.blit(surf, (WIDTH - mm - MINIMAP_MARGIN, MINIMAP_MARGIN))


# HUD
def draw_hud(screen, player, font):
    # Crosshair
    pygame.draw.line(screen, C_CROSSHAIR,
                        (HALF_W-10, HALF_H), (HALF_W+10, HALF_H), 2)
    pygame.draw.line(screen, C_CROSSHAIR,
                        (HALF_W, HALF_H-10), (HALF_W, HALF_H+10), 2)

    hp_col     = C_HEALTH if player.health < 30 else C_TEXT
    kills_left = max(0, (player.target_score - player.score) // KILL_SCORE)

    screen.blit(font.render(f"SCORE:  {player.score}",          True, C_TEXT),  (20,  20))
    screen.blit(font.render(f"HEALTH: {player.health}",         True, hp_col),  (20,  56))
    screen.blit(font.render(f"LEVEL:  {player.levels_cleared}", True, C_INFO),  (20,  92))
    screen.blit(font.render(f"KILLS TO NEXT: {kills_left}",     True, C_TEXT),  (20, 128))

    draw_minimap(screen, player)


# OVERLAY MESSAGES
def show_message(screen, font, lines, delay_ms=2000):
    #Draw a semi-transparent overlay with centred text lines then pause.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    for i, (text, colour) in enumerate(lines):
        surf = font.render(text, True, colour)
        rect = surf.get_rect(center=(HALF_W, HALF_H - 40 + i*50))
        screen.blit(surf, rect)

    pygame.display.flip()
    pygame.time.delay(delay_ms)


# LEVEL + GAME RESET
def new_level(player):
    #Generate a fresh map and respawn everything for the next level.
    enemies.clear()
    bullets.clear()
    generate_map()

    px, py = find_spawn()
    player.x     = px
    player.y     = py
    player.angle = best_facing_angle(px, py)
    player.pitch = 0.0

    # Paranoia: if somehow the chosen spawn is still inside a wall, try harder
    if not position_free(player.x, player.y):
        player.x, player.y = find_open_tile()

    spawn_enemies(30, player.x, player.y)


def reset_game(player):
    #Full reset after the player dies.
    player.health         = 100
    player.score          = 0
    player.levels_cleared = 0
    player.target_score   = LEVEL_SCORE
    new_level(player)


# MAIN LOOP
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Python DOOM")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Impact", 36)

    # Capture the mouse for free-look rotation
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    # First map + player
    generate_map()
    player = Player()
    px, py = find_spawn()
    player.x     = px
    player.y     = py
    player.angle = best_facing_angle(px, py)
    spawn_enemies(30, player.x, player.y)

    running = True
    while running:

        # Tick ONCE per frame – dt is in seconds 
        # BUG IN ORIGINAL: clock.tick() was called TWICE per loop iteration
        # (once at the top, once at the bottom).  This halved the effective
        # frame rate and made dt measurements unreliable.  Call it ONCE.
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)   # cap so physics don't explode on stutters

        # Events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if player.health > 0:
                        player.shoot()

            elif event.type == MUSIC_END:
                try:
                    pygame.mixer.music.load('soundtrack2.mp3')
                    pygame.mixer.music.play(-1)
                except Exception:
                    pass

        # Mouse look (rel_x is pixels moved since last call)
        rel_x, _ = pygame.mouse.get_rel()
        player.apply_mouse(rel_x)

        # Player movement + damage cooldown
        keys = pygame.key.get_pressed()
        if player.health > 0:
            player.move(keys, dt)
        player.tick_damage(dt)

        # Bullet updates
        for b in bullets:
            b.update()
        bullets[:] = [b for b in bullets if b.alive]

        # Render
        z_buffer = cast_rays(screen, player)                         # walls
        update_and_draw_enemies(screen, player, z_buffer, dt)        # enemies
        draw_bullets(screen, player, z_buffer)                       # bullets
        draw_hud(screen, player, font)                               # HUD + minimap

        # Level clear 
        if player.score >= player.target_score:
            show_message(screen, font,
                            [("LEVEL CLEARED!", (0, 255, 0)),
                            ("+50 HEALTH",      (0, 220, 100))],
                            delay_ms=2200)
            player.levels_cleared += 1
            player.score           = 0
            player.target_score   += 500
            player.health          = min(100, player.health + 50)
            new_level(player)
            continue

        # Death 
        if player.health <= 0:
            show_message(screen, font,
                            [("YOU DIED",                               (220, 40,  40)),
                            (f"LEVELS CLEARED: {player.levels_cleared}", C_TEXT)],
                            delay_ms=3000)
            reset_game(player)
            continue

        pygame.display.flip()
        # NOTE: NO second clock.tick() here.  The original had one at the
        # top AND one at the bottom, which is why timing was unreliable.

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()