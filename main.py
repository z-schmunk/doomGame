import os
import pygame
import math
import sys
import random

# GAME SETTINGS
WIDTH, HEIGHT   = 800, 600
HALF_W, HALF_H  = WIDTH // 2, HEIGHT // 2
FPS             = 60
FOV             = math.pi / 3
HALF_FOV        = FOV / 2
MAX_DEPTH       = 20.0
MOVE_SPEED      = 0.05
ROT_SPEED       = 0.03
MOUSE_SENS      = 0.002
PLAYER_RADIUS   = 0.25
PITCH_STEP      = 0.02
PITCH_MAX       = 0.45

# Minimap
MINIMAP_RADIUS  = 8
MINIMAP_SCALE   = 4
MINIMAP_MARGIN  = 10

# Enemy constants
ENEMY_HIT_RADIUS    = 0.4
ENEMY_ATTACK_RANGE  = 12.0
ENEMY_DAMAGE        = 5
ENEMY_ATTACK_RATE   = 1.5
ENEMY_DEATH_DISPLAY = 0.7
BULLET_SPEED        = 0.18
ENEMY_BULLET_SPEED  = 0.25
ENEMY_BULLET_RADIUS = 0.25

# Enemy movement
ENEMY_MOVE_SPEED    = 0.02
ENEMY_CHASE_RANGE   = 18.0
ENEMY_STOP_RANGE    = 3.0
ENEMY_PATH_INTERVAL = 0.4

# Scoring
KILL_SCORE  = 100
LEVEL_SCORE = 1000

# COLOURS
C_CEILING   = (20,  20,  20)
C_FLOOR     = (15,  15,  15)
C_WALL      = (190, 40,  40)
C_TEXT      = (255, 255, 255)
C_CROSSHAIR = (255, 255, 255)
C_HEALTH    = (255,  60,  60)
C_INFO      = (  0, 200, 255)

# GLOBALS
WORLD_MAP     = []
MAP_W         = 0
MAP_H         = 0
ROOM_CENTERS  = []
enemies       = []
bullets       = []
enemy_bullets = []

MUSIC_END = pygame.USEREVENT + 1


# MAP HELPERS
def tile_is_wall(mx, my):
    if my < 0 or my >= MAP_H or mx < 0 or mx >= MAP_W:
        return True
    return WORLD_MAP[my][mx] != 0

def tile_is_open(mx, my):
    return not tile_is_wall(mx, my)


# MAP GENERATION
def carve_maze(size):
    maze = [[1] * size for _ in range(size)]
    for y in range(1, size - 1, 2):
        for x in range(1, size - 1, 2):
            maze[y][x] = 0
    stack   = [(1, 1)]
    visited = {(1, 1)}
    while stack:
        x, y = stack[-1]
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
    global WORLD_MAP, MAP_W, MAP_H, ROOM_CENTERS
    size = 50
    WORLD_MAP    = carve_maze(size)
    MAP_W        = size
    MAP_H        = size
    ROOM_CENTERS = []
    placed = []
    for _ in range(30):
        if len(placed) >= 10: break
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
        for _ in range(min(3, len(ROOM_CENTERS)-1)):
            a, b = random.sample(ROOM_CENTERS, 2)
            carve_corridor(a[0], a[1], b[0], b[1])
    if len(ROOM_CENTERS) >= 2:
        src = ROOM_CENTERS[0]
        for dst in ROOM_CENTERS[1:]:
            if not bfs_connected(src[0], src[1], dst[0], dst[1]):
                carve_corridor(src[0], src[1], dst[0], dst[1])
    if not ROOM_CENTERS:
        carve_rect(2, 2, 8, 8)
        ROOM_CENTERS.append((6, 6))


# COLLISION
def position_free(px, py):
    if tile_is_wall(int(px), int(py)):
        return False
    for dx, dy in ((PLAYER_RADIUS, 0), (-PLAYER_RADIUS, 0),
                    (0, PLAYER_RADIUS), (0, -PLAYER_RADIUS)):
        if tile_is_wall(int(px+dx), int(py+dy)):
            return False
    return True

def slide_move(px, py, dx, dy):
    nx, ny = px+dx, py+dy
    if position_free(nx, ny): return nx, ny
    if position_free(px+dx, py): return px+dx, py
    if position_free(px, py+dy): return px, py+dy
    return px, py


# PATHFINDING
def bfs_next_step(sx, sy, gx, gy):
    # BFS from enemy tile to player tile, returns the first tile to step into
    start = (sx, sy)
    goal  = (gx, gy)
    if start == goal: return None
    parent = {start: None}
    queue  = [start]
    found  = False
    while queue:
        curr = queue.pop(0)
        if curr == goal:
            found = True
            break
        cx, cy = curr
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb = (cx+dx, cy+dy)
            if nb not in parent and tile_is_open(nb[0], nb[1]):
                parent[nb] = curr
                queue.append(nb)
    if not found: return None
    node = goal
    while parent[node] != start:
        node = parent[node]
        if node is None: return None
    return node


# SPAWN HELPERS
def find_open_tile():
    for _ in range(2000):
        x = random.randint(1, MAP_W-2)
        y = random.randint(1, MAP_H-2)
        if WORLD_MAP[y][x] != 0: continue
        open_nb = sum(1 for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),
                                        (-1,-1),(1,-1),(-1,1),(1,1))
                        if tile_is_open(x+dx, y+dy))
        if open_nb >= 5:
            return x+0.5, y+0.5
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
            best_score = avg
            best_angle = angle
    return best_angle

def find_spawn(min_dist_from=None, min_dist=8.0):
    for _ in range(2000):
        x = random.randint(1, MAP_W-2)
        y = random.randint(1, MAP_H-2)
        if WORLD_MAP[y][x] != 0: continue
        px, py = x + 0.5, y + 0.5
        if min_dist_from is not None and math.hypot(px-min_dist_from[0], py-min_dist_from[1]) < min_dist:
            continue
        if position_free(px, py):
            return px, py
    return find_open_tile()


# ENEMY
class Enemy:
    def __init__(self, x, y):
        self.x           = x
        self.y           = y
        self.alive       = True
        self.dead        = False
        self.state       = 'idle'
        self.dmg_timer   = 0.0
        self.death_timer = 0.0
        self.path_timer  = 0.0
        self.waypoint    = None

def spawn_enemies(count, avoid_x, avoid_y):
    for _ in range(count * 40):
        if sum(1 for e in enemies if not e.dead) >= count: break
        px, py = find_spawn(min_dist_from=(avoid_x, avoid_y), min_dist=8.0)
        if any(math.hypot(px - e.x, py - e.y) < 1.0 for e in enemies if not e.dead):
            continue
        enemies.append(Enemy(px, py))


# BULLETS
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
        if tile_is_wall(int(self.x), int(self.y)):
            self.alive = False
            return
        for enemy in enemies:
            if enemy.alive and math.hypot(enemy.x-self.x, enemy.y-self.y) < ENEMY_HIT_RADIUS:
                enemy.alive       = False
                enemy.dead        = True
                enemy.state       = 'dead'
                enemy.death_timer = ENEMY_DEATH_DISPLAY
                self.alive        = False
                return

class EnemyBullet:
    def __init__(self, x, y, angle):
        self.x     = x
        self.y     = y
        self.dx    = math.cos(angle) * ENEMY_BULLET_SPEED
        self.dy    = math.sin(angle) * ENEMY_BULLET_SPEED
        self.alive = True

    def update(self, player):
        self.x += self.dx
        self.y += self.dy
        if tile_is_wall(int(self.x), int(self.y)):
            self.alive = False
            return
        if math.hypot(self.x - player.x, self.y - player.y) < ENEMY_BULLET_RADIUS:
            player.take_hit(ENEMY_DAMAGE)
            self.alive = False


# PLAYER
class Player:
    def __init__(self):
        self.x            = 2.5
        self.y            = 2.5
        self.angle        = 0.0
        self.pitch        = 0.0
        self.health       = 100
        self.score        = 0
        self.levels_cleared = 0
        self.target_score = LEVEL_SCORE
        self.dmg_cooldown = 0.0
        self.has_audio    = False
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
        fwd  = ( MOVE_SPEED if keys[pygame.K_w] else
                -MOVE_SPEED if keys[pygame.K_s] else 0)
        side = ( MOVE_SPEED if keys[pygame.K_d] else
                -MOVE_SPEED if keys[pygame.K_a] else 0)
        dx = cos_a * fwd - sin_a * side
        dy = sin_a * fwd + cos_a * side
        self.x, self.y = slide_move(self.x, self.y, dx, dy)
        if keys[pygame.K_LEFT]:  self.angle -= ROT_SPEED
        if keys[pygame.K_RIGHT]: self.angle += ROT_SPEED
        if keys[pygame.K_q] or keys[pygame.K_PAGEUP]:
            self.pitch = min(PITCH_MAX, self.pitch + PITCH_STEP)
        if keys[pygame.K_e] or keys[pygame.K_PAGEDOWN]:
            self.pitch = max(-PITCH_MAX, self.pitch - PITCH_STEP)
        self.angle %= (2 * math.pi)

    def apply_mouse(self, rel_x):
        self.angle += rel_x * MOUSE_SENS
        self.angle %= (2 * math.pi)

    def tick_damage(self, dt):
        if self.dmg_cooldown > 0:
            self.dmg_cooldown = max(0.0, self.dmg_cooldown - dt)

    def take_hit(self, amount):
        if self.dmg_cooldown <= 0:
            self.health       = max(0, self.health - amount)
            self.dmg_cooldown = 1.0


# RAYCASTER (DDA)
def cast_rays(screen, player):
    vertical_shift = int(player.pitch * HALF_H)
    pygame.draw.rect(screen, C_CEILING, (0, 0, WIDTH, HALF_H + vertical_shift))
    pygame.draw.rect(screen, C_FLOOR,   (0, HALF_H + vertical_shift, WIDTH, HEIGHT))
    z_buffer = [MAX_DEPTH] * WIDTH
    for col in range(WIDTH):
        camera_x  = 2.0 * col / WIDTH - 1.0
        plane_len = math.tan(HALF_FOV)
        dir_x     = math.cos(player.angle)
        dir_y     = math.sin(player.angle)
        plane_x   = -dir_y * plane_len
        plane_y   =  dir_x * plane_len
        ray_dx    = dir_x + plane_x * camera_x
        ray_dy    = dir_y + plane_y * camera_x
        map_x     = int(player.x)
        map_y     = int(player.y)
        delta_x   = abs(1.0 / ray_dx) if ray_dx != 0.0 else 1e30
        delta_y   = abs(1.0 / ray_dy) if ray_dy != 0.0 else 1e30
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
        hit  = False
        side = 0
        for _ in range(int(MAX_DEPTH * 3)):
            if side_dx < side_dy:
                side_dx += delta_x
                map_x   += step_x
                side     = 0
            else:
                side_dy += delta_y
                map_y   += step_y
                side     = 1
            if map_y < 0 or map_y >= MAP_H or map_x < 0 or map_x >= MAP_W:
                break
            if WORLD_MAP[map_y][map_x] != 0:
                hit = True
                break
        if not hit: continue
        if side == 0:
            perp_dist = (map_x - player.x + (1 - step_x) / 2) / ray_dx
        else:
            perp_dist = (map_y - player.y + (1 - step_y) / 2) / ray_dy
        perp_dist     = max(perp_dist, 0.05)
        z_buffer[col] = perp_dist
        wall_h        = int(HEIGHT / perp_dist)
        draw_top      = max(0, HALF_H - wall_h // 2 + vertical_shift)
        draw_bot      = min(HEIGHT-1, HALF_H + wall_h // 2 + vertical_shift)
        shade_factor  = 0.65 if side == 1 else 1.0
        dist_factor   = max(0.0, 1.0 - perp_dist / MAX_DEPTH)
        brightness    = shade_factor * dist_factor
        color = (
            max(0, min(255, int(C_WALL[0] * brightness))),
            max(0, min(255, int(C_WALL[1] * brightness))),
            max(0, min(255, int(C_WALL[2] * brightness))),
        )
        pygame.draw.line(screen, color, (col, draw_top), (col, draw_bot))
    return z_buffer


# DUCK
def draw_duck(surface, cx, cy, size, y_spin_angle):
    # y_spin_angle in radians drives horizontal squish (fake Y-axis rotation)
    x_scale = abs(math.cos(y_spin_angle))  # 1.0 = full width, 0.0 = edge-on
    flip    = math.cos(y_spin_angle) < 0   # mirror when past 90 degrees

    s      = max(1, size)
    body_w = max(4, int(s * 1.8 * x_scale))
    body_h = max(3, int(s * 1.2))
    head_r  = max(2, int(s * 0.7 * x_scale))

    # Body (ellipse)
    if body_w > 1:
        pygame.draw.ellipse(surface, (255, 255, 255),
                            (cx - body_w, cy - body_h // 2, body_w * 2, body_h))

    # Head — offset direction flips with rotation side
    head_offset = int(body_w * (0.6 if not flip else -0.6))
    head_cx = cx + head_offset
    head_cy = cy - body_h // 2
    if head_r > 1:
        pygame.draw.circle(surface, (255, 255, 255), (head_cx, head_cy), head_r)

    # Bill — only draw when wide enough to be visible
    if x_scale > 0.15:
        bill_w = max(2, int(s * 0.7 * x_scale))
        bill_h = max(1, int(s * 0.35))
        bill_dir = 1 if not flip else -1
        pygame.draw.rect(surface, (255, 165, 0),
                         (head_cx + bill_dir * (head_r - 1),
                          head_cy - bill_h // 2, bill_dir * bill_w, bill_h))

    # Eye
    if head_r > 2 and x_scale > 0.2:
        eye_offset = int(max(1, head_r // 2) * (1 if not flip else -1))
        pygame.draw.circle(surface, (0, 0, 0),
                           (head_cx + eye_offset, head_cy - max(1, head_r // 3)),
                           max(1, int(s * 0.18 * x_scale)))

    # Wing
    wing_w = max(2, int(s * 0.9 * x_scale))
    wing_h = max(1, int(s * 0.5))
    if wing_w > 1:
        pygame.draw.ellipse(surface, (200, 200, 210),
                            (cx - wing_w // 2, cy - wing_h // 2, wing_w, wing_h))

    # Tail — flips side with rotation
    tail_dir = -1 if not flip else 1
    tail_tip = (cx + tail_dir * body_w,       cy)
    tail_top = (cx + tail_dir * (body_w - 2), cy - max(2, int(s * 0.6)))
    tail_bot = (cx + tail_dir * (body_w - 2), cy + max(2, int(s * 0.6)))
    if body_w > 2:
        pygame.draw.polygon(surface, (220, 220, 220), [tail_tip, tail_top, tail_bot])


# ENEMY SPRITE
def draw_enemy_sprite(screen, cx, cy, size, state):
    if state == 'dead':
        body_col = (60, 0, 0)
    elif state == 'attack':
        body_col = (240, 50, 50)
    elif state == 'chase':
        body_col = (200, 80, 20)
    else:
        body_col = (140, 20, 20)
    bw = max(14, int(size * 0.32))
    bh = max(24, int(size * 0.65))
    hr = max(8,  int(size * 0.15))
    lh = max(8,  int(size * 0.18))
    bx = int(cx - bw/2)
    by = int(cy + hr)
    pygame.draw.rect(screen, body_col, (bx, by, bw, bh))
    head_col = tuple(min(255, c+70) for c in body_col)
    pygame.draw.circle(screen, head_col, (int(cx), int(cy + hr)), hr)
    pygame.draw.circle(screen, (255,255,255), (int(cx), int(cy + hr)), max(2, hr//4))
    pygame.draw.line(screen, (30,0,0), (bx+4, by+bh), (bx+4, by+bh+lh), 2)
    pygame.draw.line(screen, (30,0,0), (bx+bw-4, by+bh), (bx+bw-4, by+bh+lh), 2)


# ENEMY AI + RENDERING
def update_and_draw_enemies(screen, player, z_buffer, dt):
    for enemy in list(enemies):

        if enemy.dead:
            enemy.death_timer -= dt
            if enemy.death_timer <= 0:
                enemies.remove(enemy)
                continue

        else:
            dx   = enemy.x - player.x
            dy   = enemy.y - player.y
            dist = math.hypot(dx, dy)

            has_los = False
            if dist <= ENEMY_CHASE_RANGE:
                steps   = max(1, int(dist / 0.15))
                cos_dir = dx / dist if dist > 0 else 0
                sin_dir = dy / dist if dist > 0 else 0
                blocked = False
                for k in range(1, steps):
                    tx = player.x + cos_dir * (k * 0.15)
                    ty = player.y + sin_dir * (k * 0.15)
                    if tile_is_wall(int(tx), int(ty)):
                        blocked = True
                        break
                has_los = not blocked

            if dist > ENEMY_CHASE_RANGE:
                enemy.state    = 'idle'
                enemy.waypoint = None

            elif has_los and dist <= ENEMY_STOP_RANGE:
                enemy.state    = 'attack'
                enemy.waypoint = None
                enemy.dmg_timer -= dt
                if enemy.dmg_timer <= 0:
                    angle_to_player = math.atan2(player.y - enemy.y, player.x - enemy.x)
                    spread = random.uniform(-0.05, 0.05)
                    enemy_bullets.append(EnemyBullet(enemy.x, enemy.y, angle_to_player + spread))
                    enemy.dmg_timer = ENEMY_ATTACK_RATE

            else:
                enemy.state = 'chase'
                at_waypoint = (enemy.waypoint is None or
                                math.hypot(enemy.x - enemy.waypoint[0],
                                            enemy.y - enemy.waypoint[1]) < 0.5)
                enemy.path_timer -= dt
                if enemy.path_timer <= 0 or at_waypoint:
                    enemy.path_timer = ENEMY_PATH_INTERVAL
                    next_tile = bfs_next_step(int(enemy.x), int(enemy.y),
                                                int(player.x), int(player.y))
                    if next_tile is not None:
                        enemy.waypoint = (next_tile[0] + 0.5, next_tile[1] + 0.5)
                    else:
                        enemy.waypoint = (player.x, player.y)

                if enemy.waypoint is not None:
                    wx, wy = enemy.waypoint
                    wdx    = wx - enemy.x
                    wdy    = wy - enemy.y
                    wdist  = math.hypot(wdx, wdy)
                    if wdist > 0.01:
                        step   = ENEMY_MOVE_SPEED
                        new_x, new_y = slide_move(enemy.x, enemy.y,
                                                   (wdx / wdist) * step,
                                                   (wdy / wdist) * step)
                        enemy.x = new_x
                        enemy.y = new_y

                if has_los and dist <= ENEMY_ATTACK_RANGE:
                    enemy.dmg_timer -= dt
                    if enemy.dmg_timer <= 0:
                        angle_to_player = math.atan2(player.y - enemy.y, player.x - enemy.x)
                        spread = random.uniform(-0.05, 0.05)
                        enemy_bullets.append(EnemyBullet(enemy.x, enemy.y, angle_to_player + spread))
                        enemy.dmg_timer = ENEMY_ATTACK_RATE

        dx = enemy.x - player.x
        dy = enemy.y - player.y
        angle_to   = math.atan2(dy, dx)
        diff_angle = (angle_to - player.angle + math.pi) % (2*math.pi) - math.pi
        if abs(diff_angle) > HALF_FOV + 0.3: continue
        perp_dist = math.hypot(dx, dy) * math.cos(diff_angle)
        if perp_dist < 0.1: continue
        screen_x = int(HALF_W + math.tan(diff_angle) * (WIDTH / (2 * math.tan(HALF_FOV))))
        z_col = max(0, min(WIDTH-1, screen_x))
        if z_buffer[z_col] < perp_dist: continue
        sprite_h = max(1, int(HEIGHT / perp_dist))
        sprite_w = max(1, int(sprite_h * 0.5))
        if screen_x + sprite_w//2 < 0 or screen_x - sprite_w//2 >= WIDTH: continue
        vertical_shift = int(player.pitch * HALF_H)
        sprite_y = HALF_H - sprite_h // 2 + vertical_shift
        state = 'dead' if enemy.dead else enemy.state
        draw_enemy_sprite(screen, screen_x, sprite_y, sprite_h, state)
        if enemy.dead and abs(enemy.death_timer - ENEMY_DEATH_DISPLAY) < dt + 0.001:
            player.score += KILL_SCORE


# PLAYER BULLET RENDERING (spinning duck)
def draw_bullets(screen, player, z_buffer, duck_frame):
    vertical_shift = int(player.pitch * HALF_H)
    for b in bullets:
        dx = b.x - player.x
        dy = b.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.1: continue
        angle_to   = math.atan2(dy, dx)
        diff_angle = (angle_to - player.angle + math.pi) % (2*math.pi) - math.pi
        if abs(diff_angle) > HALF_FOV + 0.1: continue
        perp_dist = dist * math.cos(diff_angle)
        if perp_dist < 0.1: continue
        screen_x = int(HALF_W + math.tan(diff_angle) * (WIDTH / (2 * math.tan(HALF_FOV))))
        if not (0 <= screen_x < WIDTH): continue
        if z_buffer[screen_x] < perp_dist: continue
        size     = max(4, int(HEIGHT / perp_dist * 0.3))
        screen_y = HALF_H + vertical_shift

        # Draw the duck onto a transparent surface then rotate it as one unit.
        # Without this intermediate surface, rotating individual primitives
        # drawn directly to the screen would spin around separate fixed points.
        duck_size = size * 2
        duck_surf = pygame.Surface((duck_size * 3, duck_size * 2), pygame.SRCALPHA)
        y_spin_angle = (duck_frame / 20) * 2 * math.pi   # full Y rotation cycle
        draw_duck(duck_surf, duck_surf.get_width() // 2, duck_surf.get_height() // 2,
                size, y_spin_angle)
        screen.blit(duck_surf, duck_surf.get_rect(center=(screen_x, screen_y)))


# ENEMY BULLET RENDERING
def update_and_draw_enemy_bullets(screen, player, z_buffer):
    vertical_shift = int(player.pitch * HALF_H)
    for b in list(enemy_bullets):
        b.update(player)
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    for b in enemy_bullets:
        dx = b.x - player.x
        dy = b.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.1: continue
        angle_to   = math.atan2(dy, dx)
        diff_angle = (angle_to - player.angle + math.pi) % (2*math.pi) - math.pi
        if abs(diff_angle) > HALF_FOV + 0.1: continue
        perp_dist = dist * math.cos(diff_angle)
        if perp_dist < 0.1: continue
        screen_x = int(HALF_W + math.tan(diff_angle) * (WIDTH / (2 * math.tan(HALF_FOV))))
        if not (0 <= screen_x < WIDTH): continue
        if z_buffer[screen_x] < perp_dist: continue
        size     = max(3, int(HEIGHT / perp_dist * 0.3))
        screen_y = HALF_H + vertical_shift
        pygame.draw.circle(screen, (255, 100, 0), (screen_x, screen_y), size)


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
    for enemy in enemies:
        if not enemy.dead:
            ex = int((enemy.x - cx + r) * sc)
            ey = int((enemy.y - cy + r) * sc)
            if 0 <= ex < mm and 0 <= ey < mm:
                pygame.draw.rect(surf, (0, 255, 0, 220), (ex-2, ey-2, 5, 5))
    ppx, ppy = r*sc, r*sc
    pygame.draw.circle(surf, (255, 255, 255, 255), (ppx, ppy), 3)
    lx = int(ppx + math.cos(player.angle) * 5 * sc)
    ly = int(ppy + math.sin(player.angle) * 5 * sc)
    pygame.draw.line(surf, (255, 255, 255, 200), (ppx, ppy), (lx, ly), 1)
    screen.blit(surf, (WIDTH - mm - MINIMAP_MARGIN, MINIMAP_MARGIN))


# HUD
def draw_hud(screen, player, font):
    pygame.draw.line(screen, C_CROSSHAIR, (HALF_W-10, HALF_H), (HALF_W+10, HALF_H), 2)
    pygame.draw.line(screen, C_CROSSHAIR, (HALF_W, HALF_H-10), (HALF_W, HALF_H+10), 2)
    hp_col     = C_HEALTH if player.health < 30 else C_TEXT
    kills_left = max(0, (player.target_score - player.score) // KILL_SCORE)
    screen.blit(font.render(f"SCORE:  {player.score}",          True, C_TEXT), (20,  20))
    screen.blit(font.render(f"HEALTH: {player.health}",         True, hp_col), (20,  56))
    screen.blit(font.render(f"LEVEL:  {player.levels_cleared}", True, C_INFO), (20,  92))
    screen.blit(font.render(f"KILLS TO NEXT: {kills_left}",     True, C_TEXT), (20, 128))
    draw_minimap(screen, player)


# OVERLAY MESSAGES
def show_message(screen, font, lines, delay_ms=2000):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))
    for i, (text, colour) in enumerate(lines):
        surf = font.render(text, True, colour)
        rect = surf.get_rect(center=(HALF_W, HALF_H - 40 + i*50))
        screen.blit(surf, rect)
    pygame.display.flip()
    pygame.time.delay(delay_ms)


# LEVEL / RESET
def new_level(player):
    enemies.clear()
    bullets.clear()
    enemy_bullets.clear()
    generate_map()
    px, py = find_spawn()
    player.x     = px
    player.y     = py
    player.angle = best_facing_angle(px, py)
    player.pitch = 0.0
    if not position_free(player.x, player.y):
        player.x, player.y = find_open_tile()
    spawn_enemies(50, player.x, player.y)

def reset_game(player):
    player.health         = 100
    player.score          = 0
    player.levels_cleared = 0
    player.target_score   = LEVEL_SCORE
    new_level(player)


# MAIN
def main():
    pygame.init()

    # duck_frame increments each tick to drive the spin angle in draw_bullets.
    # DUCK_FRAME_RATE controls how fast it increments (lower = faster spin).
    DUCK_FRAME_RATE = 0.05
    duck_timer      = 0.0
    duck_frame      = 0

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Python DOOM")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Impact", 36)

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    generate_map()
    player = Player()
    px, py = find_spawn()
    player.x     = px
    player.y     = py
    player.angle = best_facing_angle(px, py)
    spawn_enemies(30, player.x, player.y)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        duck_timer += dt
        if duck_timer >= DUCK_FRAME_RATE:
            duck_timer  = 0.0
            duck_frame  = (duck_frame + 1) % 20

        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if player.health > 0:
                        player.shoot()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and player.health > 0:
                    player.shoot()
            elif event.type == MUSIC_END:
                try:
                    pygame.mixer.music.load('soundtrack2.mp3')
                    pygame.mixer.music.play(-1)
                except Exception:
                    pass

        rel_x, _ = pygame.mouse.get_rel()
        player.apply_mouse(rel_x)

        keys = pygame.key.get_pressed()
        if player.health > 0:
            player.move(keys, dt)
        player.tick_damage(dt)

        for b in bullets:
            b.update()
        bullets[:] = [b for b in bullets if b.alive]

        z_buffer = cast_rays(screen, player)
        update_and_draw_enemies(screen, player, z_buffer, dt)
        draw_bullets(screen, player, z_buffer, duck_frame)
        update_and_draw_enemy_bullets(screen, player, z_buffer)
        draw_hud(screen, player, font)

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

        if player.health <= 0:
            show_message(screen, font,
                            [("YOU DIED",                                 (220, 40,  40)),
                            (f"LEVELS CLEARED: {player.levels_cleared}", C_TEXT)],
                            delay_ms=3000)
            reset_game(player)
            continue

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()