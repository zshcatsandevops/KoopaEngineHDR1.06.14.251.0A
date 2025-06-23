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

# NES Palette
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), 
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0), 
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), 
    (0, 50, 60), (0, 0, 0), (152, 150, 152), (8, 76, 196), 
    (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), 
    (152, 34, 32), (120, 60, 0), (84, 90, 0), (40, 114, 0), 
    (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), 
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), 
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32), 
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), 
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0)
]

# Game State
class GameState:
    def __init__(self):
        self.slot = 0
        self.progress = [
            {"world": "1-1", "completed": set(), "powerups": set(), "boss_defeated": False}, 
            {"world": "1-1", "completed": set(), "powerups": set(), "boss_defeated": False}, 
            {"world": "1-1", "completed": set(), "powerups": set(), "boss_defeated": False}
        ]
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.world = "1-1"
        self.time = 300
        self.mario_size = "small"  # "small", "big", "fire"
        self.powerup_active = False
        self.powerup_type = None
        self.paused = False

state = GameState()

# Scene management
SCENES = []

def push(scene): SCENES.append(scene)
def pop(): 
    if SCENES: 
        return SCENES.pop()
    return None

class Scene:
    def handle(self, events, keys): ...
    def update(self, dt): ...
    def draw(self, surf): ...

# World themes
WORLD_THEMES = {
    "1": {"name": "Mushroom Plains", "bg": 27, "ground": 20, "block": 21, "enemies": ["G", "K"]},
    "2": {"name": "Sandy Dunes", "bg": 26, "ground": 33, "block": 21, "enemies": ["G", "P"]},
    "3": {"name": "Coral Cove", "bg": 29, "ground": 24, "block": 25, "enemies": ["C", "S"]},
    "4": {"name": "Frozen Falls", "bg": 31, "ground": 39, "block": 38, "enemies": ["G", "S"]},
    "5": {"name": "Cloudy Heights", "bg": 27, "ground": 31, "block": 39, "enemies": ["G", "P"]},
    "6": {"name": "Rocky Mountains", "bg": 21, "ground": 33, "block": 21, "enemies": ["K", "P"]},
    "7": {"name": "Twisted Forest", "bg": 13, "ground": 14, "block": 15, "enemies": ["G", "T"]},
    "8": {"name": "Bowser's Domain", "bg": 1, "ground": 33, "block": 21, "enemies": ["K", "F"]}
}

# Generate 32 levels with distinct types
def generate_level_data():
    levels = {}
    
    # Level types for each world
    level_types = {
        "1": ["plains", "plains", "plains", "castle"],
        "2": ["desert", "desert", "desert", "castle"],
        "3": ["beach", "underwater", "coral", "castle"],
        "4": ["ice", "ice_cave", "snow", "castle"],
        "5": ["clouds", "sky", "airship", "castle"],
        "6": ["caves", "mountains", "mine", "castle"],
        "7": ["forest", "swamp", "haunted", "castle"],
        "8": ["volcano", "lava", "fortress", "castle"]
    }
    
    for world_num in range(1, 9):
        world_str = str(world_num)
        for level_num in range(1, 5):  # 4 levels per world
            level_id = f"{world_num}-{level_num}"
            level_type = level_types[world_str][level_num-1]
            
            # Create level based on type
            level = []
            level_height = 20
            
            # Sky/background
            for i in range(level_height):
                level.append(" " * 100)
                
            # Get theme colors
            theme = WORLD_THEMES[world_str]
            
            # Different level types
            if level_type == "plains":
                # Plains level - open with platforms
                # Ground
                for i in range(15, level_height):
                    if i == 15:
                        row = "G" * 100
                    else:
                        row = "B" * 100
                    level[i] = row
                
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
            
            elif level_type == "desert":
                # Desert level - sand and pyramids
                # Sand ground
                for i in range(15, level_height):
                    if i == 15:
                        row = "S" * 100
                    else:
                        row = "D" * 100
                    level[i] = row
                
                # Add pyramids
                pyramid_x = [20, 60]
                for px in pyramid_x:
                    height = 5
                    width = 1
                    for y in range(15-height, 15):
                        row = " " * (px - width) + "P" * (width*2+1) + " " * (100 - px - width - 1)
                        level[y] = row
                        width += 1
                
                # Add quicksand
                for i in range(3):
                    qs_x = random.randint(30 + i*20, 40 + i*20)
                    qs_width = random.randint(3, 6)
                    level[15] = level[15][:qs_x] + "Q" * qs_width + level[15][qs_x+qs_width:]
                
                # Add cacti
                for i in range(4):
                    cactus_x = random.randint(10 + i*20, 15 + i*20)
                    cactus_height = random.randint(3, 5)
                    for j in range(cactus_height):
                        level[15-j] = level[15-j][:cactus_x] + "C" + level[15-j][cactus_x+1:]
            
            elif level_type == "underwater":
                # Underwater level - water physics
                # Water ground
                for i in range(15, level_height):
                    if i == 15:
                        row = "G" * 100
                    else:
                        row = "B" * 100
                    level[i] = row
                
                # Add seaweed
                for i in range(8):
                    weed_x = random.randint(5 + i*12, 10 + i*12)
                    weed_height = random.randint(3, 6)
                    for j in range(weed_height):
                        level[15-j] = level[15-j][:weed_x] + "W" + level[15-j][weed_x+1:]
                
                # Add coral
                for i in range(5):
                    coral_x = random.randint(15 + i*15, 20 + i*15)
                    coral_y = 14
                    level[coral_y] = level[coral_y][:coral_x] + "C" + level[coral_y][coral_x+1:]
            
            elif level_type == "ice":
                # Ice level - slippery surfaces
                # Ice ground
                for i in range(15, level_height):
                    if i == 15:
                        row = "I" * 100
                    else:
                        row = "B" * 100
                    level[i] = row
                
                # Add ice blocks
                for i in range(6):
                    block_y = random.randint(5, 10)
                    block_x = random.randint(5 + i*15, 10 + i*15)
                    level[block_y] = level[block_y][:block_x] + "B" + level[block_y][block_x+1:]
                
                # Add slopes
                slope_x = [30, 70]
                for sx in slope_x:
                    height = 3
                    for y in range(15-height, 15):
                        level[y] = level[y][:sx] + "/" * (15-y) + level[y][sx+(15-y):]
            
            elif level_type == "castle":
                # Castle level - brick structures with lava and boss
                # Ground
                for i in range(15, level_height):
                    if i == 15:
                        level[i] = "G" * 100
                    else:
                        level[i] = "B" * 100
                
                # Add lava pits
                for i in range(3):
                    pit_x = random.randint(20 + i*25, 30 + i*25)
                    pit_width = random.randint(4, 8)
                    for x in range(pit_width):
                        if pit_x + x < 100:
                            level[15] = level[15][:pit_x+x] + "L" + level[15][pit_x+x+1:]
                            level[16] = level[16][:pit_x+x] + "L" + level[16][pit_x+x+1:]
                
                # Add brick structures
                for i in range(5):
                    struct_x = random.randint(10 + i*15, 15 + i*15)
                    struct_height = random.randint(4, 8)
                    struct_width = random.randint(2, 4)
                    
                    for y in range(15 - struct_height, 15):
                        for x in range(struct_width):
                            if struct_x + x < 100:
                                level[y] = level[y][:struct_x+x] + "B" + level[y][struct_x+x+1:]
                
                # Add platforms
                for i in range(3):
                    platform_y = random.randint(8, 12)
                    platform_x = random.randint(20 + i*25, 25 + i*25)
                    length = random.randint(3, 5)
                    for j in range(length):
                        level[platform_y] = level[platform_y][:platform_x+j] + "P" + level[platform_y][platform_x+j+1:]
                
                # Add question blocks
                for i in range(4):
                    block_y = random.randint(5, 10)
                    block_x = random.randint(10 + i*20, 15 + i*20)
                    level[block_y] = level[block_y][:block_x] + "?" + level[block_y][block_x+1:]
                
                # Add boss at the end
                level[10] = level[10][:90] + "X" + level[10][91:]
            
            # Add player start
            level[14] = level[14][:5] + "S" + level[14][6:]
            
            # Add flag at end
            level[14] = level[14][:95] + "F" + level[14][96:]
            
            # Add enemies
            enemy_types = theme["enemies"]
            for i in range(5):
                enemy_y = 14
                enemy_x = random.randint(20 + i*15, 25 + i*15)
                enemy_type = random.choice(enemy_types)
                level[enemy_y] = level[enemy_y][:enemy_x] + enemy_type + level[enemy_y][enemy_x+1:]
            
            # Add coins
            for i in range(10):
                coin_y = random.randint(5, 12)
                coin_x = random.randint(10 + i*8, 15 + i*8)
                level[coin_y] = level[coin_y][:coin_x] + "O" + level[coin_y][coin_x+1:]
            
            levels[level_id] = (level, theme)
    
    return levels

LEVELS = generate_level_data()

# Create thumbnails
THUMBNAILS = {}
for level_id, (level_data, theme) in LEVELS.items():
    thumb = pygame.Surface((32, 24))
    thumb.fill(NES_PALETTE[theme["bg"]])
    # Draw a simple representation of the level
    for y, row in enumerate(level_data[10:14]):
        for x, char in enumerate(row[::3]):  # Sample every 3rd column
            if char in ("G", "S", "I", "B", "P", "T", "L"):
                thumb.set_at((x, y+10), NES_PALETTE[theme["ground"]])
            elif char in ("?", "B"):
                thumb.set_at((x, y+10), NES_PALETTE[theme["block"]])
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
        self.run_speed = 3.5
        self.invincible = 0
        self.animation_frame = 0
        self.walk_timer = 0
        self.fireballs = []
        self.fire_cooldown = 0
        self.star_timer = 0
        self.underwater = False
        
    def update(self, colliders, dt, enemies, items):
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Current speed (running if shift pressed)
        current_speed = self.run_speed if keys[K_LSHIFT] else self.move_speed
        
        # Horizontal movement
        self.vx = 0
        if keys[K_LEFT]:
            self.vx = -current_speed
            self.facing_right = False
        if keys[K_RIGHT]:
            self.vx = current_speed
            self.facing_right = True
            
        # Jumping
        if keys[K_SPACE] and self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
            
        # Fireballs
        if keys[K_z] and state.mario_size == "fire" and self.fire_cooldown <= 0:
            self.fireballs.append(Fireball(self.x, self.y, self.facing_right))
            self.fire_cooldown = 0.5
            
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
            
        # Update fireballs
        for fb in self.fireballs[:]:
            fb.update(colliders, dt)
            if not fb.active:
                self.fireballs.remove(fb)
                
        # Update star timer
        if self.star_timer > 0:
            self.star_timer -= dt
            if self.star_timer <= 0:
                self.invincible = 0
                
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
            
        # Underwater physics
        if self.underwater:
            self.vy *= 0.95  # Water resistance
            self.vx *= 0.9
            
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
                elif self.invincible <= 0 and self.star_timer <= 0:
                    if state.mario_size == "fire":
                        state.mario_size = "big"
                        self.invincible = 2
                    elif state.mario_size == "big":
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
                    
        # Check collision with items
        for item in items[:]:
            if self.check_collision(item):
                if item.type == "mushroom":
                    if state.mario_size == "small":
                        state.mario_size = "big"
                    state.progress[state.slot]["powerups"].add("mushroom")
                elif item.type == "flower":
                    state.mario_size = "fire"
                    state.progress[state.slot]["powerups"].add("flower")
                elif item.type == "star":
                    self.star_timer = 10
                    self.invincible = 10
                    state.progress[state.slot]["powerups"].add("star")
                items.remove(item)
                state.score += 1000
                
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return  # Blink during invincibility
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Draw Mario based on size
        color = NES_PALETTE[33]  # Red for overalls
        skin = NES_PALETTE[39]   # Skin color
        
        if state.mario_size == "fire":
            # Fire Mario has white overalls
            color = NES_PALETTE[31]
        
        if state.mario_size in ("big", "fire"):
            # Body
            pygame.draw.rect(surf, color, (x+4, y+8, 8, 16))
            
            # Head
            pygame.draw.rect(surf, skin, (x+4, y+4, 8, 4))
            
            # Hat
            pygame.draw.rect(surf, color, (x+2, y, 12, 4))
            
            # Arms
            arm_offset = 0
            if self.animation_frame == 1 and self.vx != 0:
                arm_offset = 2 if self.facing_right else -2
                
            pygame.draw.rect(surf, skin, (x+arm_offset, y+10, 4, 6))  # Left arm
            pygame.draw.rect(surf, skin, (x+12-arm_offset, y+10, 4, 6))  # Right arm
            
            # Legs
            leg_offset = 0
            if self.animation_frame == 2 and self.vx != 0:
                leg_offset = 2 if self.facing_right else -2
                
            pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+24, 4, 8))  # Left leg
            pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+24-leg_offset, 4, 8+leg_offset))  # Right leg
            
            # Fire flower details
            if state.mario_size == "fire":
                # White cuffs
                pygame.draw.rect(surf, NES_PALETTE[31], (x+4, y+8, 8, 2))
                pygame.draw.rect(surf, NES_PALETTE[31], (x+4, y+18, 8, 2))
        else:
            # Small Mario
            # Body
            pygame.draw.rect(surf, color, (x+4, y+8, 8, 8))
            
            # Head
            pygame.draw.rect(surf, skin, (x+4, y, 8, 8))
            
            # Hat
            pygame.draw.rect(surf, color, (x+2, y, 12, 2))
        
        # Draw fireballs
        for fb in self.fireballs:
            fb.draw(surf, cam)

class Fireball:
    def __init__(self, x, y, right):
        self.x = x
        self.y = y
        self.vx = 6 if right else -6
        self.vy = 0
        self.width = 8
        self.height = 8
        self.active = True
        self.timer = 1.0
        
    def update(self, colliders, dt):
        self.x += self.vx
        self.vy += 0.2
        self.y += self.vy
        
        self.timer -= dt
        if self.timer <= 0:
            self.active = False
            
        # Check collision with walls
        for rect in colliders:
            if pygame.Rect(self.x, self.y, self.width, self.height).colliderect(rect):
                self.active = False
                
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        pygame.draw.circle(surf, NES_PALETTE[33], (x+4, y+4), 4)
        pygame.draw.circle(surf, NES_PALETTE[39], (x+4, y+4), 2)

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.walk_timer = 0
        
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
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[21], (x+2, y+4, 12, 12))  # Brown body
        
        # Feet
        foot_offset = 2 if self.animation_frame == 0 else -2
        pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+14, 4, 2))  # Left foot
        pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+14+foot_offset, 4, 2))  # Right foot
        
        # Eyes
        eye_dir = 0 if self.vx > 0 else 2
        pygame.draw.rect(surf, NES_PALETTE[0], (x+4+eye_dir, y+6, 2, 2))  # Left eye
        pygame.draw.rect(surf, NES_PALETTE[0], (x+10-eye_dir, y+6, 2, 2))  # Right eye

class PiranhaPlant(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vy = -0.5
        self.height = 16
        self.max_height = 32
        self.state = "rising"  # rising, up, lowering
        self.timer = 0
        
    def update(self, colliders, dt):
        self.timer += dt
        
        if self.state == "rising":
            self.y += self.vy
            if self.height >= self.max_height:
                self.state = "up"
                self.timer = 0
        elif self.state == "up":
            if self.timer > 2.0:
                self.state = "lowering"
        elif self.state == "lowering":
            self.y -= self.vy
            if self.height <= 16:
                self.state = "rising"
                self.timer = 0
                
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        
        # Stem
        pygame.draw.rect(surf, NES_PALETTE[14], (x+6, y, 4, self.height))
        
        # Head
        pygame.draw.ellipse(surf, NES_PALETTE[14], (x+2, y-4, 12, 12))
        
        # Mouth
        pygame.draw.ellipse(surf, NES_PALETTE[33], (x+4, y-2, 8, 8))
        pygame.draw.rect(surf, NES_PALETTE[0], (x+4, y+2, 8, 4))

class CheepCheep(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = random.choice([-1, 1])
        self.vy = 0
        self.amplitude = random.uniform(0.5, 1.5)
        self.offset = random.uniform(0, math.pi*2)
        
    def update(self, colliders, dt):
        self.x += self.vx
        self.vy = math.sin(pygame.time.get_ticks() / 500.0 + self.offset) * self.amplitude
        self.y += self.vy
        
        # Bounce off edges
        if self.x < 0:
            self.vx = abs(self.vx)
        elif self.x > 3000:
            self.vx = -abs(self.vx)
            
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[33], (x, y, 16, 8))
        
        # Tail
        pygame.draw.polygon(surf, NES_PALETTE[33], [(x+16, y+4), (x+24, y), (x+24, y+8)])
        
        # Eye
        pygame.draw.circle(surf, NES_PALETTE[0], (x+4, y+3), 2)
        
        # Fins
        pygame.draw.polygon(surf, NES_PALETTE[33], [(x+8, y), (x+12, y-4), (x+16, y)])

class Boss(Entity):
    def __init__(self, x, y, boss_type):
        super().__init__(x, y)
        self.boss_type = boss_type
        self.health = 3
        self.attack_timer = 0
        self.attack_cooldown = 2.0
        self.vx = 0
        self.vy = 0
        self.width = 32
        self.height = 32
        
    def update(self, colliders, dt, player):
        self.attack_timer += dt
        
        # Simple AI
        if self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0
            # Choose attack based on boss type
            if self.boss_type == "boom_boom":
                # Charge at player
                self.vx = 2 if player.x > self.x else -2
            elif self.boss_type == "morton":
                # Ground pound
                self.vy = -5
                
        # Move
        self.x += self.vx
        self.y += self.vy
        
        # Apply gravity
        if not self.on_ground:
            self.vy += 0.2
            
        # Check collision with ground
        self.on_ground = False
        for rect in colliders:
            if self.get_rect().colliderect(rect):
                if self.vy > 0 and self.y + self.height > rect.top and self.y < rect.top:
                    self.y = rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    if self.boss_type == "morton":
                        # Shockwave on ground pound
                        pass
                    
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        
        if self.boss_type == "boom_boom":
            # Boom Boom
            # Body
            pygame.draw.ellipse(surf, NES_PALETTE[31], (x, y, 32, 32))
            
            # Arms
            arm_angle = math.sin(pygame.time.get_ticks() / 200) * 0.5
            arm_length = 20
            pygame.draw.line(surf, NES_PALETTE[31], (x+16, y+16), 
                            (x+16 + math.cos(arm_angle) * arm_length, y+16 + math.sin(arm_angle) * arm_length), 6)
            pygame.draw.line(surf, NES_PALETTE[31], (x+16, y+16), 
                            (x+16 + math.cos(arm_angle+math.pi) * arm_length, y+16 + math.sin(arm_angle+math.pi) * arm_length), 6)
            
            # Face
            pygame.draw.circle(surf, NES_PALETTE[0], (x+16, y+16), 6)
            pygame.draw.circle(surf, NES_PALETTE[39], (x+16, y+16), 4)
            
        elif self.boss_type == "morton":
            # Morton Koopa Jr.
            # Shell
            pygame.draw.ellipse(surf, NES_PALETTE[33], (x, y, 32, 24))
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+8, y-8, 16, 16))
            
            # Eyes
            pygame.draw.circle(surf, NES_PALETTE[0], (x+12, y), 3)
            pygame.draw.circle(surf, NES_PALETTE[0], (x+20, y), 3)
            
            # Spike
            pygame.draw.polygon(surf, NES_PALETTE[21], [(x+16, y-16), (x+12, y-8), (x+20, y-8)])

class Item(Entity):
    def __init__(self, x, y, item_type):
        super().__init__(x, y)
        self.type = item_type
        self.vy = -2
        self.bounce_timer = 0
        
    def update(self, colliders, dt):
        self.bounce_timer += dt
        self.y += math.sin(self.bounce_timer * 5) * 0.5
        
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        
        if self.type == "mushroom":
            # Stem
            pygame.draw.rect(surf, NES_PALETTE[39], (x+6, y+8, 4, 8))
            # Cap
            pygame.draw.ellipse(surf, NES_PALETTE[33], (x+2, y, 12, 10))
            # Spots
            pygame.draw.circle(surf, NES_PALETTE[31], (x+5, y+3), 2)
            pygame.draw.circle(surf, NES_PALETTE[31], (x+11, y+3), 2)
            
        elif self.type == "flower":
            # Stem
            pygame.draw.rect(surf, NES_PALETTE[14], (x+7, y+8, 2, 8))
            # Flower
            pygame.draw.circle(surf, NES_PALETTE[33], (x+8, y+8), 6)
            pygame.draw.circle(surf, NES_PALETTE[39], (x+8, y+8), 4)
            # Petals
            for i in range(4):
                angle = i * math.pi/2
                pygame.draw.ellipse(surf, NES_PALETTE[33], 
                                   (x+8 + math.cos(angle)*4 - 4, y+8 + math.sin(angle)*4 - 2, 8, 4))
                
        elif self.type == "star":
            # Star body
            points = []
            for i in range(5):
                angle = math.pi/2 + i * 2*math.pi/5
                points.append((x+8 + math.cos(angle)*6, y+8 + math.sin(angle)*6))
                points.append((x+8 + math.cos(angle+math.pi/5)*3, y+8 + math.sin(angle+math.pi/5)*3))
                
            pygame.draw.polygon(surf, NES_PALETTE[31], points)
            pygame.draw.polygon(surf, NES_PALETTE[39], points, 1)

class TileMap:
    def __init__(self, level_data, theme):
        self.tiles = []
        self.colliders = []
        self.items = []
        self.width = len(level_data[0]) * TILE
        self.height = len(level_data) * TILE
        self.theme = theme
        
        # Parse level data
        for y, row in enumerate(level_data):
            for x, char in enumerate(row):
                if char != " ":
                    rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    self.tiles.append((x * TILE, y * TILE, char))
                    
                    if char in ("G", "B", "P", "T", "L", "?", "S", "D", "I", "C", "W", "Q"):
                        self.colliders.append(rect)
                    elif char == "O":  # Coin
                        self.items.append(Item(x * TILE, y * TILE, "coin"))
                    elif char == "M":  # Mushroom
                        self.items.append(Item(x * TILE, y * TILE, "mushroom"))
                    elif char == "F":  # Flower
                        self.items.append(Item(x * TILE, y * TILE, "flower"))
                    elif char == "S":  # Star
                        self.items.append(Item(x * TILE, y * TILE, "star"))
    
    def draw(self, surf, cam):
        # Draw background
        surf.fill(NES_PALETTE[self.theme["bg"]])
        
        # Draw clouds
        for i in range(10):
            x = (i * 80 + int(cam/3)) % (self.width + 200) - 100
            y = 30 + (i % 3) * 20
            pygame.draw.ellipse(surf, NES_PALETTE[31], (x, y, 30, 15))
            pygame.draw.ellipse(surf, NES_PALETTE[31], (x+15, y-5, 25, 15))
        
        # Draw tiles
        for x, y, char in self.tiles:
            draw_x = x - cam
            if draw_x < -TILE or draw_x > WIDTH:
                continue
                
            if char == "G":  # Green ground top
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]], (draw_x, y+8, TILE, TILE-8))
                pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+4, y+4, TILE-8, 4))
            elif char == "S":  # Sand
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "I":  # Ice
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[38], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "B":  # Brown block
                pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "P":  # Platform
                pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]], (draw_x, y, TILE, TILE))
            elif char == "T":  # Pipe
                pygame.draw.rect(surf, NES_PALETTE[14], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[20], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "?":  # Question block
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+4, y+4, 8, 4))
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+4, y+8, 2, 2))
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+10, y+8, 2, 2))
            elif char == "F":  # Flag
                pygame.draw.rect(surf, NES_PALETTE[31], (draw_x+6, y, 4, TILE*4))
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x, y, 10, 6))
            elif char == "L":  # Lava
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[21], (draw_x, y+4, TILE, TILE-4))
            elif char == "C":  # Coral
                pygame.draw.rect(surf, NES_PALETTE[25], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "W":  # Seaweed
                pygame.draw.rect(surf, NES_PALETTE[14], (draw_x+6, y, 4, TILE))
                pygame.draw.rect(surf, NES_PALETTE[14], (draw_x+2, y+8, 12, 4))
            elif char == "Q":  # Quicksand
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+2, y+2, TILE-4, TILE-4))
                for i in range(3):
                    pygame.draw.circle(surf, NES_PALETTE[21], (draw_x+4+i*4, y+8), 1)
        
        # Draw items
        for item in self.items:
            item.draw(surf, cam)

# Scenes
class TitleScreen(Scene):
    def __init__(self):
        self.timer = 0
        self.animation_frame = 0
        self.logo_y = -50
        self.logo_target_y = HEIGHT // 2 - 60
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN and e.key == K_RETURN:
                push(SlotSelect())
                
    def update(self, dt):
        self.timer += dt
        if self.timer > 0.1:
            self.timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
        # Animate logo coming down
        if self.logo_y < self.logo_target_y:
            self.logo_y += 3
            
    def draw(self, surf):
        # Background
        surf.fill(NES_PALETTE[27])
        
        # Koopa Engine Box
        box_width, box_height = 240, 100
        box_x = (WIDTH - box_width) // 2
        box_y = self.logo_y
        
        # Draw box with border
        pygame.draw.rect(surf, NES_PALETTE[0], (box_x-4, box_y-4, box_width+8, box_height+8))
        pygame.draw.rect(surf, NES_PALETTE[33], (box_x, box_y, box_width, box_height))
        
        # Title inside box
        title_font = pygame.font.SysFont(None, 32)
        title = title_font.render("KOOPA ENGINE 1.0A", True, NES_PALETTE[39])
        surf.blit(title, (box_x + (box_width - title.get_width()) // 2, box_y + 15))
        
        subtitle_font = pygame.font.SysFont(None, 16)
        subtitle = subtitle_font.render("Tech demo", True, NES_PALETTE[21])
        surf.blit(subtitle, (box_x + (box_width - subtitle.get_width()) // 2, box_y + 50))
        
        # Copyright
        copyright_font = pygame.font.SysFont(None, 14)
        copyright = copyright_font.render("[C] Team Flames 20XX [1985] - Nintendo", True, NES_PALETTE[0])
        surf.blit(copyright, (WIDTH//2 - copyright.get_width()//2, box_y + box_height + 20))
        
        # Mario and enemies
        mario_x = WIDTH//2 - 100
        mario_y = box_y + box_height + 50
        pygame.draw.rect(surf, NES_PALETTE[33], (mario_x+4, mario_y+8, 8, 16))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x+4, mario_y+4, 8, 4))
        pygame.draw.rect(surf, NES_PALETTE[33], (mario_x+2, mario_y, 12, 4))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x, mario_y+10, 4, 6))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x+16, mario_y+10, 4, 6))
        pygame.draw.rect(surf, NES_PALETTE[21], (mario_x+2, mario_y+24, 4, 8))
        pygame.draw.rect(surf, NES_PALETTE[21], (mario_x+10, mario_y+24, 4, 8))
        
        # Goomba
        goomba_x = WIDTH//2 + 30
        goomba_y = mario_y + 20
        pygame.draw.ellipse(surf, NES_PALETTE[21], (goomba_x+2, goomba_y+4, 12, 12))
        pygame.draw.rect(surf, NES_PALETTE[21], (goomba_x+2, goomba_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[21], (goomba_x+10, goomba_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (goomba_x+4, goomba_y+6, 2, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (goomba_x+10, goomba_y+6, 2, 2))
        
        # Koopa
        koopa_x = WIDTH//2 + 70
        koopa_y = mario_y + 20
        pygame.draw.ellipse(surf, NES_PALETTE[14], (koopa_x+2, koopa_y+4, 12, 12))
        pygame.draw.rect(surf, NES_PALETTE[39], (koopa_x+4, koopa_y, 8, 4))
        pygame.draw.rect(surf, NES_PALETTE[14], (koopa_x+2, koopa_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[14], (koopa_x+10, koopa_y+14, 4, 2))
        
        # Press Start
        if self.logo_y >= self.logo_target_y and int(self.timer * 10) % 2 == 0:
            font = pygame.font.SysFont(None, 24)
            text = font.render("PRESS ENTER", True, NES_PALETTE[39])
            surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 30))

class SlotSelect(Scene):
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
                    push(WorldSelect())
                elif e.key == K_ESCAPE:
                    push(TitleScreen())
                    
    def update(self, dt):
        self.offset += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render("SELECT PLAYER", True, NES_PALETTE[33])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw file slots
        for i in range(3):
            x = 50 + i * 100
            y = 90 + 5 * math.sin(self.offset * 3 + i)
            
            # Slot background
            pygame.draw.rect(s, NES_PALETTE[21], (x-5, y-5, 50, 70))
            pygame.draw.rect(s, NES_PALETTE[33], (x, y, 40, 60))
            
            # Slot number
            slot_font = pygame.font.SysFont(None, 20)
            slot_text = slot_font.render(f"{i+1}", True, NES_PALETTE[39])
            s.blit(slot_text, (x+18, y+5))
            
            # Selection indicator
            if i == self.selected:
                pygame.draw.rect(s, NES_PALETTE[39], (x-2, y-2, 44, 64), 2)
                
            # World preview
            if state.progress[i]:
                world = state.progress[i]["world"]
                world_font = pygame.font.SysFont(None, 16)
                world_text = world_font.render(f"WORLD {world}", True, NES_PALETTE[39])
                s.blit(world_text, (x+20 - world_text.get_width()//2, y+50))
                
                # Draw completed levels
                completed = len(state.progress[i]["completed"])
                completed_text = world_font.render(f"{completed}/32", True, NES_PALETTE[31])
                s.blit(completed_text, (x+20 - completed_text.get_width()//2, y+35))

class WorldSelect(Scene):
    def __init__(self):
        self.selected_world = 1
        self.offset = 0
        self.scroll_y = 0
        self.max_scroll = (8 - 4) * 60  # 8 worlds, 4 visible at a time
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key == K_UP:
                    self.selected_world = max(1, self.selected_world - 1)
                    # Adjust scroll to keep selection visible
                    if self.selected_world * 60 - self.scroll_y < 100:
                        self.scroll_y = max(0, self.selected_world * 60 - 100)
                elif e.key == K_DOWN:
                    self.selected_world = min(8, self.selected_world + 1)
                    # Adjust scroll to keep selection visible
                    if self.selected_world * 60 - self.scroll_y > HEIGHT - 100:
                        self.scroll_y = min(self.max_scroll, self.selected_world * 60 - HEIGHT + 100)
                elif e.key == K_RETURN:
                    push(LevelSelect(self.selected_world))
                elif e.key == K_ESCAPE:
                    pop()  # Back to slot select
                    
    def update(self, dt):
        self.offset += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render(f"SELECT WORLD - SLOT {state.slot+1}", True, NES_PALETTE[33])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw worlds
        for world in range(1, 9):
            y_pos = 80 + (world-1) * 60 - self.scroll_y
            if y_pos < 60 or y_pos > HEIGHT:
                continue
                
            # World box
            theme = WORLD_THEMES[str(world)]
            pygame.draw.rect(s, NES_PALETTE[theme["block"]], (50, y_pos, WIDTH-100, 50))
            pygame.draw.rect(s, NES_PALETTE[theme["ground"]], (55, y_pos+5, WIDTH-110, 40))
            
            # World title
            world_font = pygame.font.SysFont(None, 24)
            world_text = world_font.render(f"{theme['name']}", True, NES_PALETTE[39])
            s.blit(world_text, (WIDTH//2 - world_text.get_width()//2, y_pos+15))
            
            # Completed levels
            completed = sum(1 for lvl in range(1,5) 
                           if f"{world}-{lvl}" in state.progress[state.slot]["completed"])
            comp_font = pygame.font.SysFont(None, 18)
            comp_text = comp_font.render(f"{completed}/4 completed", True, NES_PALETTE[31])
            s.blit(comp_text, (WIDTH//2 - comp_text.get_width()//2, y_pos+35))
            
            # Selection indicator
            if world == self.selected_world:
                pygame.draw.rect(s, NES_PALETTE[39], (50, y_pos, WIDTH-100, 50), 3)
        
        # Scroll indicator
        if self.max_scroll > 0:
            scroll_height = (HEIGHT - 150) * (HEIGHT - 150) / (self.max_scroll + HEIGHT - 150)
            scroll_pos = 100 + (HEIGHT - 250) * self.scroll_y / self.max_scroll
            pygame.draw.rect(s, NES_PALETTE[21], (WIDTH-20, 100, 10, HEIGHT-150))
            pygame.draw.rect(s, NES_PALETTE[33], (WIDTH-18, scroll_pos, 6, scroll_height))
        
        # Instructions
        font = pygame.font.SysFont(None, 16)
        text = font.render("UP/DOWN: Select World  ENTER: Choose  ESC: Back", True, NES_PALETTE[0])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 20))

class LevelSelect(Scene):
    def __init__(self, world_num):
        self.world_num = world_num
        self.selected_level = 1
        self.offset = 0
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key == K_LEFT:
                    self.selected_level = max(1, self.selected_level - 1)
                elif e.key == K_RIGHT:
                    self.selected_level = min(4, self.selected_level + 1)
                elif e.key == K_RETURN:
                    level_id = f"{self.world_num}-{self.selected_level}"
                    state.world = level_id
                    push(LevelScene(level_id))
                elif e.key == K_ESCAPE:
                    pop()  # Back to world select
                    
    def update(self, dt):
        self.offset += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])
        theme = WORLD_THEMES[str(self.world_num)]
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render(f"{theme['name']} - SLOT {state.slot+1}", True, NES_PALETTE[33])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw levels
        for level in range(1, 5):
            x_pos = 50 + (level-1) * 70
            y_pos = 100
            
            # Level box
            pygame.draw.rect(s, NES_PALETTE[theme["block"]], (x_pos, y_pos, 60, 80))
            pygame.draw.rect(s, NES_PALETTE[theme["ground"]], (x_pos+5, y_pos+5, 50, 70))
            
            # Level number
            level_font = pygame.font.SysFont(None, 24)
            level_text = level_font.render(f"{level}", True, NES_PALETTE[39])
            s.blit(level_text, (x_pos+30 - level_text.get_width()//2, y_pos+15))
            
            # Draw thumbnail
            level_id = f"{self.world_num}-{level}"
            thumb = THUMBNAILS.get(level_id, THUMBNAILS["1-1"])
            s.blit(thumb, (x_pos+15, y_pos+35))
            
            # Castle icon for level 4
            if level == 4:
                pygame.draw.rect(s, NES_PALETTE[33], (x_pos+20, y_pos+10, 20, 15))
                pygame.draw.rect(s, NES_PALETTE[21], (x_pos+25, y_pos+5, 10, 5))
                pygame.draw.rect(s, NES_PALETTE[0], (x_pos+28, y_pos+8, 4, 7))
            
            # Completed indicator
            if level_id in state.progress[state.slot]["completed"]:
                pygame.draw.circle(s, NES_PALETTE[31], (x_pos+55, y_pos+15), 6)
            
            # Selection indicator
            if level == self.selected_level:
                pygame.draw.rect(s, NES_PALETTE[39], (x_pos, y_pos, 60, 80), 3)
        
        # Instructions
        font = pygame.font.SysFont(None, 16)
        text = font.render("LEFT/RIGHT: Select Level  ENTER: Play  ESC: Back", True, NES_PALETTE[0])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 20))

class LevelScene(Scene):
    def __init__(self, level_id):
        level_data, theme = LEVELS[level_id]
        self.map = TileMap(level_data, theme)
        self.player = Player(50, 100)
        self.enemies = []
        self.items = self.map.items
        self.cam = 0.0
        self.level_id = level_id
        self.time = 300
        self.coins = 0
        self.end_level = False
        self.end_timer = 0
        self.flag_pos = 0
        self.boss = None
        self.world_num = level_id.split("-")[0]
        
        # Check if underwater level
        self.player.underwater = self.world_num == "3"
        
        # Parse level for enemies and player start
        for y, row in enumerate(level_data):
            for x, char in enumerate(row):
                if char == "S":
                    self.player.x = x * TILE
                    self.player.y = y * TILE
                elif char == "G":
                    self.enemies.append(Goomba(x * TILE, y * TILE))
                elif char == "P":
                    self.enemies.append(PiranhaPlant(x * TILE, y * TILE))
                elif char == "C":
                    self.enemies.append(CheepCheep(x * TILE, y * TILE))
                elif char == "K":
                    self.enemies.append(Goomba(x * TILE, y * TILE))  # Koopa placeholder
                elif char == "X":  # Boss
                    if self.world_num == "1":
                        self.boss = Boss(x * TILE, y * TILE, "boom_boom")
                    elif self.world_num == "2":
                        self.boss = Boss(x * TILE, y * TILE, "morton")
                    else:
                        self.boss = Boss(x * TILE, y * TILE, "boom_boom")
                elif char == "F":
                    self.flag_pos = x * TILE
    
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    state.paused = not state.paused
                elif e.key == K_p:
                    state.paused = not state.paused
                    
    def update(self, dt):
        if state.paused:
            return
            
        # Update time
        self.time -= dt
        
        # Update player
        self.player.update(self.map.colliders, dt, self.enemies, self.items)
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.update(self.map.colliders, dt)
        
        # Update boss
        if self.boss and self.boss.active:
            self.boss.update(self.map.colliders, dt, self.player)
            
            # Check fireball collision with boss
            for fb in self.player.fireballs[:]:
                if self.boss.get_rect().colliderect(fb.x, fb.y, fb.width, fb.height):
                    self.boss.health -= 1
                    fb.active = False
                    if self.boss.health <= 0:
                        self.boss.active = False
                        state.progress[state.slot]["boss_defeated"] = True
                        state.score += 5000
        
        # Camera follow player
        target = self.player.x - WIDTH // 2
        self.cam += (target - self.cam) * 0.1
        self.cam = max(0, min(self.cam, self.map.width - WIDTH))
        
        # Check for end of level
        if self.player.x > self.map.width - 100 and not self.end_level:
            self.end_level = True
            self.end_timer = 3  # 3 seconds to show end sequence
            state.progress[state.slot]["completed"].add(self.level_id)
            
        if self.end_level:
            # Move player toward flag
            if self.player.x < self.flag_pos - 10:
                self.player.vx = 2
            else:
                self.player.vx = 0
                # Slide down flag
                if self.player.y < self.map.height - TILE * 5:
                    self.player.vy = 2
                    
            self.end_timer -= dt
            if self.end_timer <= 0:
                # Go back to level select
                pop()
        
    def draw(self, s):
        # Draw map
        self.map.draw(s, self.cam)
        
        # Draw enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.draw(s, self.cam)
            
        # Draw boss
        if self.boss and self.boss.active:
            self.boss.draw(s, self.cam)
            
        # Draw player
        self.player.draw(s, self.cam)
        
        # Draw HUD
        pygame.draw.rect(s, NES_PALETTE[0], (0, 0, WIDTH, 20))
        
        # Score
        font = pygame.font.SysFont(None, 16)
        score_text = font.render(f"SCORE {state.score:06d}", True, NES_PALETTE[39])
        s.blit(score_text, (10, 4))
        
        # Coins
        coin_text = font.render(f"COINS {state.coins:02d}", True, NES_PALETTE[39])
        s.blit(coin_text, (WIDTH//2 - coin_text.get_width()//2, 4))
        
        # World
        world_text = font.render(f"WORLD {self.level_id}", True, NES_PALETTE[39])
        s.blit(world_text, (WIDTH - world_text.get_width() - 10, 4))
        
        # Time
        time_text = font.render(f"TIME {int(self.time):03d}", True, NES_PALETTE[39])
        s.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 4))
        
        # Lives
        lives_text = font.render(f"x{state.lives}", True, NES_PALETTE[39])
        s.blit(lives_text, (WIDTH - 60, 4))
        # Draw small mario for lives indicator
        pygame.draw.rect(s, NES_PALETTE[33], (WIDTH - 80, 6, 8, 8))
        pygame.draw.rect(s, NES_PALETTE[39], (WIDTH - 80, 2, 8, 8))
        
        # Power-up indicator
        if state.mario_size == "big":
            pygame.draw.rect(s, NES_PALETTE[33], (10, HEIGHT-20, 12, 12))
        elif state.mario_size == "fire":
            pygame.draw.rect(s, NES_PALETTE[31], (10, HEIGHT-20, 12, 12))
        
        # Pause screen
        if state.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            s.blit(overlay, (0, 0))
            
            font = pygame.font.SysFont(None, 30)
            text = font.render("PAUSED", True, NES_PALETTE[39])
            s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
            
            font = pygame.font.SysFont(None, 16)
            text = font.render("Press P or ESC to continue", True, NES_PALETTE[39])
            s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 20))

class GameOverScene(Scene):
    def __init__(self):
        self.timer = 3
        
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            pop()  # Back to level select
            state.lives = 3
            state.score = 0
            
    def draw(self, s):
        s.fill(NES_PALETTE[0])
        font = pygame.font.SysFont(None, 40)
        text = font.render("GAME OVER", True, NES_PALETTE[33])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
        
        font = pygame.font.SysFont(None, 20)
        text = font.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[39])
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
                "color": random.choice([NES_PALETTE[33], NES_PALETTE[39], NES_PALETTE[31]]),
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
        s.fill(NES_PALETTE[0])
        
        # Draw fireworks
        for fw in self.fireworks:
            pygame.draw.circle(s, NES_PALETTE[39], (int(fw["x"]), int(fw["y"])), 3)
            for p in fw["particles"]:
                alpha = int(p["life"] * 255)
                color = (min(255, fw["color"][0]), min(255, fw["color"][1]), min(255, fw["color"][2]))
                pygame.draw.circle(s, color, (int(p["x"]), int(p["y"])), 2)
        
        # Text
        font = pygame.font.SysFont(None, 40)
        text = font.render("CONGRATULATIONS!", True, NES_PALETTE[33])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 50))
        
        font = pygame.font.SysFont(None, 30)
        text = font.render("YOU SAVED THE PRINCESS!", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 100))
        
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[31])
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
