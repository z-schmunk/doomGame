import pygame
import math
import sys
import random

# --- GAME SETTINGS ---
WIDTH, HEIGHT = 800, 600
HALF_WIDTH, HALF_HEIGHT = WIDTH // 2, HEIGHT // 2
FPS = 60
FOV = math.pi / 3  # 60 degree Field of View
HALF_FOV = FOV / 2
MAX_DEPTH = 20.0   # Maximum render distance
SPEED = 3.0        # Movement speed
ROTATION_SPEED = 0.05
PLAYER_RADIUS = 0.2 # keeps player from clipping

# --- COLORS ---
FLOOR_COLOR = (40, 40, 40)
CEILING_COLOR = (70, 70, 70)
WALL_COLOR = (180, 0, 0)      # Base color for walls
TARGET_COLOR = (0, 255, 0)    # Color for targets
TEXT_COLOR = (255, 255, 255)
CROSSHAIR_COLOR = (255, 255, 255)

MUSIC_END = pygame.USEREVENT + 1

# --- THE MAP ---
WORLD_MAP = []

def spawn_enemies(count, px=2.5, py=2.5):
    # Spawns enemies far away from the player's current location
    spawned = 0
    while spawned < count:
        x, y = random.randint(1, 18), random.randint(1, 18)
        
        # Calculate distance from player's current coordinates
        distance_from_player = math.hypot(x - px, y - py)
        
        # Ensure it's empty AND at least 8 map blocks away from the player
        if WORLD_MAP[y][x] == 0 and distance_from_player > 8.0:
            WORLD_MAP[y][x] = 2
            spawned += 1    #Spawns enemies in empty spaces, far away from the player's start (2.5, 2.5)

def generate_map():
    global WORLD_MAP
    # Create a large 20x20 empty room with solid borders
    WORLD_MAP = [[1 if i==0 or i==19 or j==0 or j==19 else 0 for j in range(20)] for i in range(20)]
    
    # Randomly scatter pillars/walls. Scattering ensures the map is 100% accessible
    for _ in range(40):
        x, y = random.randint(3, 18), random.randint(3, 18)
        WORLD_MAP[y][x] = 1
        
    spawn_enemies(8) # Start with 8 enemies on the map

generate_map() # Create the very first map

class Player:
    def __init__(self):
        self.x = 2.5 # Starting X in map coordinates
        self.y = 2.5 # Starting Y in map coordinates
        self.angle = 0
        self.score = 0
        self.health = 100
        self.levels_cleared = 0
        self.damage_cooldown = 0 # Cooldown timer to prevent taking damage every single frame when an enemy is shooting at you
        self.target_score = 1000
        
    # --- AUDIO SETUP ---
        pygame.mixer.init()
        try:
            self.shoot_sound = pygame.mixer.Sound('dspistol.wav')
            pygame.mixer.music.load('01._Hell_On_Earth.mp3')
            
            # Play the first track 0 times (meaning play it exactly once, no loops)
            pygame.mixer.music.play(0) 
            
            # Tell pygame to fire the MUSIC_END event when the song finishes
            pygame.mixer.music.set_endevent(MUSIC_END)
            
            self.has_audio = True
            print("Audio loaded successfully!")
        except FileNotFoundError:
            print("WARNING: Audio files missing. Game will run silently.")
            self.has_audio = False

    def handle_collision(self, dx, dy):
        # PERFECT COLLISION: Wall sliding mechanics
        # Check X axis
        if dx > 0: # Moving right
            if WORLD_MAP[int(self.y)][int(self.x + dx + PLAYER_RADIUS)] == 0 or WORLD_MAP[int(self.y)][int(self.x + dx + PLAYER_RADIUS)] == 2:
                self.x += dx
        else:      # Moving left
            if WORLD_MAP[int(self.y)][int(self.x + dx - PLAYER_RADIUS)] == 0 or WORLD_MAP[int(self.y)][int(self.x + dx - PLAYER_RADIUS)] == 2:
                self.x += dx

        # Check Y axis
        if dy > 0: # Moving down
            if WORLD_MAP[int(self.y + dy + PLAYER_RADIUS)][int(self.x)] == 0 or WORLD_MAP[int(self.y + dy + PLAYER_RADIUS)][int(self.x)] == 2:
                self.y += dy
        else:      # Moving up
            if WORLD_MAP[int(self.y + dy - PLAYER_RADIUS)][int(self.x)] == 0 or WORLD_MAP[int(self.y + dy - PLAYER_RADIUS)][int(self.x)] == 2:
                self.y += dy

    def move(self, keys):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        
        dx, dy = 0, 0
        speed = SPEED * 0.02 # Frame-adjusted speed

        # Forward / Backward
        if keys[pygame.K_w]:
            dx += cos_a * speed
            dy += sin_a * speed
        if keys[pygame.K_s]:
            dx -= cos_a * speed
            dy -= sin_a * speed
            
        # Strafe L / R
        if keys[pygame.K_a]: 
            dx += sin_a * speed
            dy -= cos_a * speed
        if keys[pygame.K_d]: 
            dx -= sin_a * speed
            dy += cos_a * speed

        self.handle_collision(dx, dy)

        # Turning
        if keys[pygame.K_LEFT]:
            self.angle -= ROTATION_SPEED
        if keys[pygame.K_RIGHT]:
            self.angle += ROTATION_SPEED

    def shoot(self):
        if self.has_audio:
            self.shoot_sound.play()
        
        # Raycast for shooting hit detection
        for depth in range(1, int(MAX_DEPTH * 10)):
            target_x = self.x + math.cos(self.angle) * (depth * 0.1)
            target_y = self.y + math.sin(self.angle) * (depth * 0.1)
            
            # Keep within bounds
            if 0 <= int(target_y) < len(WORLD_MAP) and 0 <= int(target_x) < len(WORLD_MAP[0]):
                tile = WORLD_MAP[int(target_y)][int(target_x)]
                
                if tile == 1:
                    # Hit a wall, bullet stops.
                    break
                elif tile == 2:
                    # Hit an enemy! Remove it, add points, and instantly respawn a new one
                    WORLD_MAP[int(target_y)][int(target_x)] = 0
                    self.score += 100
                    spawn_enemies(1, self.x, self.y) # Spawns away from current location
                    break

def draw_raycaster(screen, player):
    #The 3D engine
    # Draw ceiling and floor
    pygame.draw.rect(screen, CEILING_COLOR, (0, 0, WIDTH, HALF_HEIGHT))
    pygame.draw.rect(screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

    start_angle = player.angle - HALF_FOV
    
    for ray in range(WIDTH):
        ray_angle = start_angle + (ray / WIDTH) * FOV
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # Cast the ray step-by-step
        for depth in range(1, int(MAX_DEPTH * 20)):
            target_x = player.x + cos_a * (depth * 0.05)
            target_y = player.y + sin_a * (depth * 0.05)
            
            map_x, map_y = int(target_x), int(target_y)
            
            if 0 <= map_y < len(WORLD_MAP) and 0 <= map_x < len(WORLD_MAP[0]):
                tile = WORLD_MAP[map_y][map_x]
                if tile != 0:
                    # Calculate distance
                    distance = depth * 0.05
                    distance *= math.cos(player.angle - ray_angle) 
                    
                    # Prevent division by zero
                    distance = max(distance, 0.0001) 
                    
                    # Calculate wall height on screen
                    wall_height = (HEIGHT / distance)
                    
                    # Depth shading (farther = darker)
                    shade = max(0, min(255, 255 - int(distance * 15)))
                    
                    if tile == 1:
                        color = (shade, 0, 0) # Red wall
                    elif tile == 2:
                        color = (0, shade, 0) # Green target
                        # ENEMY SHOOTING BACK: Use cooldown to prevent instant death
                        if distance < 8.0 and player.damage_cooldown == 0: 
                            if random.random() < 0.05: # 5% chance to hit
                                player.health -= 5     # Take 5 damage
                                player.damage_cooldown = 30 # Wait before taking damage again
                        
                    # Draw the vertical slice of the wall
                    pygame.draw.line(screen, color, 
                                     (ray, HALF_HEIGHT - wall_height // 2), 
                                     (ray, HALF_HEIGHT + wall_height // 2), 1)
                    break

def draw_ui(screen, player, font):
    # Crosshair
    pygame.draw.line(screen, CROSSHAIR_COLOR, (HALF_WIDTH - 10, HALF_HEIGHT), (HALF_WIDTH + 10, HALF_HEIGHT), 2)
    pygame.draw.line(screen, CROSSHAIR_COLOR, (HALF_WIDTH, HALF_HEIGHT - 10), (HALF_WIDTH, HALF_HEIGHT + 10), 2)
    
    # Score, health, and levels cleared
    score_text = font.render(f"SCORE: {player.score}", True, TEXT_COLOR)
    health_text = font.render(f"HEALTH: {player.health}", True, (255, 0, 0) if player.health < 30 else TEXT_COLOR)
    levels_text = font.render(f"LEVELS CLEARED: {player.levels_cleared}", True, (0, 200, 255))
    
    screen.blit(score_text, (20, 20))
    screen.blit(health_text, (20, 60))
    screen.blit(levels_text, (20, 100))

    if player.health <= 0:
        dead_text = font.render("YOU DIED", True, (255, 0, 0))
        screen.blit(dead_text, (HALF_WIDTH - 150, HALF_HEIGHT - 50))    # Crosshair
    pygame.draw.line(screen, CROSSHAIR_COLOR, (HALF_WIDTH - 10, HALF_HEIGHT), (HALF_WIDTH + 10, HALF_HEIGHT), 2)
    pygame.draw.line(screen, CROSSHAIR_COLOR, (HALF_WIDTH, HALF_HEIGHT - 10), (HALF_WIDTH, HALF_HEIGHT + 10), 2)
    
    screen.blit(score_text, (20, 20))
    screen.blit(health_text, (20, 60))

    if player.health <= 0:
        dead_text = font.render("YOU DIED", True, (255, 0, 0))
        screen.blit(dead_text, (HALF_WIDTH - 60, HALF_HEIGHT - 50))    # Crosshair
    pygame.draw.line(screen, CROSSHAIR_COLOR, (HALF_WIDTH - 10, HALF_HEIGHT), (HALF_WIDTH + 10, HALF_HEIGHT), 2)
    pygame.draw.line(screen, CROSSHAIR_COLOR, (HALF_WIDTH, HALF_HEIGHT - 10), (HALF_WIDTH, HALF_HEIGHT + 10), 2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Python Doom")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Impact", 36)

    player = Player()

    running = True
    while running:
        # 1. Handle events (quitting, shooting, and music changes)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.shoot()
            elif event.type == MUSIC_END:
                try:
                    pygame.mixer.music.load('soundtrack2.mp3')
                    pygame.mixer.music.play(-1)
                except FileNotFoundError:
                    pass

        # 2. Handle continuous movement & cooldowns
        keys = pygame.key.get_pressed()
        player.move(keys)
        
        if player.damage_cooldown > 0:
            player.damage_cooldown -= 1

        # 3. Check game state (level ups) before drawing
        if player.score >= player.target_score:
            # 1. Draw the screen once so the player sees their score hit 1000!
            draw_raycaster(screen, player)
            draw_ui(screen, player, font)
            
            # 2. Centered level-Up text
            win_text = font.render("LEVEL CLEARED!", True, (0, 255, 0)) # Green text
            reward_text = font.render("+50 HEALTH", True, (0, 255, 0))
            screen.blit(win_text, (HALF_WIDTH - 110, HALF_HEIGHT - 50))
            screen.blit(reward_text, (HALF_WIDTH - 85, HALF_HEIGHT - 10))
            
            # 3. Update the display and pause
            pygame.display.flip()
            pygame.time.delay(2000) 
            
            # 4. Reset in the background
            player.levels_cleared += 1
            generate_map()
            player.x, player.y = 2.5, 2.5
            player.score = 0
            player.target_score += 500
            player.health += 50
            if player.health > 100: player.health = 100
            
            continue # Start the new level perfectly clean
            
        # 4. Check death state before drawing
        if player.health <= 0:
            # Draw the death screen once
            draw_raycaster(screen, player)
            draw_ui(screen, player, font)
            pygame.display.flip()
            
            pygame.time.delay(3000) # Wait 3 seconds
            
            # --- RESET THE GAME ---
            player.health = 100
            player.score = 0
            player.levels_cleared = 0
            player.x, player.y = 2.5, 2.5
            generate_map()
            continue # Restart fresh

        # 5. Draw everything (normal frame)
        draw_raycaster(screen, player)
        draw_ui(screen, player, font)

        # 6. Update screen
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()