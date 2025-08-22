import math
import random
import sys
import pygame
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# =========================
# Midnight Drag (pygame) — Street-Spread Edition
# Controls:
#   A/D or ←/→ = steer
#   W/S or ↑/↓ = accelerate / brake
#   SPACE or LSHIFT = Nitro
#   P = pause | R = restart level | ESC = quit
# =========================

# --- Firebase Initialization ---
# IMPORTANT: Replace 'path/to/your/serviceAccountKey.json' with the actual path to your Firebase service account key file.
# You can download this file from your Firebase project settings -> Service accounts.
# Also, replace 'YOUR_DATABASE_URL' with your Firebase Realtime Database URL (e.g., 'https://your-project-id-default-rtdb.firebaseio.com/').
try:
    cred = credentials.Certificate('MD.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://midnight-drag-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
    firebase_ref = db.reference('leaderboard') # Reference to the 'leaderboard' node in your database
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    firebase_ref = None # Set to None if initialization fails


# ===============================

def clamp(x, a, b): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t

def glow_circle(surface, center, base_color, max_radius, steps=6, alpha_start=30):
    r, g, b = base_color
    for i in range(steps, 0, -1):
        radius = int(max_radius * i / steps)
        alpha = int(alpha_start * (i / steps))
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, alpha), (radius, radius), radius)
        surface.blit(s, (center[0] - radius, center[1] - radius))

def draw_neon_rect(surface, rect, color, thickness=2, glow=10):
    x, y, w, h = rect
    for i in range(glow, 0, -2):
        a = int(18 * (i / glow))
        pygame.draw.rect(surface, (*color, a), (x - i, y - i, w + i * 2, h + i * 2), border_radius=10)
    pygame.draw.rect(surface, color, rect, width=thickness, border_radius=10)

def draw_gradient_v(surface, rect, top_color, bottom_color):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        c = (int(lerp(top_color[0], bottom_color[0], t)),
             int(lerp(top_color[1], bottom_color[1], t)),
             int(lerp(top_color[2], bottom_color[2], t)))
        pygame.draw.line(surface, c, (x, y + i), (x + w, y + i))

# ---------- Procedural vehicles ----------
def make_car_surface(w=56, h=100, primary=(255, 60, 180), accents=(0, 255, 220), kind="car"):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    
    # Default body and cabin dimensions
    body_rect = pygame.Rect(4, 8, w-8, h-16)
    cabin_rect = pygame.Rect(w*0.18, h*0.18, w*0.64, h*0.32)
    stripe_rect = pygame.Rect(w*0.45, h*0.05, w*0.10, h*0.9)
    br = 12 # Default border radius

    if kind == "truck":
        body_rect = pygame.Rect(4, 8, w-8, h-16)
        cabin_rect = pygame.Rect(w*0.18, h*0.18, w*0.64, h*0.22)
        br = 8
    elif kind == "bike":
        body_rect = pygame.Rect(w*0.2, 8, w*0.6, h-16)
        cabin_rect = pygame.Rect(w*0.3, h*0.25, w*0.4, h*0.15)
        stripe_rect = pygame.Rect(w*0.4, h*0.05, w*0.2, h*0.9)
        br = 10
    elif kind == "van":
        body_rect = pygame.Rect(4, 8, w-8, h-16)
        cabin_rect = pygame.Rect(w*0.15, h*0.15, w*0.7, h*0.4)
        br = 10
    elif kind == "sport": # Sleeker, lower profile
        body_rect = pygame.Rect(6, 10, w-12, h-20)
        cabin_rect = pygame.Rect(w*0.2, h*0.25, w*0.6, h*0.25)
        stripe_rect = pygame.Rect(w*0.47, h*0.05, w*0.06, h*0.9) # Thinner stripe
        br = 15 # More rounded
    elif kind == "muscle": # Wider, more aggressive
        body_rect = pygame.Rect(2, 6, w-4, h-12)
        cabin_rect = pygame.Rect(w*0.15, h*0.2, w*0.7, h*0.3)
        stripe_rect = pygame.Rect(w*0.4, h*0.05, w*0.2, h*0.9) # Wider stripe
        br = 8 # Sharper corners
    elif kind == "classic": # Rounded, vintage feel
        body_rect = pygame.Rect(8, 12, w-16, h-24)
        cabin_rect = pygame.Rect(w*0.2, h*0.2, w*0.6, h*0.35)
        stripe_rect = pygame.Rect(w*0.4, h*0.08, w*0.2, h*0.8) # Shorter, wider stripe
        br = 20 # Very rounded

    # Glow
    for i in range(12, 0, -2):
        a = int(20 * (i / 12))
        pygame.draw.rect(surf, (*primary, a), body_rect.inflate(i*2, i*2), border_radius=br+i)
    
    # Body
    pygame.draw.rect(surf, primary, body_rect, border_radius=br)
    
    # Cabin
    pygame.draw.rect(surf, (10, 10, 30), cabin_rect, border_radius=10)
    pygame.draw.rect(surf, accents, cabin_rect, width=2, border_radius=10)
    
    # Stripe
    pygame.draw.rect(surf, accents, stripe_rect, border_radius=8)
    
    # Lights
    # Headlights
    pygame.draw.rect(surf, (250, 250, 180), (w*0.15, 2, w*0.2, 10), border_radius=5)
    pygame.draw.rect(surf, (250, 250, 180), (w*0.65, 2, w*0.2, 10), border_radius=5)
    # Taillights
    pygame.draw.rect(surf, (255, 60, 30), (w*0.15, h-12, w*0.2, 10), border_radius=5)
    pygame.draw.rect(surf, (255, 60, 30), (w*0.65, h-12, w*0.2, 10), border_radius=5)
    
    # Wheels
    wheel_h = 28 if kind not in ["bike", "sport"] else 18 if kind == "bike" else 24 # Adjust wheel height for sport
    for x_offset in (8, w-18):
        for y_offset in (18, h-28):
            wheel = pygame.Rect(x_offset, y_offset, 10, wheel_h)
            pygame.draw.rect(surf, (15, 15, 18), wheel, border_radius=3)
            pygame.draw.rect(surf, (90, 90, 110), wheel, width=2, border_radius=3)
    return surf

def make_vehicle(kind="car", color=(90, 200, 255)):
    if kind == "bike":
        return make_car_surface(32, 72, primary=color, accents=(240, 240, 255), kind="bike")
    if kind == "truck":
        return make_car_surface(72, 130, primary=color, accents=(240, 240, 255), kind="truck")
    if kind == "van":
        return make_car_surface(60, 108, primary=color, accents=(240, 240, 255), kind="van")
    if kind == "sport":
        return make_car_surface(50, 90, primary=color, accents=(0, 255, 255), kind="sport")
    if kind == "muscle":
        return make_car_surface(60, 110, primary=color, accents=(255, 255, 0), kind="muscle")
    if kind == "classic":
        return make_car_surface(58, 95, primary=color, accents=(200, 200, 200), kind="classic")
    return make_car_surface(56, 100, primary=color, accents=(240, 240, 255), kind="car")

# ---------- Particles ----------
class Particle:
    def __init__(self, pos, vel, life, size, color):
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.life = life
        self.t = life
        self.size = size
        self.color = color
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.t -= dt
    def alive(self): return self.t > 0
    def draw(self, surface):
        if self.t <= 0: return
        k = self.t / self.life
        a = int(180 * (k ** 1.5))
        r = max(1, int(self.size * (0.6 + 0.4 * k)))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (r, r), r)
        surface.blit(s, (self.x - r, self.y - r))

# ---------- Levels ----------
LEVELS = [
    # name, distance_goal, traffic_rate, max_speed, orb_rate, near_miss_score, palette, lateral_activity, background_theme
    ("Neon Warmup",       1200,  1.0,  260,  0.55, 30, ((10,10,25),(15,5,40)), 0.35, "city"), # Increased goal
    ("City Pulse",       1600,  1.4,  290,  0.65, 35, ((8,8,20),(10,10,35)), 0.45, "city"), # Increased goal
    ("Cyber Tunnel",     2000,  1.9,  320,  0.75, 40, ((10,6,18),(14,10,28)), 0.55, "city"), # Increased goal
    ("Starlit Bridge",   2400,  2.6,  350,  0.85, 45, ((6,6,16),(10,10,24)), 0.70, "bridge"), # Increased goal
    ("Quantum Strip",    2800,  3.3,  380,  0.95, 50, ((5,6,16),(8,8,22)),  0.85, "futuristic"), # Increased goal
    ("Violet Overdrive", 3200,  4.1,  410,  1.00, 55, ((6,4,14),(10,6,20)),  1.00, "city"), # Increased goal
    ("Abyss Express",    3600,  4.9,  440,  1.05, 60, ((4,4,10),(8,6,16)),  1.15, "abyss"), # Increased goal
    ("Midnight Crown",   4000,  5.7,  480,  1.10, 70, ((3,3,8),(6,5,12)),   1.30, "city"), # Increased goal
    # New Levels
    ("Desert Mirage",    4500,  3.0,  300,  0.60, 40, ((50,30,10),(80,50,20)), 0.40, "desert"),
    ("Mountain Pass",    5000,  3.8,  330,  0.70, 45, ((20,30,40),(30,50,60)), 0.60, "mountain"),
    ("Ocean Drive",      5500,  4.5,  360,  0.80, 50, ((10,20,50),(20,40,80)), 0.75, "ocean"),
    ("Volcanic Trail",   6000,  5.2,  390,  0.90, 55, ((30,10,10),(60,20,20)), 0.90, "volcano"),
    ("Cosmic Highway",   6500,  6.0,  420,  1.00, 60, ((10,10,30),(20,20,60)), 1.00, "cosmic"),
]

# Player Car Types and their stats
CAR_TYPES = {
    "Standard": {"kind": "car", "color": (90, 200, 255), "max_speed_mult": 1.0, "accel_mult": 1.0, "turn_mult": 1.0},
    "Sport":    {"kind": "sport", "color": (255, 0, 0), "max_speed_mult": 1.2, "accel_mult": 1.1, "turn_mult": 1.3},
    "Muscle":   {"kind": "muscle", "color": (0, 0, 255), "max_speed_mult": 1.1, "accel_mult": 1.3, "turn_mult": 0.9},
    "Classic":  {"kind": "classic", "color": (150, 150, 150), "max_speed_mult": 0.9, "accel_mult": 0.9, "turn_mult": 1.1},
}

# ---------- Player ----------
class Player:
    def __init__(self, x, y, car_type_name="Standard"):
        self.car_type_name = car_type_name
        car_stats = CAR_TYPES[car_type_name]
        self.base_surface = make_vehicle(car_stats["kind"], car_stats["color"])
        self.surface = self.base_surface
        self.rect = self.surface.get_rect(center=(x, y))
        self.speed = 140.0
        self.base_max_speed = 280.0 * car_stats["max_speed_mult"]
        self.max_speed = self.base_max_speed # This will be updated by level params
        self.accel = 140.0 * car_stats["accel_mult"]
        self.turn_speed = 280.0 * car_stats["turn_mult"]
        self.nitro = 0.0
        self.nitro_max = 100.0
        self.nitro_active = False
        self.alive = True
        self.trail_timer = 0.0
        self.invincible_timer = 0.0 # For invincibility power-up
        self.score_multiplier_timer = 0.0 # For score multiplier power-up

    def update(self, dt, keys, bounds_x, road_grip_factor=1.0):
        if not self.alive: return

        # Update power-up timers
        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.score_multiplier_timer = max(0, self.score_multiplier_timer - dt)

        if keys[pygame.K_w] or keys[pygame.K_UP]:   self.speed += self.accel * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.speed -= self.accel * 1.2 * dt
        self.speed = clamp(self.speed, 60.0, self.max_speed * (1.35 if self.nitro_active else 1.0))
        if (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]) and self.nitro > 0:
            self.nitro_active = True
            self.nitro -= 30 * dt
            if self.nitro <= 0: self.nitro, self.nitro_active = 0, False
        else:
            self.nitro_active = False
        
        # Modified steering: more direct control, affected by road grip
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.turn_speed * dt * (1.15 if self.nitro_active else 1.0) * road_grip_factor
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.turn_speed * dt * (1.15 if self.nitro_active else 1.0) * road_grip_factor

        self.rect.x = clamp(self.rect.x, bounds_x[0], bounds_x[1] - self.rect.w)
        self.trail_timer += dt

    def add_nitro(self, v): self.nitro = clamp(self.nitro + v, 0, self.nitro_max)
    def activate_invincibility(self, duration): self.invincible_timer = duration
    def activate_score_multiplier(self, duration): self.score_multiplier_timer = duration
    def is_invincible(self): return self.invincible_timer > 0
    def get_score_multiplier(self): return 2 if self.score_multiplier_timer > 0 else 1

    def set_max_speed_from_level(self, level_max_speed):
        # Combine base car max speed with level max speed
        self.max_speed = level_max_speed * (self.base_max_speed / 280.0) # 280 is the base max_speed from original Player class

    def draw(self, surface):
        if self.is_invincible():
            # Flash player to indicate invincibility
            if int(pygame.time.get_ticks() / 100) % 2 == 0:
                temp_surf = self.surface.copy()
                temp_surf.fill((255, 255, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(temp_surf, self.rect.topleft)
            else:
                surface.blit(self.surface, self.rect.topleft)
        else:
            surface.blit(self.surface, self.rect.topleft)

# ---------- Smarter Traffic with lateral behavior ----------
class Traffic:
    def __init__(self, x, y, level_activity, road_bounds):
        # Choose vehicle kind and palette
        r = random.random()
        if r < 0.12:   kind = "bike"
        elif r < 0.40: kind = "car"
        elif r < 0.75: kind = "van"
        else:          kind = "truck"
        color_choices = [(70, 200, 255), (255, 60, 120), (140, 255, 120), (255, 180, 80), (160, 120, 255)]
        color = random.choice(color_choices)
        self.kind = kind
        self.surface = make_vehicle(kind, color)
        self.rect = self.surface.get_rect(midtop=(x, y))

        # Forward speed (slower for trucks, faster for bikes)
        base = {"bike": (170, 260), "car": (120, 220), "van": (100, 180), "truck": (80, 140)}[kind]
        self.speed = random.uniform(*base)
        # Lateral behavior
        self.road_left, self.road_right = road_bounds
        max_vx = 22 + 28 * level_activity
        self.vx = random.uniform(-max_vx, max_vx) * (0.3 if kind == "truck" else 1.0)
        self.wander_timer = random.uniform(0.6, 1.4) / max(0.35, level_activity)
        self.change_timer = random.uniform(1.2, 2.2) / max(0.35, level_activity)
        self.target_x = x
        self.activity = level_activity

    def update(self, dt, world_speed, player_rect):
        # forward relative motion
        self.rect.y += int((world_speed - self.speed) * dt)

        # random wander (smooth)
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            # flip small drift
            self.vx += random.uniform(-10, 10) * self.activity
            self.wander_timer = random.uniform(0.5, 1.2)

        # occasional lane-change "intent"
        self.change_timer -= dt
        if self.change_timer <= 0:
            width = self.road_right - self.road_left
            lane_w = width / 5
            candidate = random.randint(0, 5)
            self.target_x = self.road_left + candidate * lane_w + random.uniform(0.2, 0.8) * lane_w
            self.change_timer = random.uniform(1.0, 2.0) / max(0.4, self.activity)

        # avoid walls
        if self.rect.left < self.road_left + 10: self.vx = abs(self.vx) * 0.8 + 20 * self.activity
        if self.rect.right > self.road_right - 10: self.vx = -abs(self.vx) * 0.8 - 20 * self.activity

        # soft avoidance when near the player (prevents impossible traps)
        if abs(self.rect.centery - player_rect.centery) < 130:
            if self.rect.centerx < player_rect.centerx:
                self.vx -= 18 * self.activity
            else:
                self.vx += 18 * self.activity

        # steer toward target_x
        steer = clamp(self.target_x - self.rect.centerx, -40, 40)
        self.vx += steer * 0.6 * dt * (1.0 if self.kind != "truck" else 0.5)

        # apply lateral velocity with damping
        self.rect.x += int(self.vx * dt)
        self.vx *= (0.96 if self.kind != "bike" else 0.93)

        # clamp inside road
        if self.rect.left < self.road_left: self.rect.left, self.vx = self.road_left, abs(self.vx)*0.7
        if self.rect.right > self.road_right: self.rect.right, self.vx = self.road_right, -abs(self.vx)*0.7

    def draw(self, surface):
        surface.blit(self.surface, self.rect.topleft)

class RivalAI(Traffic): # Inherit from Traffic for basic movement
    def __init__(self, x, y, level_activity, road_bounds):
        super().__init__(x, y, level_activity, road_bounds)
        self.surface = make_vehicle("car", (255, 200, 0)) # Unique color for rival
        self.speed = random.uniform(200, 300) # Faster than regular traffic
        self.target_lane = random.randint(0, 4) # Rival tries to stay in a lane
        self.lane_change_timer = random.uniform(2.0, 5.0)

    def update(self, dt, world_speed, player_rect):
        # Rival AI specific movement logic
        self.rect.y += int((world_speed - self.speed) * dt)

        # Try to stay in target lane or change lanes
        self.lane_change_timer -= dt
        if self.lane_change_timer <= 0:
            self.target_lane = random.randint(0, 4)
            self.lane_change_timer = random.uniform(2.0, 5.0)

        lane_w = (self.road_right - self.road_left) / 5
        target_x_in_lane = self.road_left + self.target_lane * lane_w + lane_w / 2
        
        # Steer towards target lane, with some randomness
        steer_force = clamp(target_x_in_lane - self.rect.centerx, -50, 50)
        self.vx += steer_force * 0.8 * dt + random.uniform(-5, 5) * dt

        # Avoid player if too close
        if abs(self.rect.centery - player_rect.centery) < 150:
            if self.rect.centerx < player_rect.centerx:
                self.vx -= 25 * self.activity
            else:
                self.vx += 25 * self.activity

        self.rect.x += int(self.vx * dt)
        self.vx *= 0.95 # Damping

        # Clamp inside road
        if self.rect.left < self.road_left: self.rect.left, self.vx = self.road_left, abs(self.vx)*0.7
        if self.rect.right > self.road_right: self.rect.right, self.vx = self.road_right, -abs(self.vx)*0.7

    def draw(self, surface):
        surface.blit(self.surface, self.rect.topleft)

class Orb:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.r = 10
        self.color = (0, 255, 220)
    def update(self, dt, world_speed): self.y += (world_speed - 0) * dt
    def draw(self, surface):
        glow_circle(surface, (int(self.x), int(self.y)), self.color, 18, steps=6, alpha_start=36)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.r, width=2)

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x, self.y = x, y
        self.power_type = power_type # "invincibility", "speed_boost", "score_multiplier"
        self.r = 12
        self.color = (255, 255, 0) if power_type == "invincibility" else \
                     (0, 255, 0) if power_type == "speed_boost" else \
                     (255, 165, 0) # Orange for score multiplier
        self.text = "I" if power_type == "invincibility" else \
                    "S" if power_type == "speed_boost" else \
                    "$"
        self.font = pygame.font.SysFont("Montserrat", 16, bold=True)

    def update(self, dt, world_speed):
        self.y += (world_speed - 0) * dt

    def draw(self, surface):
        glow_circle(surface, (int(self.x), int(self.y)), self.color, 20, steps=6, alpha_start=40)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.r, width=2)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surf, text_rect)

    def alive(self, screen_height):
        return self.y < screen_height + 60

class Obstacle:
    def __init__(self, x, y, width, height, color=(200, 50, 50)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.glow_color = (255, 0, 0) # Red glow for obstacles
        self.glow_strength = 10

    def update(self, dt, world_speed):
        self.rect.y += int(world_speed * dt)

    def draw(self, surface):
        # Draw glow
        for i in range(self.glow_strength, 0, -2):
            a = int(18 * (i / self.glow_strength))
            pygame.draw.rect(surface, (*self.glow_color, a), self.rect.inflate(i*2, i*2), border_radius=5)
        # Draw obstacle body
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)

    def alive(self, screen_height):
        return self.rect.top < screen_height

class DestructibleElement:
    def __init__(self, x, y, width, height, color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.life = 1 # Can be destroyed in one hit
        self.destroyed = False

    def update(self, dt, world_speed):
        if not self.destroyed:
            self.rect.y += int(world_speed * dt)

    def draw(self, surface):
        if not self.destroyed:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=3)

    def alive(self, screen_height):
        return self.rect.top < screen_height and not self.destroyed

    def hit(self):
        self.destroyed = True

class FloatingText:
    def __init__(self, x, y, text, color=(255,255,255)):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.timer = 1.2
    def update(self, dt):
        self.timer -= dt
        self.y -= 35 * dt
    def alive(self): return self.timer > 0

# ---------- HUD & Scenery ----------
def draw_hud(surface, font, small, score, dist, goal, speed, nitro, level_name, paused=False, player_invincible=False, score_multiplier_active=False):
    w, h = surface.get_size()
    bar_w, bar_h = 200, 12
    x, y = 20, h - 24
    pygame.draw.rect(surface, (30, 30, 50), (x, y, bar_w, bar_h), border_radius=8)
    fill = int(bar_w * clamp(speed / 500, 0, 1))
    pygame.draw.rect(surface, (120, 200, 255), (x, y, fill, bar_h), border_radius=8)
    surface.blit(small.render("SPEED", True, (200, 220, 255)), (x, y - 18))
    nx = x + bar_w + 20
    pygame.draw.rect(surface, (30, 30, 50), (nx, y, bar_w, bar_h), border_radius=8)
    nfill = int(bar_w * clamp(nitro / 100, 0, 1))
    pygame.draw.rect(surface, (0, 255, 220), (nx, y, nfill, bar_h), border_radius=8)
    surface.blit(small.render("NITRO", True, (200, 255, 245)), (nx, y - 18))
    surface.blit(font.render(f"{level_name}", True, (240, 240, 255)), (20, 12))
    surface.blit(small.render(f"Score: {int(score)}", True, (230, 230, 255)), (20, 48))
    surface.blit(small.render(f"Distance: {int(dist)} / {goal} m", True, (210, 210, 240)), (20, 72))

    if player_invincible:
        inv_text = small.render("INVINCIBLE!", True, (255, 255, 0))
        surface.blit(inv_text, (nx + bar_w + 20, y - 18))
    if score_multiplier_active:
        mult_text = small.render("x2 SCORE!", True, (255, 165, 0))
        surface.blit(mult_text, (nx + bar_w + 20, y))


    if paused:
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((6, 8, 14, 160))
        surface.blit(overlay, (0, 0))
        ptext = font.render("PAUSED", True, (255, 255, 255))
        surface.blit(ptext, (w//2 - ptext.get_width()//2, h//2 - 60))
        for i, line in enumerate(["A/D or ←/→: steer", "W/S or ↑/↓: accelerate / brake", "SPACE: Nitro      R: Restart      ESC: Quit"]):
            t = small.render(line, True, (220, 230, 255))
            surface.blit(t, (w//2 - t.get_width()//2, h//2 + i*22))

def draw_parallax_city(surface, t, palette, weather_effect=None, background_theme="city"):
    w, h = surface.get_size()
    sky_top, sky_bottom = palette
    draw_gradient_v(surface, (0, 0, w, h), sky_top, sky_bottom)
    
    # Stars (always present, but might be obscured by fog)
    random.seed(0)
    for _ in range(60):
        sx = random.randint(0, w)
        sy = random.randint(0, h//2)
        pygame.draw.rect(surface, (220, 230, 255), (sx, sy, 2, 2))
    
    random.seed(1)
    base_y = int(h * 0.55)

    if background_theme == "city":
        for i in range(80):
            bx = (i * 40 - int(t * 20)) % (w + 40) - 20
            bw = random.randint(20, 46)
            bh = random.randint(40, 130)
            col = (20, 20, 40)
            pygame.draw.rect(surface, col, (bx, base_y - bh, bw, bh))
            if i % 3 == 0:
                for wy in range(base_y - bh + 8, base_y - 10, 10):
                    if random.random() < 0.3:
                        wx = bx + random.randint(4, bw - 8)
                        pygame.draw.rect(surface, (255, 230, 120), (wx, wy, 3, 5))
    elif background_theme == "bridge":
        # Draw bridge cables/structure
        for i in range(0, w, 100):
            x_offset = (i - int(t * 10)) % (w + 100) - 50
            pygame.draw.line(surface, (100, 100, 120), (x_offset, base_y), (x_offset + 50, base_y - 100), 3)
            pygame.draw.line(surface, (100, 100, 120), (x_offset, base_y), (x_offset - 50, base_y - 100), 3)
        # Draw water below
        draw_gradient_v(surface, (0, base_y, w, h - base_y), (10, 10, 40), (5, 5, 20))
        # Add some reflections/sparkles on water
        for _ in range(50):
            sx = random.randint(0, w)
            sy = random.randint(base_y, h)
            pygame.draw.rect(surface, (50, 50, 100, 100), (sx, sy, 2, 2))
    elif background_theme == "futuristic":
        # Draw glowing lines and geometric shapes
        for i in range(0, w, 80):
            x_offset = (i - int(t * 30)) % (w + 80) - 40
            pygame.draw.line(surface, (50, 200, 255, 150), (x_offset, base_y), (x_offset + 40, base_y - 150), 2)
            pygame.draw.line(surface, (50, 200, 255, 150), (x_offset, base_y), (x_offset - 40, base_y - 150), 2)
        for _ in range(30):
            sx = random.randint(0, w)
            sy = random.randint(0, base_y)
            glow_circle(surface, (sx, sy), (100, 255, 255), 8, steps=4, alpha_start=20)
    elif background_theme == "abyss":
        # Dark, deep space/ocean feel with faint distant lights
        for _ in range(100):
            sx = random.randint(0, w)
            sy = random.randint(0, h)
            pygame.draw.circle(surface, (random.randint(0, 20), random.randint(0, 20), random.randint(30, 60)), (sx, sy), random.randint(1, 3))
        # Faint, slow-moving "creatures" or anomalies
        for i in range(5):
            cx = (i * 200 + int(t * 5)) % (w + 200) - 100
            cy = (i * 150 + int(t * 8)) % (h + 150) - 75
            glow_circle(surface, (cx, cy), (50, 50, 100), 15, steps=5, alpha_start=15)
    elif background_theme == "desert":
        # Distant dunes/mountains
        for i in range(0, w, 150):
            x_offset = (i - int(t * 15)) % (w + 150) - 75
            pygame.draw.polygon(surface, (80, 60, 30), [(x_offset, base_y), (x_offset + 75, base_y - 80), (x_offset + 150, base_y)])
        # Faint stars in a clear desert sky
        random.seed(2)
        for _ in range(80):
            sx = random.randint(0, w)
            sy = random.randint(0, h//2)
            pygame.draw.rect(surface, (255, 240, 200), (sx, sy, 1, 1))
    elif background_theme == "mountain":
        # Jagged mountain peaks
        for i in range(0, w, 120):
            x_offset = (i - int(t * 18)) % (w + 120) - 60
            peak_height = random.randint(80, 150)
            pygame.draw.polygon(surface, (40, 50, 60), [(x_offset, base_y), (x_offset + 60, base_y - peak_height), (x_offset + 120, base_y)])
            pygame.draw.polygon(surface, (50, 60, 70), [(x_offset + 30, base_y), (x_offset + 90, base_y - peak_height + 20), (x_offset + 150, base_y)])
    elif background_theme == "ocean":
        # Distant ocean horizon and faint waves
        ocean_horizon_y = int(h * 0.6)
        draw_gradient_v(surface, (0, ocean_horizon_y, w, h - ocean_horizon_y), (10, 30, 70), (5, 15, 35))
        # Faint wave lines
        for i in range(0, w, 50):
            x_offset = (i - int(t * 10)) % (w + 50) - 25
            pygame.draw.line(surface, (20, 50, 100, 100), (x_offset, ocean_horizon_y + random.randint(0, h - ocean_horizon_y)), (x_offset + 20, ocean_horizon_y + random.randint(0, h - ocean_horizon_y)), 1)
        # Distant islands/landmasses
        if random.random() < 0.05: # Small chance to draw an island
            island_x = (random.randint(0, w) - int(t * 5)) % (w + 100) - 50
            island_width = random.randint(50, 100)
            island_height = random.randint(20, 40)
            pygame.draw.ellipse(surface, (30, 60, 30), (island_x, ocean_horizon_y - island_height // 2, island_width, island_height))
    elif background_theme == "volcano":
        # Red/orange sky, distant volcanic peaks
        draw_gradient_v(surface, (0, 0, w, h), (50, 10, 10), (100, 30, 30))
        for i in range(0, w, 100):
            x_offset = (i - int(t * 15)) % (w + 100) - 50
            peak_height = random.randint(60, 120)
            pygame.draw.polygon(surface, (30, 0, 0), [(x_offset, base_y), (x_offset + 50, base_y - peak_height), (x_offset + 100, base_y)])
            # Faint lava glow
            glow_circle(surface, (x_offset + 50, base_y - peak_height + 10), (255, 100, 0), 20, steps=4, alpha_start=15)
    elif background_theme == "cosmic":
        # Deep space with nebulae and distant galaxies
        # Draw faint nebulae
        for _ in range(5):
            nx = random.randint(0, w)
            ny = random.randint(0, h)
            glow_circle(surface, (nx, ny), (random.randint(50, 100), random.randint(0, 50), random.randint(100, 150)), random.randint(30, 80), steps=8, alpha_start=10)
        # Draw distant galaxies/stars
        for _ in range(10):
            gx = random.randint(0, w)
            gy = random.randint(0, h)
            pygame.draw.circle(surface, (200, 200, 255), (gx, gy), random.randint(1, 2))
            glow_circle(surface, (gx, gy), (200, 200, 255), 5, steps=3, alpha_start=5)


    # Apply weather effects
    if weather_effect == "rain":
        for _ in range(100):
            x = random.randint(0, w)
            y = random.randint(0, h)
            pygame.draw.line(surface, (150, 150, 200, 180), (x, y), (x - 5, y + 10), 1)
    elif weather_effect == "fog":
        fog_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        fog_overlay.fill((180, 180, 180, 80)) # Light grey, semi-transparent
        surface.blit(fog_overlay, (0, 0))


def draw_road(surface, road_left, road_right, t, dash_speed=240, weather_effect=None):
    w, h = surface.get_size()
    road_w = road_right - road_left
    draw_gradient_v(surface, (road_left, 0, road_w, h), (16, 16, 26), (26, 26, 36))
    # Edge neon
    for side in (road_left, road_right - 4):
        glow_color = (255, 0, 120)
        for i in range(12, 0, -2):
            a = int(14 * (i / 12))
            pygame.draw.rect(surface, (*glow_color, a), (side - (i if side==road_left else 0), 0, 4+i, h))
    # Painted lane guides (5 lanes reference)
    lane_count = 5
    lane_w = road_w / lane_count
    dash_h = 32
    gap = 36
    off = int((t * dash_speed) % (dash_h + gap))
    for k in range(1, lane_count):
        x = int(road_left + k * lane_w)
        for y in range(-off, h, dash_h + gap):
            pygame.draw.rect(surface, (210, 210, 220), (x-2, y, 4, dash_h), border_radius=3)

    if weather_effect == "rain":
        # Add puddles or wet road effect
        for _ in range(5):
            px = random.randint(road_left, road_right)
            py = random.randint(0, h)
            pygame.draw.circle(surface, (50, 50, 70, 100), (px, py), random.randint(10, 30))

# --- Firebase Leaderboard Functions ---
def submit_score(player_name, score):
    if firebase_ref:
        try:
            firebase_ref.push().set({'name': player_name, 'score': score})
            print(f"Score {score} submitted for {player_name}.")
        except Exception as e:
            print(f"Error submitting score to Firebase: {e}")
    else:
        print("Firebase not initialized. Cannot submit score.")

def get_leaderboard():
    if firebase_ref:
        try:
            # Order by score in descending order and limit to top 10
            scores_data = firebase_ref.order_by_child('score').limit_to_last(10).get()
            leaderboard = []
            if scores_data:
                # Firebase returns data as a dictionary of {key: value} pairs.
                # We need to convert it to a list of (name, score) tuples and sort it.
                for key, value in scores_data.items():
                    leaderboard.append((value.get('name', 'Unknown'), value.get('score', 0)))
                leaderboard.sort(key=lambda x: x[1], reverse=True) # Sort by score descending
            return leaderboard
        except Exception as e:
            print(f"Error retrieving leaderboard from Firebase: {e}")
            return []
    else:
        print("Firebase not initialized. Cannot retrieve leaderboard.")
        return []

# --- Leaderboard Screen ---
def leaderboard_screen(screen, font, small, W, H):
    leaderboard_running = True
    leaderboard_data = get_leaderboard()

    while leaderboard_running:
        screen.fill((10, 10, 30))

        title_text = font.render("LEADERBOARD", True, (0, 255, 220))
        screen.blit(title_text, (W // 2 - title_text.get_width() // 2, 50))

        if leaderboard_data:
            y_offset = 150
            for i, (name, score) in enumerate(leaderboard_data):
                entry_text = small.render(f"{i+1}. {name}: {int(score)}", True, (255, 255, 255))
                screen.blit(entry_text, (W // 2 - entry_text.get_width() // 2, y_offset + i * 30))
        else:
            no_data_text = small.render("No scores yet or Firebase error.", True, (150, 150, 150))
            screen.blit(no_data_text, (W // 2 - no_data_text.get_width() // 2, H // 2))

        back_text = small.render("Press ESC to return to Main Menu", True, (200, 200, 200))
        screen.blit(back_text, (W // 2 - back_text.get_width() // 2, H - 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False # Quit game
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    leaderboard_running = False
    return True # Return to main menu

# --- Score Submission Prompt ---
def score_submission_prompt(screen, font, small, W, H, final_score):
    input_active = True
    player_name = ""
    prompt_text = font.render("Enter your name for the leaderboard:", True, (255, 255, 255))
    score_text = small.render(f"Your Score: {int(final_score)}", True, (0, 255, 220))

    while input_active:
        screen.fill((10, 10, 30))
        screen.blit(prompt_text, (W // 2 - prompt_text.get_width() // 2, H // 3))
        screen.blit(score_text, (W // 2 - score_text.get_width() // 2, H // 3 + 50))

        name_display = font.render(player_name + ("|" if int(pygame.time.get_ticks() / 500) % 2 == 0 else ""), True, (255, 255, 255))
        name_rect = name_display.get_rect(center=(W // 2, H // 2 + 50))
        pygame.draw.rect(screen, (50, 50, 80), name_rect.inflate(20, 10), border_radius=5)
        screen.blit(name_display, name_rect)

        submit_info = small.render("Press ENTER to submit, ESC to skip", True, (200, 200, 200))
        screen.blit(submit_info, (W // 2 - submit_info.get_width() // 2, H - 100))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False # Quit game
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if player_name:
                        submit_score(player_name, int(final_score))
                    input_active = False
                elif event.key == pygame.K_ESCAPE:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    if len(player_name) < 15: # Limit name length
                        player_name += event.unicode
    return True # Continue to main menu

# ---------- Main Menu ----------
def main_menu(screen, font, small, W, H):
    menu_running = True
    selected_option = 0 # 0: Start Game, 1: Leaderboard, 2: Quit
    car_selection_mode = False
    selected_car_index = 0
    car_types_list = list(CAR_TYPES.keys())

    while menu_running:
        screen.fill((10, 10, 30)) # Dark background

        # Title
        title_text = font.render("MIDNIGHT DRAG", True, (0, 255, 220))
        screen.blit(title_text, (W // 2 - title_text.get_width() // 2, H // 4))

        if not car_selection_mode:
            # Menu Options
            options = ["START GAME", "LEADERBOARD", "QUIT"]
            for i, option in enumerate(options):
                color = (255, 255, 255) if i == selected_option else (150, 150, 150)
                text = font.render(option, True, color)
                screen.blit(text, (W // 2 - text.get_width() // 2, H // 2 + i * 60))
        else:
            # Car Selection
            car_title = font.render("SELECT YOUR RIDE", True, (0, 200, 255))
            screen.blit(car_title, (W // 2 - car_title.get_width() // 2, H // 2 - 100))

            # Display selected car
            selected_car_name = car_types_list[selected_car_index]
            car_surface = make_vehicle(CAR_TYPES[selected_car_name]["kind"], CAR_TYPES[selected_car_name]["color"])
            car_rect = car_surface.get_rect(center=(W // 2, H // 2 + 20))
            screen.blit(car_surface, car_rect)

            car_name_text = small.render(selected_car_name, True, (255, 255, 255))
            screen.blit(car_name_text, (W // 2 - car_name_text.get_width() // 2, H // 2 + 100))

            # Car Stats
            stats = CAR_TYPES[selected_car_name]
            stats_text = small.render(f"Speed: {stats['max_speed_mult']:.1f}x Accel: {stats['accel_mult']:.1f}x Turn: {stats['turn_mult']:.1f}x", True, (200, 200, 200))
            screen.blit(stats_text, (W // 2 - stats_text.get_width() // 2, H // 2 + 130))

            # Navigation arrows
            arrow_left = font.render("<", True, (255, 255, 255))
            arrow_right = font.render(">", True, (255, 255, 255))
            screen.blit(arrow_left, (W // 2 - 100, H // 2 + 10))
            screen.blit(arrow_right, (W // 2 + 80, H // 2 + 10))

            # Confirm button
            confirm_text = font.render("CONFIRM", True, (0, 255, 0))
            screen.blit(confirm_text, (W // 2 - confirm_text.get_width() // 2, H // 2 + 200))


        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None # Quit game
            if event.type == pygame.KEYDOWN:
                if not car_selection_mode:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN:
                        if selected_option == 0: # Start Game
                            car_selection_mode = True
                        elif selected_option == 1: # Leaderboard
                            if not leaderboard_screen(screen, font, small, W, H):
                                return None # User quit from leaderboard screen
                        else: # Quit
                            return None
                else: # Car selection mode
                    if event.key == pygame.K_LEFT:
                        selected_car_index = (selected_car_index - 1) % len(car_types_list)
                    elif event.key == pygame.K_RIGHT:
                        selected_car_index = (selected_car_index + 1) % len(car_types_list)
                    elif event.key == pygame.K_RETURN:
                        return car_types_list[selected_car_index] # Return selected car type

    return None # Should not be reached

# ---------- Game loop ----------
def game_loop(screen, font, small, W, H, selected_car_type):
    clock = pygame.time.Clock()

    # Road bounds (wider with shoulders for weaving)
    road_margin = 120
    road_left = road_margin
    road_right = W - road_margin

    player = Player(W // 2, int(H * 0.72), selected_car_type)

    level_index = 0
    def level_params(i):
        name, goal, traffic_rate, max_spd, orb_rate, nm_score, palette, activity, background_theme = LEVELS[i]
        return {"name": name, "goal": goal, "traffic_rate": traffic_rate, "max_spd": max_spd,
                "orb_rate": orb_rate, "nm_score": nm_score, "palette": palette, "activity": activity, "background_theme": background_theme}
    params = level_params(level_index)
    player.set_max_speed_from_level(params["max_spd"])

    score = 0
    distance = 0
    particles, traffics, orbs, obstacles, power_ups, destructibles, texts = [], [], [], [], [], [], []
    rival_ai = None

    spawn_t = 0.0
    spawn_orb_t = 0.0
    spawn_obstacle_t = 0.0
    spawn_power_up_t = 0.0
    spawn_destructible_t = 0.0

    paused = False
    time_t = 0.0
    near_miss_dist = 26
    near_miss_cooldown = 0.2
    near_timer = 0.0

    current_weather = None
    weather_change_timer = random.uniform(15, 30)
    road_grip_factor = 1.0

    def banner(text_top, text_bottom, color=(0,255,220)):
        s = pygame.Surface((W, 120), pygame.SRCALPHA)
        draw_neon_rect(s, (10, 10, W - 20, 100), color, thickness=2, glow=16)
        big = font.render(text_top, True, (240, 240, 255))
        s.blit(big, (W//2 - big.get_width()//2, 16))
        sm = small.render(text_bottom, True, (220, 230, 255))
        s.blit(sm, (W//2 - sm.get_width()//2, 62))
        return s
    banner_surf = banner(f"LEVEL 1 • {params['name']}", "New rule: traffic weaves & spreads across the whole street!")
    banner_timer = 2.4

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        time_t += dt
        near_timer = max(0.0, near_timer - dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_p: paused = not paused
                elif event.key == pygame.K_r:
                    # restart level
                    score = 0; distance = 0
                    particles.clear(); traffics.clear(); orbs.clear(); obstacles.clear(); power_ups.clear(); destructibles.clear(); texts.clear()
                    rival_ai = None
                    spawn_t = spawn_orb_t = spawn_obstacle_t = spawn_power_up_t = spawn_destructible_t = 0
                    player.rect.centerx = W//2; player.speed = 140; player.nitro = 0; player.alive = True
                    player.invincible_timer = 0; player.score_multiplier_timer = 0
                    current_weather = None; road_grip_factor = 1.0; weather_change_timer = random.uniform(15, 30)
                    banner_surf = banner(f"LEVEL {level_index+1} • {params['name']}", "Restarted!")
                    banner_timer = 1.2

        keys = pygame.key.get_pressed()
        if paused:
            draw_parallax_city(screen, time_t, params["palette"], current_weather, params["background_theme"])
            draw_road(screen, road_left, road_right, time_t, weather_effect=current_weather)
            for t in traffics: t.draw(screen)
            if rival_ai: rival_ai.draw(screen)
            for o in orbs: o.draw(screen)
            for obs in obstacles: obs.draw(screen)
            for pu in power_ups: pu.draw(screen)
            for de in destructibles: de.draw(screen)
            for p in particles: p.draw(screen)
            player.draw(screen)
            draw_hud(screen, font, small, score, distance, params["goal"], player.speed, player.nitro, params["name"], paused=True, player_invincible=player.is_invincible(), score_multiplier_active=player.score_multiplier_timer > 0)
            pygame.display.flip()
            continue

        # Update player
        player.update(dt, keys, (road_left + 14, road_right - 14), road_grip_factor)

        # Weather system update
        weather_change_timer -= dt
        if weather_change_timer <= 0:
            weather_options = [None, "rain", "fog"] # None means clear weather
            current_weather = random.choice(weather_options)
            weather_change_timer = random.uniform(20, 40) # Next weather change
            if current_weather == "rain":
                road_grip_factor = 0.7 # Reduced grip in rain
                texts.append(FloatingText(W//2, H//4, "RAIN! Reduced Grip!", color=(150, 150, 200)))
            elif current_weather == "fog":
                road_grip_factor = 0.9 # Slightly reduced grip in fog
                texts.append(FloatingText(W//2, H//4, "FOG! Low Visibility!", color=(180, 180, 180)))
            else:
                road_grip_factor = 1.0 # Full grip
                texts.append(FloatingText(W//2, H//4, "Clear Skies!", color=(200, 255, 200)))


        # Spawn traffic (street-wide)
        spawn_t -= dt
        if spawn_t <= 0:
            tr = params["traffic_rate"]
            spawn_t = clamp(1.1 / tr, 0.16, 0.9)
            width = road_right - road_left
            lane_w = width / 5
            lane = random.randint(0, 4)
            x = road_left + lane * lane_w + random.uniform(0.15, 0.85) * lane_w
            safe = True
            for v in traffics:
                if abs(v.rect.centerx - x) < 45 and v.rect.top < 140:
                    safe = False; break
            if safe:
                traffics.append(Traffic(x, -140, params["activity"], (road_left, road_right)))

        # Spawn Rival AI (only one at a time, and not too frequently)
        if rival_ai is None and random.random() < 0.001 * dt * 60: # Small chance per frame
            rival_ai = RivalAI(W // 2, -200, params["activity"], (road_left, road_right))

        # Spawn orbs
        spawn_orb_t -= dt
        if spawn_orb_t <= 0:
            spawn_orb_t = clamp(2.1 / params["orb_rate"], 0.35, 2.8)
            width = road_right - road_left
            x = road_left + random.uniform(0.12, 0.88) * width
            orbs.append(Orb(x, -30))

        # Spawn obstacles
        spawn_obstacle_t -= dt
        if spawn_obstacle_t <= 0:
            spawn_obstacle_t = random.uniform(1.5, 3.0)
            obs_width = random.randint(30, 80)
            obs_height = random.randint(20, 60)
            obs_x = random.randint(road_left, road_right - obs_width)
            obstacles.append(Obstacle(obs_x, -obs_height, obs_width, obs_height))

        # Spawn Power-Ups
        spawn_power_up_t -= dt
        if spawn_power_up_t <= 0:
            spawn_power_up_t = random.uniform(5.0, 10.0) # Spawn every 5-10 seconds
            power_up_types = ["invincibility", "speed_boost", "score_multiplier"]
            chosen_type = random.choice(power_up_types)
            pu_x = random.randint(road_left + 20, road_right - 20)
            power_ups.append(PowerUp(pu_x, -50, chosen_type))

        # Spawn Destructible Elements (on shoulders)
        spawn_destructible_t -= dt
        if spawn_destructible_t <= 0:
            spawn_destructible_t = random.uniform(0.8, 2.0)
            side = random.choice(["left", "right"])
            de_width = random.randint(15, 30)
            de_height = random.randint(20, 40)
            if side == "left":
                de_x = random.randint(road_left - 50, road_left - de_width - 10)
            else:
                de_x = random.randint(road_right + 10, road_right + 50 - de_width)
            destructibles.append(DestructibleElement(de_x, -de_height, de_width, de_height))


        # Update traffic/orbs/particles/obstacles/power-ups/destructibles
        for t in traffics: t.update(dt, player.speed, player.rect)
        if rival_ai: rival_ai.update(dt, player.speed, player.rect)
        for o in orbs: o.update(dt, player.speed)
        for obs in obstacles: obs.update(dt, player.speed)
        for pu in power_ups: pu.update(dt, player.speed)
        for de in destructibles: de.update(dt, player.speed)
        for p in particles: p.update(dt)
        particles = [p for p in particles if p.alive()]
        texts = [tx for tx in texts if tx.alive()]
        for tx in texts: tx.update(dt)

        # Despawn
        H = screen.get_height()
        traffics = [t for t in traffics if t.rect.top < H + 160]
        orbs = [o for o in orbs if o.y < H + 60]
        obstacles = [obs for obs in obstacles if obs.alive(H)]
        power_ups = [pu for pu in power_ups if pu.alive(H)]
        destructibles = [de for de in destructibles if de.alive(H)]
        if rival_ai and rival_ai.rect.top > H + 160: rival_ai = None # Despawn rival

        # Exhaust particles
        if player.trail_timer > (0.03 if player.nitro_active else 0.06):
            player.trail_timer = 0.0
            px, py = player.rect.centerx, player.rect.bottom - 6
            vspread = 50 if player.nitro_active else 30
            for _ in range(2 if player.nitro_active else 1):
                vx = random.uniform(-20, 20)
                vy = random.uniform(80, 130) + vspread
                col = (0, 255, 220) if player.nitro_active else (255, 60, 120)
                particles.append(Particle((px, py), (vx, vy), life=random.uniform(0.25, 0.45), size=random.randint(5,9), color=col))

        # Progress & score
        score_gain = (player.speed * 0.02) * dt * player.get_score_multiplier()
        distance += player.speed * dt
        score += score_gain

        # Collisions
        player_box = player.rect.inflate(-10, -18)
        if player.alive:
            # Traffic collision
            for t in traffics:
                shrink = (-10, -10) if t.kind == "bike" else (-8, -8) if t.kind == "car" else (-6, -6) if t.kind == "van" else (-2, -2)
                if player_box.colliderect(t.rect.inflate(*shrink)):
                    if not player.is_invincible():
                        player.alive = False
                        for _ in range(50):
                            ang = random.uniform(0, math.tau)
                            spd = random.uniform(120, 340)
                            particles.append(Particle(player.rect.center, (math.cos(ang)*spd, math.sin(ang)*spd), 0.6, random.randint(3,6), (255, 60, 120)))
                        texts.append(FloatingText(player.rect.centerx, player.rect.top, "CRASH!", color=(255, 90, 120)))
                        score = max(0, score - 80)
                    else:
                        # If invincible, traffic is destroyed
                        traffics.remove(t)
                        texts.append(FloatingText(t.rect.centerx, t.rect.top, "BOOM!", color=(255, 255, 0)))
                        score += 50 * player.get_score_multiplier()
                    break
            
            # Rival AI collision (if exists)
            if rival_ai and player_box.colliderect(rival_ai.rect.inflate(-8, -8)):
                if not player.is_invincible():
                    player.alive = False
                    for _ in range(50):
                        ang = random.uniform(0, math.tau)
                        spd = random.uniform(120, 340)
                        particles.append(Particle(player.rect.center, (math.cos(ang)*spd, math.sin(ang)*spd), 0.6, random.randint(3,6), (255, 60, 120)))
                    texts.append(FloatingText(player.rect.centerx, player.rect.top, "RIVAL CRASH!", color=(255, 90, 120)))
                    score = max(0, score - 150) # Higher penalty for rival crash
                else:
                    # If invincible, rival is defeated
                    rival_ai = None
                    texts.append(FloatingText(player.rect.centerx, player.rect.top, "RIVAL DEFEATED!", color=(255, 200, 0)))
                    score += 200 * player.get_score_multiplier()


            # Obstacle collision
            for obs in obstacles[:]:
                if player_box.colliderect(obs.rect):
                    if not player.is_invincible():
                        player.alive = False
                        for _ in range(50):
                            ang = random.uniform(0, math.tau)
                            spd = random.uniform(120, 340)
                            particles.append(Particle(player.rect.center, (math.cos(ang)*spd, math.sin(ang)*spd), 0.6, random.randint(3,6), (255, 60, 120)))
                        texts.append(FloatingText(player.rect.centerx, player.rect.top, "OBSTACLE HIT!", color=(255, 50, 50)))
                        score = max(0, score - 100)
                    else:
                        obstacles.remove(obs)
                        texts.append(FloatingText(obs.rect.centerx, obs.rect.top, "SMASH!", color=(255, 255, 0)))
                        score += 75 * player.get_score_multiplier()
                    break

            # Power-Up collection
            for pu in power_ups[:]:
                if (abs(pu.x - player.rect.centerx) < 30) and (abs(pu.y - player.rect.centery) < 60):
                    power_ups.remove(pu)
                    if pu.power_type == "invincibility":
                        player.activate_invincibility(5.0) # 5 seconds invincibility
                        texts.append(FloatingText(player.rect.centerx, player.rect.top - 20, "INVINCIBLE!", color=(255, 255, 0)))
                    elif pu.power_type == "speed_boost":
                        player.speed = min(player.max_speed * 1.5, player.speed + 100) # Temporary speed boost
                        texts.append(FloatingText(player.rect.centerx, player.rect.top - 20, "SPEED BOOST!", color=(0, 255, 0)))
                    elif pu.power_type == "score_multiplier":
                        player.activate_score_multiplier(8.0) # 8 seconds x2 score
                        texts.append(FloatingText(player.rect.centerx, player.rect.top - 20, "SCORE x2!", color=(255, 165, 0)))
                    score += 50 * player.get_score_multiplier()
                    break

            # Destructible element collision
            for de in destructibles[:]:
                if player_box.colliderect(de.rect):
                    de.hit()
                    texts.append(FloatingText(de.rect.centerx, de.rect.top, "CRUNCH!", color=(180, 180, 180)))
                    score += 10 * player.get_score_multiplier() # Small score for destroying
                    # Spawn small particles for visual effect
                    for _ in range(5):
                        particles.append(Particle(de.rect.center, (random.uniform(-50, 50), random.uniform(50, 100)), 0.3, random.randint(2,4), (100, 100, 100)))
                    break


        # Near-miss scoring
        if player.alive and near_timer <= 0:
            for t in traffics:
                dy = t.rect.centery - player.rect.centery
                if 0 < dy < 90:
                    dx = abs(t.rect.centerx - player.rect.centerx)
                    if dx < player.rect.w * 0.6 + near_miss_dist:
                        near_timer = near_miss_cooldown
                        bonus = params["nm_score"] * player.get_score_multiplier()
                        score += bonus
                        player.add_nitro(14)
                        texts.append(FloatingText(player.rect.centerx, player.rect.top - 14, f"NEAR MISS +{bonus}", color=(255, 255, 200)))
                        break

        # Orb collection
        if player.alive:
            for o in orbs[:]:
                if (abs(o.x - player.rect.centerx) < 28) and (abs(o.y - player.rect.centery) < 50):
                    orbs.remove(o)
                    score += 25 * player.get_score_multiplier()
                    player.add_nitro(18)
                    texts.append(FloatingText(player.rect.centerx, player.rect.top - 12, f"+ORB", color=(0, 255, 220)))
                    for _ in range(12):
                        angle = random.uniform(-0.6, 0.6) + math.pi/2
                        spd = random.uniform(90, 220)
                        particles.append(Particle((o.x, o.y), (math.cos(angle)*spd, math.sin(angle)*spd), 0.5, random.randint(3,6), (0, 255, 220)))

        # Level complete / Game complete
        if player.alive and distance >= params["goal"]:
            level_index += 1
            if level_index >= len(LEVELS):
                # Game Won!
                draw_parallax_city(screen, time_t, params["palette"], current_weather, params["background_theme"]); draw_road(screen, road_left, road_right, time_t, weather_effect=current_weather)
                msg = "YOU WON • Midnight Crown Achieved"
                sub = f"Final Score: {int(score)}  |  Press ESC to quit or R to replay last level"
                screen.blit(banner(msg, sub, color=(0,255,220)), (0, screen.get_height()//2 - 60))
                pygame.display.flip()
                
                # Prompt for score submission
                if firebase_ref:
                    if not score_submission_prompt(screen, font, small, W, H, score):
                        return # User quit during submission prompt
                
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT: return # Quit game
                        if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
                            return # Quit game
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                            return # Restart game (handled by main loop)
                    clock.tick(60) # Keep window responsive
            
            # Proceed to next level
            params = level_params(level_index)
            player.set_max_speed_from_level(params["max_spd"]) # Update player max speed for new level
            distance = 0
            particles.clear(); traffics.clear(); orbs.clear(); obstacles.clear(); power_ups.clear(); destructibles.clear(); texts.clear()
            rival_ai = None # Reset rival for new level
            spawn_t = spawn_orb_t = spawn_obstacle_t = spawn_power_up_t = spawn_destructible_t = 0
            player.rect.centerx = (road_left + road_right)//2
            player.speed = max(160, player.speed * 0.75)
            player.nitro = clamp(player.nitro + 20, 0, player.nitro_max)
            player.alive = True
            player.invincible_timer = 0; player.score_multiplier_timer = 0 # Reset power-ups on level change
            current_weather = None; road_grip_factor = 1.0; weather_change_timer = random.uniform(15, 30) # Reset weather
            banner_surf = banner(f"LEVEL {level_index+1} • {params['name']}", "Heavier traffic, more weaving. Keep those near-misses coming!")
            banner_timer = 2.2

        # -------- Render --------
        draw_parallax_city(screen, time_t, params["palette"], current_weather, params["background_theme"])
        draw_road(screen, road_left, road_right, time_t, weather_effect=current_weather)

        for o in orbs: o.draw(screen)
        for t in traffics: t.draw(screen)
        if rival_ai: rival_ai.draw(screen) # Draw rival AI
        for obs in obstacles: obs.draw(screen)
        for pu in power_ups: pu.draw(screen)
        for de in destructibles: de.draw(screen)
        player.draw(screen)
        for p in particles: p.draw(screen)
        for tx in texts:
            s = small.render(tx.text, True, tx.color)
            screen.blit(s, (tx.x - s.get_width()//2, tx.y))

        draw_hud(screen, font, small, score, distance, params["goal"], player.speed, player.nitro, params["name"], paused=False, player_invincible=player.is_invincible(), score_multiplier_active=player.score_multiplier_timer > 0)

        if banner_timer > 0:
            banner_timer -= dt
            screen.blit(banner_surf, (0, 60))

        if not player.alive:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((6, 8, 14, 160))
            screen.blit(overlay, (0, 0))
            t1 = font.render("CRASHED", True, (255, 120, 140))
            t2 = small.render("Press R to restart level • ESC to quit", True, (230, 230, 255))
            screen.blit(t1, (W//2 - t1.get_width()//2, H//2 - 30))
            screen.blit(t2, (W//2 - t2.get_width()//2, H//2 + 10))
            pygame.display.flip()

            # Prompt for score submission on crash
            if firebase_ref:
                if not score_submission_prompt(screen, font, small, W, H, score):
                    return # User quit during submission prompt
            
            while True: # Wait for user input after crash
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: return # Quit game
                    if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
                        return # Quit game
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        return # Restart game (handled by main loop)
                clock.tick(60) # Keep window responsive


    # If game loop ends (e.g., player quits), return to main menu
    return

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Midnight Drag")
    W, H = 900, 600
    screen = pygame.display.set_mode((W, H))
    font = pygame.font.SysFont("Montserrat", 28)
    small = pygame.font.SysFont("Montserrat", 18)

    # Main game loop that handles menu and game states
    while True:
        selected_car = main_menu(screen, font, small, W, H)
        if selected_car:
            game_loop(screen, font, small, W, H, selected_car)
        else:
            # User chose to quit from main menu or leaderboard
            break

    pygame.quit()
    sys.exit()
