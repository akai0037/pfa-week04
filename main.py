import os
import random

import pygame

# --- Settings ---
WIDTH, HEIGHT = 800, 450
FPS = 60
GROUND_Y = 400          # y position of the ground line
BALL_RADIUS = 20
MOVE_SPEED = 5          # pixels per frame left/right
JUMP_STRENGTH = 15      # starting upward speed of a jump
GRAVITY = 0.7           # how fast the ball falls back down

START_SPEED = 5         # how fast the world moves left at the start
SPEED_UP = 0.1          # extra speed added every second
MAX_SPEED = 12          # the world never moves faster than this

COIN_RADIUS = 10

# the cat picture: its size on screen and the box used for hits
PLAYER_H = 60                     # height of the cat on screen in pixels
HITBOX_W, HITBOX_H = 34, 54       # a little smaller than the picture, so hits feel fair
EAT_FRAMES = 15                   # how long the mouth stays open after eating a coin
HERE = os.path.dirname(os.path.abspath(__file__))

POPCAT_H = 170                    # height of the pop cat on the game over screen
POPCAT_FRAMES = 25                # how many frames the spin-in animation takes
POPCAT_MIN_SCALE = 0.5            # size of the game over cat with 0 coins
POPCAT_GROW = 0.1                 # extra size for every coin eaten
POPCAT_MAX_SCALE = 2.2            # the cat never gets bigger than this

BG_COLOR = (30, 30, 40)
GROUND_COLOR = (90, 200, 120)
STRIPE_COLOR = (70, 170, 100)
OBSTACLE_COLOR = (200, 90, 200)
PLATFORM_COLOR = (240, 210, 60)
COIN_COLOR = (255, 215, 0)
COIN_EDGE = (200, 150, 0)
TEXT_COLOR = (255, 255, 255)
OVER_COLOR = (230, 70, 70)
BUTTON_COLOR = (70, 70, 90)
BUTTON_HOVER = (110, 110, 140)

BUTTON_W, BUTTON_H = 180, 50
RESTART_BUTTON = pygame.Rect(WIDTH // 2 - BUTTON_W - 15, HEIGHT // 2 + 60, BUTTON_W, BUTTON_H)
QUIT_BUTTON = pygame.Rect(WIDTH // 2 + 15, HEIGHT // 2 + 60, BUTTON_W, BUTTON_H)


# ---------- game state ----------

def new_game():
    """Return everything a fresh round needs, stored in one dict."""
    return {
        "ball": make_ball(),
        "obstacles": [],       # purple blocks: touching one ends the game
        "platforms": [],       # yellow blocks: the ball can stand on top
        "coins": [],           # gold coins: touching one adds to the count
        "next_spawn": 300,     # pixels the world must move before the next thing appears
        "scroll": 0,           # total distance moved (used for the ground stripes)
        "frames": 0,           # frames survived, used for the timer
        "coin_count": 0,
        "game_over": False,
        "popcat": None,        # the pop cat shown on the game over screen
    }


def make_ball():
    """Create the ball as a dict holding its position and vertical speed."""
    return {
        "x": WIDTH // 3,
        "y": GROUND_Y - BALL_RADIUS,
        "vy": 0,              # vertical speed (negative = going up)
        "on_ground": True,
        "eat_timer": 0,       # counts down while the mouth is open
    }


def load_sprites():
    """Load the normal and coin-eating cat pictures, scaled to PLAYER_H tall."""
    sprites = {}
    for key, filename in (("normal", "player.png"), ("eat", "player_eat.png")):
        img = pygame.image.load(os.path.join(HERE, filename)).convert_alpha()
        w = round(img.get_width() * PLAYER_H / img.get_height())
        sprites[key] = pygame.transform.smoothscale(img, (w, PLAYER_H))
    return sprites


def load_popcats():
    """Load every picture for the game over screen from the popcats folder."""
    files = []
    folder = os.path.join(HERE, "popcats")
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith(".png"):
                files.append(os.path.join(folder, name))
    pictures = []
    for path in files:
        img = pygame.image.load(path).convert_alpha()
        w = round(img.get_width() * POPCAT_H / img.get_height())
        pictures.append(pygame.transform.smoothscale(img, (w, POPCAT_H)))
    print(f"Loaded {len(pictures)} game over pictures:", ", ".join(os.path.basename(f) for f in files))
    return pictures


popcat_bag = []


def next_popcat_picture(pictures):
    """Like drawing cards: every picture shows once before any repeats."""
    if not popcat_bag:
        popcat_bag.extend(pictures)
        random.shuffle(popcat_bag)
    return popcat_bag.pop()


def popcat_scale(coin_count):
    """More coins = bigger cat on the game over screen."""
    return min(POPCAT_MAX_SCALE, POPCAT_MIN_SCALE + coin_count * POPCAT_GROW)


def make_popcat(pictures, coin_count):
    """Pick a random pop cat with a random tilt, side and spin; its size comes from the coins."""
    if not pictures:
        return None    # popcats folder is empty: show no picture
    img = next_popcat_picture(pictures)
    if random.random() < 0.5:
        img = pygame.transform.flip(img, True, False)
    return {
        "img": img,
        "angle": random.uniform(-30, 30),           # final tilt in degrees
        "scale": popcat_scale(coin_count),
        "x": random.choice([random.randint(110, 170), random.randint(630, 690)]),
        "y": random.randint(190, 260),
        "spin": random.choice([-1, 1]),             # which way it spins in
        "frame": 0,
    }


def draw_popcat(screen, popcat):
    """Draw the pop cat spinning and growing in, then staying at its final tilt."""
    t = min(1, popcat["frame"] / POPCAT_FRAMES)
    # ease out with a little overshoot, so it "pops"
    grow = 1 + 2.2 * (t - 1) ** 3 + 1.2 * (t - 1) ** 2
    angle = popcat["angle"] + popcat["spin"] * 360 * (1 - t)
    scale = max(0.01, popcat["scale"] * grow)
    img = pygame.transform.rotozoom(popcat["img"], angle, scale)
    screen.blit(img, img.get_rect(center=(popcat["x"], popcat["y"])))
    popcat["frame"] += 1


def player_hitbox(ball):
    """The rectangle used for hits: centered on the cat, feet on ball's bottom."""
    bottom = ball["y"] + BALL_RADIUS
    return pygame.Rect(int(ball["x"] - HITBOX_W / 2), int(bottom - HITBOX_H), HITBOX_W, HITBOX_H)


def current_speed(game):
    """The world gets faster the longer you survive, up to MAX_SPEED."""
    seconds = game["frames"] / FPS
    return min(MAX_SPEED, START_SPEED + seconds * SPEED_UP)


# ---------- ball ----------

def handle_input(ball):
    """Move left/right with the arrow keys or A/D."""
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        ball["x"] -= MOVE_SPEED
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        ball["x"] += MOVE_SPEED


def jump(ball):
    """Start a jump, but only if the ball is standing on something."""
    if ball["on_ground"]:
        ball["vy"] = -JUMP_STRENGTH
        ball["on_ground"] = False


def apply_gravity(ball, platforms):
    """Pull the ball down, and land it on the ground or on top of a yellow block."""
    old_bottom = ball["y"] + BALL_RADIUS
    ball["vy"] += GRAVITY
    ball["y"] += ball["vy"]
    ball["on_ground"] = False

    # land on a yellow block only when falling onto its top
    # (the ball can jump up through it from below)
    if ball["vy"] >= 0:
        new_bottom = ball["y"] + BALL_RADIUS
        for p in platforms:
            over_block = p.left - BALL_RADIUS / 2 < ball["x"] < p.right + BALL_RADIUS / 2
            if over_block and old_bottom <= p.top <= new_bottom:
                ball["y"] = p.top - BALL_RADIUS
                ball["vy"] = 0
                ball["on_ground"] = True
                return

    if ball["y"] >= GROUND_Y - BALL_RADIUS:
        ball["y"] = GROUND_Y - BALL_RADIUS
        ball["vy"] = 0
        ball["on_ground"] = True


# ---------- obstacles, platforms and coins ----------

def spawn_something(game):
    """Add a random new thing at the right edge of the screen."""
    roll = random.random()
    if roll < 0.40:
        # purple block sitting on the ground
        w = random.randint(25, 45)
        h = random.randint(30, 70)
        game["obstacles"].append(pygame.Rect(WIDTH, GROUND_Y - h, w, h))
    elif roll < 0.65:
        # purple block floating in the air: stay low and let it pass over you
        w = random.randint(30, 60)
        h = random.randint(20, 40)
        bottom = random.randint(GROUND_Y - 160, GROUND_Y - PLAYER_H - 8)
        game["obstacles"].append(pygame.Rect(WIDTH, bottom - h, w, h))
    else:
        # yellow block to jump onto, with a row of coins on top
        w = random.randint(110, 180)
        top = GROUND_Y - random.randint(80, 140)
        platform = pygame.Rect(WIDTH, top, w, 16)
        game["platforms"].append(platform)
        n = random.randint(1, 3)
        for i in range(n):
            cx = platform.centerx + (i - (n - 1) / 2) * 35
            game["coins"].append({"x": cx, "y": top - 35})
        # also put a purple block on the ground under some of them
        if random.random() < 0.5:
            game["obstacles"].append(pygame.Rect(platform.centerx - 15, GROUND_Y - 40, 30, 40))


def next_gap(speed):
    """How far (in pixels) to wait before spawning again; bigger when faster."""
    return random.randint(int(speed * 35) + 120, int(speed * 70) + 220)


def update_world(game, speed):
    """Move everything left, spawn new things, and remove what left the screen."""
    for ob in game["obstacles"]:
        ob.x -= speed
    for p in game["platforms"]:
        p.x -= speed
    for c in game["coins"]:
        c["x"] -= speed

    game["obstacles"] = [ob for ob in game["obstacles"] if ob.right > 0]
    game["platforms"] = [p for p in game["platforms"] if p.right > 0]
    game["coins"] = [c for c in game["coins"] if c["x"] > -COIN_RADIUS]

    game["scroll"] += speed
    game["next_spawn"] -= speed
    if game["next_spawn"] <= 0:
        spawn_something(game)
        game["next_spawn"] = next_gap(speed)


def circle_hits_rect(x, y, radius, rect):
    """True if a circle at (x, y) overlaps a rectangle."""
    cx = max(rect.left, min(x, rect.right))
    cy = max(rect.top, min(y, rect.bottom))
    return (x - cx) ** 2 + (y - cy) ** 2 < radius ** 2


def rects_overlap(a, b):
    """True if two rectangles overlap."""
    return a.left < b.right and b.left < a.right and a.top < b.bottom and b.top < a.bottom


def hits_obstacle(ball, obstacles):
    """Return True if the cat touches any purple block."""
    box = player_hitbox(ball)
    for ob in obstacles:
        if rects_overlap(box, ob):
            return True
    return False


def collect_coins(game):
    """Remove every coin the cat touches, add it to the count, and open the mouth."""
    ball = game["ball"]
    box = player_hitbox(ball)
    if ball["eat_timer"] > 0:
        ball["eat_timer"] -= 1
    kept = []
    for c in game["coins"]:
        if circle_hits_rect(c["x"], c["y"], COIN_RADIUS, box):
            game["coin_count"] += 1
            ball["eat_timer"] = EAT_FRAMES
        else:
            kept.append(c)
    game["coins"] = kept


def is_out_of_bounds(ball):
    """Return True if any part of the cat has left the window."""
    box = player_hitbox(ball)
    return box.left < 0 or box.right > WIDTH or box.top < 0


# ---------- drawing ----------

def background_color(seconds):
    if seconds < 10:
        return (30, 30, 40)
    elif seconds < 20:
        return (50, 20, 70)
    elif seconds < 30:
        return (70, 20, 60)
    else:
        return (70, 20, 30)

def draw(screen, game, font, sprites):
    """Draw the world, the ball, and the timer and coin count at the top."""
    screen.fill(background_color(game["frames"] / FPS))
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    # stripes on the ground slide left so the world looks like it is moving
    for x in range(-(int(game["scroll"]) % 60), WIDTH, 60):
        pygame.draw.rect(screen, STRIPE_COLOR, (x, GROUND_Y + 15, 30, 6))

    for p in game["platforms"]:
        pygame.draw.rect(screen, PLATFORM_COLOR, p, border_radius=4)
    for ob in game["obstacles"]:
        pygame.draw.rect(screen, OBSTACLE_COLOR, ob, border_radius=4)
    for c in game["coins"]:
        pygame.draw.circle(screen, COIN_COLOR, (int(c["x"]), int(c["y"])), COIN_RADIUS)
        pygame.draw.circle(screen, COIN_EDGE, (int(c["x"]), int(c["y"])), COIN_RADIUS, 2)

    ball = game["ball"]
    img = sprites["eat"] if ball["eat_timer"] > 0 else sprites["normal"]
    feet = (int(ball["x"]), int(ball["y"] + BALL_RADIUS))
    screen.blit(img, img.get_rect(midbottom=feet))

    if not game["game_over"]:
        seconds = game["frames"] / FPS
        hud = font.render(f"Time: {seconds:.1f}s    Coins: {game['coin_count']}", True, TEXT_COLOR)
        screen.blit(hud, (15, 12))


def draw_button(screen, rect, label, font):
    """Draw one button; it gets lighter when the mouse is over it."""
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(screen, BUTTON_HOVER if hovered else BUTTON_COLOR, rect, border_radius=10)
    text = font.render(label, True, TEXT_COLOR)
    screen.blit(text, text.get_rect(center=rect.center))


def draw_game_over(screen, game, big_font, small_font):
    """Dim the screen and show GAME OVER, the final time and coins, and the buttons."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    if game["popcat"]:
        draw_popcat(screen, game["popcat"])

    title = big_font.render("GAME OVER", True, OVER_COLOR)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))

    seconds = game["frames"] / FPS
    result = small_font.render(f"Time: {seconds:.1f}s    Coins: {game['coin_count']}", True, TEXT_COLOR)
    screen.blit(result, result.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 15)))

    draw_button(screen, RESTART_BUTTON, "Restart", small_font)
    draw_button(screen, QUIT_BUTTON, "Quit Game", small_font)


# ---------- main loop ----------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pop Cat Jump")
    clock = pygame.time.Clock()

    big_font = pygame.font.Font(None, 96)
    small_font = pygame.font.Font(None, 36)
    sprites = load_sprites()
    popcats = load_popcats()

    game = new_game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif not game["game_over"] and event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    jump(game["ball"])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game["game_over"]:
                if RESTART_BUTTON.collidepoint(event.pos):
                    game = new_game()
                elif QUIT_BUTTON.collidepoint(event.pos):
                    running = False

        if not game["game_over"]:
            ball = game["ball"]
            speed = current_speed(game)

            handle_input(ball)
            update_world(game, speed)
            apply_gravity(ball, game["platforms"])
            collect_coins(game)
            game["frames"] += 1

            if is_out_of_bounds(ball) or hits_obstacle(ball, game["obstacles"]):
                game["game_over"] = True
                game["popcat"] = make_popcat(popcats, game["coin_count"])

        draw(screen, game, small_font, sprites)
        if game["game_over"]:
            draw_game_over(screen, game, big_font, small_font)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
