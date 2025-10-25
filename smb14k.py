#!/usr/bin/env python3
"""
ULTRA! SUPER MARIO BROS 2D
Fused Engine: Somari Physics + Super Mario RPG HUD + Metal Gear "!" Eyes
"""

import pygame
import sys
import math
import random

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ULTRA! SUPER MARIO BROS 2D - Somari Engine")

SKY_BLUE = (107, 140, 255)
BROWN = (139, 69, 19)
RED = (220, 0, 0)
GREEN = (0, 168, 0)
YELLOW = (255, 216, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BROWN = (101, 67, 33)
BLUE = (0, 120, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 128, 0)

clock = pygame.time.Clock()
FPS = 60

GRAVITY = 0.8
MOVE_ACCEL = 0.18
GROUND_FRICTION = 0.94
AIR_FRICTION = 0.992
JUMP_STRENGTH = -14
MAX_SPEED_X = 12
MAX_FALL_SPEED = 15
SPIN_CHARGE_RATE = 0.55


class SuperMarioRPGHUD:
    def __init__(self):
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14, bold=True)
        self.health = 100
        self.max_health = 100
        self.coins = 0
        self.score = 0
        self.lives = 3
        self.time = 400
        self.world = "1-1"
        self.power_level = 1

    def draw(self, screen):
        pygame.draw.rect(screen, (40, 40, 120), (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.rect(screen, (80, 80, 200), (0, 0, SCREEN_WIDTH, 60), 2)

        # HP bar
        health_width = 200
        fill = (self.health / self.max_health) * health_width
        pygame.draw.rect(screen, (200, 0, 0), (20, 15, health_width, 20))
        pygame.draw.rect(screen, (0, 200, 0), (20, 15, fill, 20))
        pygame.draw.rect(screen, WHITE, (20, 15, health_width, 20), 2)
        screen.blit(self.font_small.render(f"HP: {self.health}/{self.max_health}", True, WHITE), (25, 17))

        stats_bg = pygame.Rect(SCREEN_WIDTH - 250, 10, 240, 40)
        pygame.draw.rect(screen, (60, 60, 140), stats_bg)
        pygame.draw.rect(screen, (100, 100, 220), stats_bg, 2)

        screen.blit(self.font_small.render(f"COINS: {self.coins:02d}", True, YELLOW), (SCREEN_WIDTH - 240, 15))
        screen.blit(self.font_small.render(f"LIVES: {self.lives}", True, WHITE), (SCREEN_WIDTH - 240, 35))
        screen.blit(self.font_small.render(f"SCORE: {self.score:06d}", True, WHITE), (SCREEN_WIDTH - 120, 15))
        screen.blit(self.font_small.render(f"WORLD: {self.world}", True, WHITE), (SCREEN_WIDTH - 120, 35))

        # Power bar
        power_bg = pygame.Rect(250, 15, 150, 20)
        pygame.draw.rect(screen, (80, 40, 0), power_bg)
        pygame.draw.rect(screen, ORANGE, (250, 15, self.power_level * 15, 20))
        pygame.draw.rect(screen, YELLOW, power_bg, 2)
        screen.blit(self.font_small.render(f"POWER: {self.power_level}", True, WHITE), (255, 17))


class Player:
    def __init__(self):
        self.width = 32
        self.height = 48
        self.x = 100
        self.y = SCREEN_HEIGHT - 150
        self.vel_x = 0
        self.vel_y = 0
        self.jump_power = -15
        self.gravity = 0.8
        self.speed = 5
        self.is_jumping = False
        self.facing_right = True
        self.lives = 3
        self.score = 0
        self.invincible = 0
        self.spin_mode = False
        self.charge = 0.0
        self.anim_timer = 0
        self.jump_pressed = False
        self.health = 100
        self.max_health = 100
        self.power_level = 1
        self.on_ground = False  # FIXED

    def draw_alert_eye(self, x, y):
        """Draws a NES-pixel-style Metal Gear '!' alert symbol."""
        pygame.draw.rect(screen, YELLOW, (x, y, 6, 8))
        pygame.draw.rect(screen, BLACK, (x + 2, y + 1, 2, 4))
        pygame.draw.rect(screen, RED, (x + 1, y, 4, 1))
        pygame.draw.rect(screen, BLACK, (x + 2, y + 6, 2, 1))
        pygame.draw.rect(screen, BLACK, (x + 2, y + 7, 2, 1))

    def draw(self):
        if self.invincible > 0 and self.invincible % 6 < 3:
            return
        pygame.draw.rect(screen, RED, (self.x, self.y + 15, self.width, self.height - 15))
        face_color = (252, 216, 168)
        pygame.draw.rect(screen, face_color, (self.x + 6, self.y, self.width - 12, 20))
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, 12))
        pygame.draw.rect(screen, RED, (self.x - 3, self.y + 12, self.width + 6, 6))

        # Metal Gear “!” eyes
        self.draw_alert_eye(self.x + 8, self.y + 6)
        self.draw_alert_eye(self.x + self.width - 14, self.y + 6)

        pygame.draw.circle(screen, YELLOW, (int(self.x + self.width // 2), int(self.y + 30)), 3)
        pygame.draw.rect(screen, face_color, (self.x - 4, self.y + 20, 4, 12))
        pygame.draw.rect(screen, face_color, (self.x + self.width, self.y + 20, 4, 12))
        leg_color = BLUE if self.power_level > 1 else RED
        pygame.draw.rect(screen, leg_color, (self.x + 4, self.y + self.height - 12, 8, 12))
        pygame.draw.rect(screen, leg_color, (self.x + self.width - 12, self.y + self.height - 12, 8, 12))
        if self.spin_mode and self.charge > 0:
            charge_radius = int(5 + self.charge * 2)
            pygame.draw.circle(screen, YELLOW, (int(self.x + self.width // 2), int(self.y + self.height // 2)), charge_radius, 2)

    def handle_input(self, keys):
        ax = 0.0
        down_pressed = keys[pygame.K_DOWN]
        if down_pressed and self.on_ground:
            self.charge += 1.0
            self.spin_mode = True
            ax = 0.0
            self.facing_right = self.vel_x >= 0
        else:
            if self.spin_mode and self.charge > 0:
                boost = min(self.charge * SPIN_CHARGE_RATE, MAX_SPEED_X)
                self.vel_x += boost if self.facing_right else -boost
                self.charge = 0.0
            self.spin_mode = False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                ax -= MOVE_ACCEL
                self.facing_right = False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                ax += MOVE_ACCEL
                self.facing_right = True
            jp = keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]
            if jp and self.on_ground and not self.jump_pressed:
                self.vel_y = JUMP_STRENGTH
                self.on_ground = False
            self.jump_pressed = jp

        self.vel_x += ax
        self.vel_x *= (GROUND_FRICTION if self.on_ground else AIR_FRICTION)
        self.vel_x = max(-MAX_SPEED_X, min(MAX_SPEED_X, self.vel_x))

    def update(self, platforms, blocks, enemies):
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
        if self.invincible > 0:
            self.invincible -= 1
        self.x += int(self.vel_x)
        self.y += int(self.vel_y)
        self.on_ground = False
        for platform in platforms:
            if (self.y + self.height >= platform.y and self.y + self.height <= platform.y + 15 and
                self.x + self.width > platform.x and self.x < platform.x + platform.width):
                self.y = platform.y - self.height
                self.vel_y = 0
                self.on_ground = True
        if self.y + self.height >= SCREEN_HEIGHT - 50:
            self.y = SCREEN_HEIGHT - 50 - self.height
            self.vel_y = 0
            self.on_ground = True
        return "playing"


class Platform:
    def __init__(self, x, y, width, height, style="ground"):
        self.x, self.y, self.width, self.height, self.style = x, y, width, height, style

    def draw(self):
        if self.style == "ground":
            pygame.draw.rect(screen, BROWN, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, 6))
        elif self.style == "brick":
            pygame.draw.rect(screen, (200, 76, 12), (self.x, self.y, self.width, self.height))
        elif self.style == "cloud":
            pygame.draw.ellipse(screen, WHITE, (self.x, self.y, self.width, self.height // 2))


def draw_background():
    for y in range(SCREEN_HEIGHT):
        shade = max(100, 255 - y // 3)
        pygame.draw.line(screen, (shade // 2, shade // 2, 255), (0, y), (SCREEN_WIDTH, y))
    pygame.draw.rect(screen, BROWN, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
    pygame.draw.rect(screen, GREEN, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 8))


def main():
    player = Player()
    hud = SuperMarioRPGHUD()
    game_state = "playing"

    platforms = [
        Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50),
        Platform(100, 450, 200, 20, "brick"),
        Platform(400, 400, 150, 20, "brick"),
        Platform(200, 350, 100, 20, "brick"),
        Platform(50, 300, 120, 20, "brick"),
        Platform(350, 500, 100, 20, "brick"),
    ]

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update(platforms, [], [])
        draw_background()
        for p in platforms:
            p.draw()
        player.draw()
        hud.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
