import pygame
import sys
import math
import random
from pygame.locals import *

# Constants
SCALE = 2
TILE = 16
WIDTH = int(300 * SCALE)
HEIGHT = int(200 * SCALE)
FPS = 60

# Yoshi's Island DS Palette (bright, vibrant colors)
YOSHI_PALETTE = [
    (255, 241, 232),  # Light cream (background)
    (197, 223, 214),  # Light blue (sky)
    (255, 200, 200),  # Light pink
    (255, 150, 150),  # Pink
    (255, 100, 100),  # Red
    (180, 220, 120),  # Light green
    (120, 200, 80),   # Green
    (80, 160, 60),    # Dark green
    (200, 180, 120),  # Light brown
    (160, 140, 80),   # Brown
    (120, 100, 60),   # Dark brown
    (180, 180, 180),  # Light gray
    (100, 100, 100),  # Gray
    (50, 50, 50),     # Dark gray
    (0, 0, 0),        # Black
]

# Game State
class GameState:
    def __init__(self):
        self.slot = 0
        self.progress = [{"world": "1-1"}, {"world": "1-1"}, {"world": "1-1"}]
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.world = "1-1"
        self.time = 300
        self.mario_size = "small"  # "small" or "big"

state = GameState()

# Scene management
SCENES = []

def push(scene): SCENES.append(scene)
def pop(): SCENES.pop()

class Scene:
    def handle(self, events, keys): ...
    def update(self, dt): ...
    def draw(self, surf): ...

# Generate 32 levels
def generate_level_data(world):
    levels = {}
    for world_num in range(1, 9):
        for level_num in range(1, 5):  # 4 levels per world
            level_id = f"{world_num}-{level_num}"
            level = []
            
            # Sky
            for i in range(10):
                level.append(" " * 100)
                
            # Platforms
            for i in range(10, 15):
                level.append(" " * 100)
                
            # Ground
            for i in range(15, 20):
                if i == 15:
                    row = "G" * 100
                else:
                    row = "B" * 100
                level.append(row)
            
            # Add platforms
            for i in range(5):
                platform_y = random.randint(8, 12)
                platform_x = random.randint(10 + i*20, 15 + i*20)
                length = random.randint(4, 8)
                for j in range(length):
                    level[platform_y] = level[platform_y][:platform_x+j] + "P" + level[platform_y][platform_x+j+1:]
            
            # Add pipes
            for i in range(2):
                pipe_x = random.randint(20 + i*30, 25 + i*30)
                pipe_height = random.randint(2, 4)
                for j in range(pipe_height):
                    level[19-j] = level[19-j][:pipe_x] + "T" + level[19-j][pipe_x+1:]
                    level[19-j] = level[19-j][:pipe_x+1] + "T" + level[19-j][pipe_x+2:]
            
            # Add bricks and question blocks
            for i in range(8):
                block_y = random.randint(5, 10)
                block_x = random.randint(5 + i*10, 8 + i*10)
                block_type = "?" if random.random() > 0.5 else "B"
                level[block_y] = level[block_y][:block_x] + block_type + level[block_y][block_x+1:]
            
            # Add player start
            level[14] = level[14][:5] + "S" + level[14][6:]
            
            # Add flag at end
            level[14] = level[14][:95] + "F" + level[14][96:]
            
            # Add enemies
            for i in range(5):
                enemy_y = 14
                enemy_x = random.randint(20 + i*15, 25 + i*15)
                enemy_type = "G" if random.random() > 0.3 else "K"
                level[enemy_y] = level[enemy_y][:enemy_x] + enemy_type + level[enemy_y][enemy_x+1:]
            
            levels[level_id] = level
    
    return levels

LEVELS = generate_level_data("1-1")

# Create thumbnails
THUMBNAILS = {}
for level_id, level_data in LEVELS.items():
    thumb = pygame.Surface((32, 24))
    thumb.fill(YOSHI_PALETTE[1])  # Sky blue
    # Draw a simple representation of the level
    for y, row in enumerate(level_data[10:14]):
        for x, char in enumerate(row[::3]):  # Sample every 3rd column
            if char in ("G", "B", "P", "T"):
                thumb.set_at((x, y+10), YOSHI_PALETTE[8])  # Brown
            elif char in ("?", "B"):
                thumb.set_at((x, y+10), YOSHI_PALETTE[4])  # Red
    THUMBNAILS[level_id] = thumb

# Entity classes
class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = TILE
        self.height = TILE
        self.on_ground = False
        self.facing_right = True
        self.active = True
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def check_collision(self, other):
        return self.get_rect().colliderect(other.get_rect())
        
    def update(self, colliders, dt):
        # Apply gravity
        if not self.on_ground:
            self.vy += 0.5 * dt * 60
            
        # Update position
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        
        # Check collision with ground
        self.on_ground = False
        for rect in colliders:
            if self.get_rect().colliderect(rect):
                # Bottom collision
                if self.vy > 0 and self.y + self.height > rect.top and self.y < rect.top:
                    self.y = rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                # Top collision
                elif self.vy < 0 and self.y < rect.bottom and self.y + self.height > rect.bottom:
                    self.y = rect.bottom
                    self.vy = 0
                # Left collision
                if self.vx > 0 and self.x + self.width > rect.left and self.x < rect.left:
                    self.x = rect.left - self.width
                    self.vx = 0
                # Right collision
                elif self.vx < 0 and self.x < rect.right and self.x + self.width > rect.right:
                    self.x = rect.right
                    self.vx = 0
                    
    def draw(self, surf, cam):
        pass

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.jump_power = -5
        self.move_speed = 2
        self.invincible = 0
        self.animation_frame = 0
        self.walk_timer = 0
        self.pre_rendered = None
        
    def update(self, colliders, dt, enemies):
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vx = 0
        if keys[K_LEFT]:
            self.vx = -self.move_speed
            self.facing_right = False
        if keys[K_RIGHT]:
            self.vx = self.move_speed
            self.facing_right = True
            
        # Jumping
        if keys[K_SPACE] and self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
            
        # Update walk animation
        if self.vx != 0:
            self.walk_timer += dt
            if self.walk_timer > 0.1:
                self.walk_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 3
        else:
            self.animation_frame = 0
            
        # Update invincibility
        if self.invincible > 0:
            self.invincible -= dt
            
        super().update(colliders, dt)
        
        # Check collision with enemies
        for enemy in enemies:
            if enemy.active and self.check_collision(enemy):
                # Jumped on enemy
                if self.vy > 0 and self.y + self.height - 5 < enemy.y:
                    enemy.active = False
                    self.vy = self.jump_power / 2
                    state.score += 100
                # Hit by enemy
                elif self.invincible <= 0:
                    if state.mario_size == "big":
                        state.mario_size = "small"
                        self.invincible = 2
                    else:
                        state.lives -= 1
                        if state.lives <= 0:
                            # Game over
                            push(GameOverScene())
                        else:
                            # Reset position
                            self.x = 50
                            self.y = 100
                            self.vx = 0
                            self.vy = 0
                    
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return  # Blink during invincibility
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Draw Mario based on size
        if state.mario_size == "big":
            # Pre-render to surface for performance
            if not self.pre_rendered:
                self.pre_rendered = pygame.Surface((TILE, TILE * 2), pygame.SRCALPHA)
                # Body
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[4], (4, 8, 8, 16))  # Red
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[5], (5, 9, 6, 14))  # Highlight
                
                # Head
                pygame.draw.circle(self.pre_rendered, YOSHI_PALETTE[2], (8, 6), 6)  # Face
                pygame.draw.circle(self.pre_rendered, YOSHI_PALETTE[0], (8, 6), 5)  # Highlight
                
                # Hat
                pygame.draw.rect(self.pre_rendered, YOSHI_PALETTE[4], (2, 0, 12, 4))  # Red hat
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[5], (3, 1, 10, 3))  # Highlight
                
                # Arms
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[2], (0, 10, 4, 6))  # Left arm
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[0], (0, 10, 4, 6), 1)  # Outline
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[2], (12, 10, 4, 6))  # Right arm
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[0], (12, 10, 4, 6), 1)  # Outline
                
                # Legs
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[6], (2, 24, 4, 8))  # Left leg
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[0], (2, 24, 4, 8), 1)  # Outline
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[6], (10, 24, 4, 8))  # Right leg
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[0], (10, 24, 4, 8), 1)  # Outline
            
            # Draw pre-rendered surface
            surf.blit(self.pre_rendered, (x, y))
        else:
            # Small Mario
            # Pre-render to surface for performance
            if not self.pre_rendered:
                self.pre_rendered = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                # Body
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[4], (4, 8, 8, 8))  # Red
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[5], (5, 9, 6, 6))  # Highlight
                
                # Head
                pygame.draw.circle(self.pre_rendered, YOSHI_PALETTE[2], (8, 4), 4)  # Face
                pygame.draw.circle(self.pre_rendered, YOSHI_PALETTE[0], (8, 4), 3)  # Highlight
                
                # Hat
                pygame.draw.rect(self.pre_rendered, YOSHI_PALETTE[4], (2, 0, 12, 2))  # Red hat
                pygame.draw.ellipse(self.pre_rendered, YOSHI_PALETTE[5], (3, 1, 10, 1))  # Highlight
            
            # Draw pre-rendered surface
            surf.blit(self.pre_rendered, (x, y))

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.walk_timer = 0
        self.pre_rendered = [None, None]
        
    def update(self, colliders, dt):
        # Turn around at edges
        if self.on_ground:
            # Check for edge
            edge_check = pygame.Rect(self.x + (self.width if self.vx > 0 else -1), 
                                    self.y + self.height, 
                                    1, 1)
            edge_found = False
            for rect in colliders:
                if edge_check.colliderect(rect):
                    edge_found = True
                    break
                    
            if not edge_found:
                self.vx *= -1
                
        super().update(colliders, dt)
        
        # Update animation
        self.walk_timer += dt
        if self.walk_timer > 0.2:
            self.walk_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
            
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Pre-render frames for performance
        if not self.pre_rendered[0]:
            for frame in range(2):
                surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                # Body
                pygame.draw.ellipse(surface, YOSHI_PALETTE[8], (2, 4, 12, 12))  # Brown
                pygame.draw.ellipse(surface, YOSHI_PALETTE[9], (3, 5, 10, 10))  # Highlight
                
                # Feet
                foot_offset = 0 if frame == 0 else 2
                pygame.draw.ellipse(surface, YOSHI_PALETTE[10], (2, 14, 4, 2))  # Left foot
                pygame.draw.ellipse(surface, YOSHI_PALETTE[10], (10, 14 + foot_offset, 4, 2))  # Right foot
                
                # Eyes
                pygame.draw.ellipse(surface, YOSHI_PALETTE[0], (4, 6, 2, 2))  # Left eye
                pygame.draw.ellipse(surface, YOSHI_PALETTE[0], (10, 6, 2, 2))  # Right eye
                
                # Outline
                pygame.draw.ellipse(surface, YOSHI_PALETTE[14], (2, 4, 12, 12), 1)  # Outline
                
                self.pre_rendered[frame] = surface
                
        surf.blit(self.pre_rendered[self.animation_frame], (x, y))

class Koopa(Goomba):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.shell_mode = False
        self.pre_rendered = [None, None]
        
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Pre-render frames for performance
        if not self.pre_rendered[0]:
            for frame in range(2):
                surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                # Shell
                pygame.draw.ellipse(surface, YOSHI_PALETTE[6], (2, 4, 12, 12))  # Green
                pygame.draw.ellipse(surface, YOSHI_PALETTE[7], (3, 5, 10, 10))  # Highlight
                
                # Head and feet
                if not self.shell_mode:
                    pygame.draw.ellipse(surface, YOSHI_PALETTE[2], (4, 0, 8, 6))  # Head
                    pygame.draw.ellipse(surface, YOSHI_PALETTE[10], (2, 14, 4, 2))  # Left foot
                    pygame.draw.ellipse(surface, YOSHI_PALETTE[10], (10, 14 + (2 if frame == 0 else 0), 4, 2))  # Right foot
                
                # Outline
                pygame.draw.ellipse(surface, YOSHI_PALETTE[14], (2, 4, 12, 12), 1)  # Outline
                
                self.pre_rendered[frame] = surface
                
        surf.blit(self.pre_rendered[self.animation_frame], (x, y))

# Pre-rendered tile images for performance
TILE_IMAGES = {}
def create_tile_images():
    global TILE_IMAGES
    # Ground top
    img = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.rect(img, YOSHI_PALETTE[6], (0, 0, TILE, TILE))  # Green
    pygame.draw.rect(img, YOSHI_PALETTE[7], (0, 0, TILE, 4))  # Darker top
    # Dots
    for i in range(3):
        pygame.draw.circle(img, YOSHI_PALETTE[5], (i*5+4, 10), 1)  # Light dots
    TILE_IMAGES["G"] = img
    
    # Brown block
    img = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.rect(img, YOSHI_PALETTE[8], (0, 0, TILE, TILE))  # Brown
    pygame.draw.rect(img, YOSHI_PALETTE[9], (2, 2, TILE-4, TILE-4))  # Highlight
    # Dots
    for i in range(2):
        for j in range(2):
            pygame.draw.circle(img, YOSHI_PALETTE[10], (i*8+4, j*8+4), 1)  # Dark dots
    TILE_IMAGES["B"] = img
    
    # Platform
    img = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.rect(img, YOSHI_PALETTE[8], (0, 0, TILE, TILE))  # Brown
    pygame.draw.rect(img, YOSHI_PALETTE[9], (0, 0, TILE, 2))  # Top edge
    TILE_IMAGES["P"] = img
    
    # Pipe
    img = pygame.Surface((TILE*2, TILE), pygame.SRCALPHA)
    pygame.draw.rect(img, YOSHI_PALETTE[6], (0, 0, TILE*2, TILE))  # Green
    pygame.draw.rect(img, YOSHI_PALETTE[7], (2, 2, TILE*2-4, TILE-4))  # Highlight
    pygame.draw.rect(img, YOSHI_PALETTE[5], (4, 4, TILE*2-8, TILE-8))  # Light highlight
    TILE_IMAGES["T"] = img
    
    # Question block
    img = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.rect(img, YOSHI_PALETTE[3], (0, 0, TILE, TILE))  # Yellow
    pygame.draw.rect(img, YOSHI_PALETTE[4], (2, 2, TILE-4, TILE-4))  # Highlight
    # Question mark
    pygame.draw.circle(img, YOSHI_PALETTE[14], (TILE//2, TILE//2), 3)  # Dot
    pygame.draw.line(img, YOSHI_PALETTE[14], (TILE//2, TILE//2-3), (TILE//2, TILE//2+3), 2)  # Line
    TILE_IMAGES["?"] = img
    
    # Flag
    img = pygame.Surface((TILE, TILE*4), pygame.SRCALPHA)
    # Pole
    pygame.draw.rect(img, YOSHI_PALETTE[11], (6, 0, 4, TILE*4))  # Gray
    # Flag
    points = [(10, 0), (20, 8), (10, 16)]
    pygame.draw.polygon(img, YOSHI_PALETTE[4], points)  # Red flag
    pygame.draw.polygon(img, YOSHI_PALETTE[14], points, 1)  # Outline
    TILE_IMAGES["F"] = img

create_tile_images()

class TileMap:
    def __init__(self, level_data):
        self.tiles = []
        self.colliders = []
        self.width = len(level_data[0]) * TILE
        self.height = len(level_data) * TILE
        self.static_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Parse level data
        for y, row in enumerate(level_data):
            for x, char in enumerate(row):
                if char != " ":
                    rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    self.tiles.append((x * TILE, y * TILE, char))
                    
                    if char in ("G", "B", "P", "T", "?"):
                        self.colliders.append(rect)
        
        # Pre-render the entire map for performance
        self.static_surface.fill((0, 0, 0, 0))  # Transparent
        for x, y, char in self.tiles:
            if char == "T":  # Pipe is 2 tiles wide
                self.static_surface.blit(TILE_IMAGES[char], (x, y))
            elif char == "F":  # Flag is 4 tiles tall
                self.static_surface.blit(TILE_IMAGES[char], (x, y))
            else:
                self.static_surface.blit(TILE_IMAGES[char], (x, y))
    
    def draw(self, surf, cam):
        # Draw sky with gradient
        for y in range(HEIGHT):
            # Create gradient from light blue to white
            color = (
                max(50, int(YOSHI_PALETTE[1][0] * (1 - y/HEIGHT))),
                max(50, int(YOSHI_PALETTE[1][1] * (1 - y/HEIGHT))),
                max(50, int(YOSHI_PALETTE[1][2] * (1 - y/HEIGHT)))
            )
            pygame.draw.line(surf, color, (0, y), (WIDTH, y))
        
        # Draw clouds (simple circles)
        for i in range(10):
            x = (i * 80 + int(cam/3)) % (self.width + 200) - 100
            y = 30 + (i % 3) * 20
            pygame.draw.ellipse(surf, YOSHI_PALETTE[0], (x, y, 30, 15))
            pygame.draw.ellipse(surf, YOSHI_PALETTE[0], (x+15, y-5, 25, 15))
        
        # Draw pre-rendered tiles
        visible_rect = pygame.Rect(cam, 0, WIDTH, HEIGHT)
        surf.blit(self.static_surface, (-cam, 0), visible_rect)

# Scenes
class TitleScreen(Scene):
    def __init__(self):
        self.timer = 0
        self.animation_frame = 0
        self.logo_y = -50
        self.logo_target_y = HEIGHT // 2 - 60
        self.logo = self.create_logo()
        
    def create_logo(self):
        # Pre-render the logo for performance
        logo = pygame.Surface((240, 100), pygame.SRCALPHA)
        # Box
        pygame.draw.rect(logo, YOSHI_PALETTE[0], (0, 0, 240, 100), border_radius=10)
        pygame.draw.rect(logo, YOSHI_PALETTE[4], (4, 4, 232, 92), border_radius=8)
        
        # Title
        font = pygame.font.SysFont(None, 32)
        title = font.render("KOOPA ENGINE 1.0A", True, YOSHI_PALETTE[0])
        logo.blit(title, (120 - title.get_width()//2, 15))
        
        # Subtitle
        font = pygame.font.SysFont(None, 16)
        subtitle = font.render("Tech demo", True, YOSHI_PALETTE[14])
        logo.blit(subtitle, (120 - subtitle.get_width()//2, 50))
        return logo
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN and e.key == K_RETURN:
                push(FileSelect())
                
    def update(self, dt):
        self.timer += dt
        if self.timer > 0.1:
            self.timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
        # Animate logo coming down
        if self.logo_y < self.logo_target_y:
            self.logo_y += 3
            
    def draw(self, surf):
        # Background with gradient
        for y in range(HEIGHT):
            color = (
                max(50, int(YOSHI_PALETTE[1][0] * (1 - y/HEIGHT))),
                max(50, int(YOSHI_PALETTE[1][1] * (1 - y/HEIGHT))),
                max(50, int(YOSHI_PALETTE[1][2] * (1 - y/HEIGHT)))
            )
            pygame.draw.line(surf, color, (0, y), (WIDTH, y))
        
        # Draw logo
        surf.blit(self.logo, (WIDTH//2 - 120, self.logo_y))
        
        # Copyright
        font = pygame.font.SysFont(None, 14)
        copyright = font.render("[C] Team Flames 20XX [1985] - Nintendo", True, YOSHI_PALETTE[14])
        surf.blit(copyright, (WIDTH//2 - copyright.get_width()//2, self.logo_y + 110))
        
        # Press Start
        if self.logo_y >= self.logo_target_y and int(self.timer * 10) % 2 == 0:
            font = pygame.font.SysFont(None, 24)
            text = font.render("PRESS ENTER", True, YOSHI_PALETTE[0])
            surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 30))

class FileSelect(Scene):
    def __init__(self):
        self.offset = 0
        self.selected = 0
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key in (K_1, K_2, K_3):
                    self.selected = e.key - K_1
                elif e.key == K_RETURN:
                    state.slot = self.selected
                    state.world = state.progress[state.slot]["world"]
                    push(LevelScene(state.world))
                elif e.key == K_ESCAPE:
                    push(TitleScreen())
                    
    def update(self, dt):
        self.offset += dt
        
    def draw(self, s):
        # Background with gradient
        for y in range(HEIGHT):
            color = (
                max(50, int(YOSHI_PALETTE[1][0] * (1 - y/HEIGHT))),
                max(50, int(YOSHI_PALETTE[1][1] * (1 - y/HEIGHT))),
                max(50, int(YOSHI_PALETTE[1][2] * (1 - y/HEIGHT)))
            )
            pygame.draw.line(s, color, (0, y), (WIDTH, y))
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render("SELECT PLAYER", True, YOSHI_PALETTE[4])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw file slots
        for i in range(3):
            x = 50 + i * 100
            y = 90 + 5 * math.sin(self.offset * 3 + i)
            
            # Slot background
            pygame.draw.rect(s, YOSHI_PALETTE[8], (x-5, y-5, 50, 70), border_radius=5)
            pygame.draw.rect(s, YOSHI_PALETTE[9], (x, y, 40, 60), border_radius=4)
            
            # Slot number
            slot_font = pygame.font.SysFont(None, 20)
            slot_text = slot_font.render(f"{i+1}", True, YOSHI_PALETTE[0])
            s.blit(slot_text, (x+18, y+5))
            
            # Selection indicator
            if i == self.selected:
                pygame.draw.rect(s, YOSHI_PALETTE[4], (x-2, y-2, 44, 64), 2, border_radius=5)
                
            # World preview
            if state.progress[i]:
                world = state.progress[i]["world"]
                world_font = pygame.font.SysFont(None, 16)
                world_text = world_font.render(f"WORLD {world}", True, YOSHI_PALETTE[0])
                s.blit(world_text, (x+20 - world_text.get_width()//2, y+50))
                
                # Draw thumbnail
                thumb = THUMBNAILS.get(world, THUMBNAILS["1-1"])
                s.blit(thumb, (x+4, y+20))

class LevelScene(Scene):
    def __init__(self, level_id):
        self.map = TileMap(LEVELS[level_id])
        self.player = Player(50, 100)
        self.enemies = []
        self.cam = 0.0
        self.level_id = level_id
        self.time = 300
        self.coins = 0
        self.end_level = False
        self.end_timer = 0
        self.mushrooms = []
        
        # Parse level for enemies and player start
        for y, row in enumerate(LEVELS[level_id]):
            for x, char in enumerate(row):
                if char == "S":
                    self.player.x = x * TILE
                    self.player.y = y * TILE
                elif char == "G":
                    self.enemies.append(Goomba(x * TILE, y * TILE))
                elif char == "K":
                    self.enemies.append(Koopa(x * TILE, y * TILE))
    
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                push(FileSelect())
                
    def update(self, dt):
        # Update time
        self.time -= dt
        
        # Update player
        self.player.update(self.map.colliders, dt, self.enemies)
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.update(self.map.colliders, dt)
        
        # Camera follow player
        target = self.player.x - WIDTH // 2
        self.cam += (target - self.cam) * 0.1
        self.cam = max(0, min(self.cam, self.map.width - WIDTH))
        
        # Check for end of level
        if self.player.x > self.map.width - 100 and not self.end_level:
            self.end_level = True
            self.end_timer = 3  # 3 seconds to show end sequence
            
        if self.end_level:
            self.end_timer -= dt
            if self.end_timer <= 0:
                # Advance to next level
                world, level = self.level_id.split("-")
                level = int(level)
                if level < 4:
                    next_level = f"{world}-{level+1}"
                else:
                    world = int(world) + 1
                    if world > 8:
                        push(WinScreen())
                        return
                    next_level = f"{world}-1"
                
                state.world = next_level
                state.progress[state.slot]["world"] = next_level
                push(LevelScene(next_level))
        
    def draw(self, s):
        # Draw map
        self.map.draw(s, self.cam)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(s, self.cam)
            
        # Draw player
        self.player.draw(s, self.cam)
        
        # Draw HUD with rounded corners
        pygame.draw.rect(s, YOSHI_PALETTE[14], (0, 0, WIDTH, 20), border_radius=3)
        pygame.draw.rect(s, YOSHI_PALETTE[9], (2, 2, WIDTH-4, 16), border_radius=2)
        
        # Score
        font = pygame.font.SysFont(None, 16)
        score_text = font.render(f"SCORE {state.score:06d}", True, YOSHI_PALETTE[0])
        s.blit(score_text, (10, 4))
        
        # Coins
        coin_text = font.render(f"COINS {state.coins:02d}", True, YOSHI_PALETTE[0])
        s.blit(coin_text, (WIDTH//2 - coin_text.get_width()//2, 4))
        
        # World
        world_text = font.render(f"WORLD {self.level_id}", True, YOSHI_PALETTE[0])
        s.blit(world_text, (WIDTH - world_text.get_width() - 10, 4))
        
        # Time
        time_text = font.render(f"TIME {int(self.time):03d}", True, YOSHI_PALETTE[0])
        s.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 4))
        
        # Lives
        lives_text = font.render(f"x{state.lives}", True, YOSHI_PALETTE[0])
        s.blit(lives_text, (WIDTH - 60, 4))
        # Draw small mario for lives indicator
        small_mario = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(small_mario, YOSHI_PALETTE[4], (0, 4, 8, 8))
        pygame.draw.ellipse(small_mario, YOSHI_PALETTE[2], (0, 0, 8, 8))
        s.blit(small_mario, (WIDTH - 80, 6))

class GameOverScene(Scene):
    def __init__(self):
        self.timer = 3
        
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            pop()  # Back to file select
            state.lives = 3
            state.score = 0
            
    def draw(self, s):
        s.fill(YOSHI_PALETTE[4])
        font = pygame.font.SysFont(None, 40)
        text = font.render("GAME OVER", True, YOSHI_PALETTE[0])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
        
        font = pygame.font.SysFont(None, 20)
        text = font.render(f"FINAL SCORE: {state.score}", True, YOSHI_PALETTE[0])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 20))

class WinScreen(Scene):
    def __init__(self):
        self.timer = 5
        self.fireworks = []
        
    def update(self, dt):
        self.timer -= dt
        
        # Add fireworks
        if random.random() < 0.2:
            self.fireworks.append({
                "x": random.randint(50, WIDTH-50),
                "y": HEIGHT,
                "size": random.randint(20, 40),
                "color": random.choice([YOSHI_PALETTE[3], YOSHI_PALETTE[4], YOSHI_PALETTE[5]]),
                "particles": []
            })
            
        # Update fireworks
        for fw in self.fireworks[:]:
            fw["y"] -= 3
            if fw["y"] < HEIGHT//3:
                # Explode
                for i in range(20):
                    angle = random.uniform(0, math.pi*2)
                    speed = random.uniform(2, 5)
                    fw["particles"].append({
                        "x": fw["x"],
                        "y": fw["y"],
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "life": 1.0
                    })
                self.fireworks.remove(fw)
                
        # Update particles
        for fw in self.fireworks:
            for p in fw["particles"][:]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.1
                p["life"] -= 0.02
                if p["life"] <= 0:
                    fw["particles"].remove(p)
                    
        if self.timer <= 0:
            push(TitleScreen())
            
    def draw(self, s):
        s.fill(YOSHI_PALETTE[1])
        
        # Draw fireworks
        for fw in self.fireworks:
            pygame.draw.circle(s, YOSHI_PALETTE[0], (int(fw["x"]), int(fw["y"])), 3)
            for p in fw["particles"]:
                alpha = int(p["life"] * 255)
                color = fw["color"]
                pygame.draw.circle(s, color, (int(p["x"]), int(p["y"])), 2)
        
        # Text
        font = pygame.font.SysFont(None, 40)
        text = font.render("CONGRATULATIONS!", True, YOSHI_PALETTE[4])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 50))
        
        font = pygame.font.SysFont(None, 30)
        text = font.render("YOU SAVED THE PRINCESS!", True, YOSHI_PALETTE[4])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 100))
        
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"FINAL SCORE: {state.score}", True, YOSHI_PALETTE[4])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 150))

# Main game
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("KOOPA ENGINE 1.0A Tech Demo")
clock = pygame.time.Clock()

# Start with title screen
push(TitleScreen())

while SCENES:
    dt = clock.tick(FPS) / 1000
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    
    # Handle quit events
    for e in events:
        if e.type == QUIT:
            pygame.quit()
            sys.exit()
    
    # Update current scene
    scene = SCENES[-1]
    scene.handle(events, keys)
    scene.update(dt)
    scene.draw(screen)
    
    pygame.display.flip()

pygame.quit()
sys.exit()
