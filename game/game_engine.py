import pygame

from game.maze import generate_maze, shortest_path, CELL
from game.entities import Player, Enemy


COLS, ROWS = 13, 11

WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50

FPS = 60

# -------------------------
# BALANCE (tuned to be easy)
# -------------------------

# Enemies are harmless and frozen for 8 seconds after a pellet.
FREEZE_DURATION = 8 * FPS

# After the freeze ends, enemies stay harmless (and blink) for 2 more
# seconds so one standing on top of the player can't cause an instant loss.
GRACE_DURATION = 2 * FPS

# Enemies wait 3 seconds at the start before they begin chasing.
HEAD_START = 3 * FPS

# Enemy speed ramp: every 12 seconds, move interval drops by 5 frames
# (starts at 80, a cell every ~1.3s), but never below 45 frames
# (a cell every 0.75s, still slower than the player's ~0.37s per cell).
RAMP_INTERVAL = 12 * FPS
START_INTERVAL = 80
INTERVAL_STEP = 5
MIN_INTERVAL = 45

# Fair-maze rules: a new maze is regenerated until the shortest route from
# the start to the exit is short and never passes close to an enemy spawn.
MAX_SOLUTION_LEN = 32
SPAWN_BUFFER = 5

# Three pellets: one near the start, two flanking the exit.
PELLET_CELLS = [(1, 2), (ROWS // 2, COLS // 2 - 3), (ROWS // 2, COLS // 2 + 3)]


class GameEngine:

    def __init__(self):

        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("monospace", 18)
        self.small_font = pygame.font.SysFont("monospace", 13, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)

        self.reset()

    def reset(self):

        # Enemy spawn corners and exit cell (needed to build a fair maze)
        spawns = [(ROWS - 1, COLS - 1), (ROWS - 1, 0), (0, COLS - 1)]
        exit_cell = (ROWS // 2, COLS // 2)

        # Maze: regenerate until the route to the exit is short and keeps
        # clear of every enemy spawn, so the game is always winnable.
        for _ in range(1000):

            self.walls = generate_maze(COLS, ROWS)

            route = shortest_path(self.walls, (0, 0), exit_cell, ROWS, COLS)

            if len(route) <= MAX_SOLUTION_LEN and all(
                abs(r - sr) + abs(c - sc) >= SPAWN_BUFFER
                for r, c in route
                for sr, sc in spawns
            ):
                break

        # Player
        self.player = Player(0, 0)

        # Enemies (one per remaining corner)
        self.enemies = [Enemy(r, c) for r, c in spawns]

        for enemy in self.enemies:
            enemy.move_interval = START_INTERVAL

        # Exit
        exit_r = ROWS // 2
        exit_c = COLS // 2

        self.exit_cell = (exit_r, exit_c)

        self.exit_rect = pygame.Rect(
            exit_c * CELL + 5,
            exit_r * CELL + 5,
            CELL - 10,
            CELL - 10,
        )

        # Power pellets
        self.pellets = []

        for r, c in PELLET_CELLS:
            self.pellets.append({
                "rect": pygame.Rect(
                    c * CELL + CELL // 2 - 8,
                    r * CELL + CELL // 2 - 8,
                    16,
                    16,
                ),
                "active": True,
            })

        self.freeze_timer = 0
        self.grace_timer = 0

        # Difficulty / timing (frame based, so it stays in sync with
        # the freeze timer and never drifts with window lag)
        self.speed_tier = 0
        self.head_start = HEAD_START

        # Score
        self.score = 0

        # State
        self.caught = False
        self.won = False

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    self.reset()

        return True

    @property
    def player_safe(self):
        """True while enemies cannot hurt the player."""
        return self.freeze_timer > 0 or self.grace_timer > 0

    def update(self):

        # Stop updating after game ends
        if self.caught or self.won:
            return

        # Player movement
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)

        # Survival score
        self.score += 1

        # Difficulty ramp
        new_tier = self.score // RAMP_INTERVAL

        if new_tier != self.speed_tier:

            self.speed_tier = new_tier

            new_interval = max(
                MIN_INTERVAL,
                START_INTERVAL - self.speed_tier * INTERVAL_STEP,
            )

            for enemy in self.enemies:
                enemy.move_interval = new_interval

        # Head start countdown
        if self.head_start > 0:
            self.head_start -= 1

        # Freeze countdown, then post-freeze grace period
        if self.freeze_timer > 0:

            self.freeze_timer -= 1

            if self.freeze_timer == 0:

                for enemy in self.enemies:
                    enemy.frozen = False
                    enemy.timer = 0

                self.grace_timer = GRACE_DURATION

        elif self.grace_timer > 0:

            self.grace_timer -= 1

        # Collect power pellets
        player_box = self.player.hitbox

        for pellet in self.pellets:

            if pellet["active"] and player_box.colliderect(pellet["rect"]):

                pellet["active"] = False

                self.freeze_timer = FREEZE_DURATION
                self.grace_timer = 0

                for enemy in self.enemies:
                    enemy.frozen = True

        # Enemy movement (after the head start)
        if self.head_start == 0:

            for enemy in self.enemies:
                enemy.update(self.walls, self.player, ROWS, COLS)

        # Enemy collision: only when the player is NOT protected
        safe = self.player_safe

        for enemy in self.enemies:
            enemy.harmless = safe

        if not safe:

            for enemy in self.enemies:

                if player_box.colliderect(enemy.hitbox):
                    self.caught = True
                    break

        # Exit
        player_r = self.player.rect.centery // CELL
        player_c = self.player.rect.centerx // CELL

        if (player_r, player_c) == self.exit_cell:

            if self.player.rect.colliderect(self.exit_rect):
                self.won = True

    def draw(self):

        self.screen.fill((230, 220, 210))

        wall_color = (50, 40, 60)

        # Maze
        for r in range(ROWS):

            for c in range(COLS):

                x = c * CELL
                y = r * CELL

                w = self.walls[r][c]

                if w[0]:
                    pygame.draw.line(
                        self.screen, wall_color, (x, y), (x + CELL, y), 3
                    )

                if w[1]:
                    pygame.draw.line(
                        self.screen, wall_color,
                        (x, y + CELL), (x + CELL, y + CELL), 3
                    )

                if w[2]:
                    pygame.draw.line(
                        self.screen, wall_color,
                        (x + CELL, y), (x + CELL, y + CELL), 3
                    )

                if w[3]:
                    pygame.draw.line(
                        self.screen, wall_color, (x, y), (x, y + CELL), 3
                    )

        # Exit
        pygame.draw.rect(
            self.screen, (80, 200, 80), self.exit_rect, border_radius=4
        )

        label = self.small_font.render("EXIT", True, (20, 80, 20))

        self.screen.blit(
            label,
            label.get_rect(center=self.exit_rect.center),
        )

        # Power pellets (gently pulsing)
        pulse = 7 + (pygame.time.get_ticks() // 200) % 2

        for pellet in self.pellets:

            if pellet["active"]:
                pygame.draw.circle(
                    self.screen, (255, 220, 40),
                    pellet["rect"].center, pulse
                )
                pygame.draw.circle(
                    self.screen, (200, 150, 0),
                    pellet["rect"].center, pulse, 2
                )

        # Player and enemies
        self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HUD
        hud = pygame.Rect(0, ROWS * CELL, WIDTH, 50)
        pygame.draw.rect(self.screen, (30, 30, 50), hud)

        parts = [f"Survived: {self.score // FPS}s"]

        if self.head_start > 0:
            parts.append(f"GET READY {self.head_start // FPS + 1}")
        elif self.freeze_timer > 0:
            parts.append(f"FREEZE: {self.freeze_timer / FPS:.1f}s")
        elif self.grace_timer > 0:
            parts.append(f"SAFE: {self.grace_timer / FPS:.1f}s")

        parts.append(f"Speed: {self.speed_tier}")
        parts.append("R=Restart")

        info = self.font.render("  ".join(parts), True, (200, 200, 200))

        self.screen.blit(info, (8, ROWS * CELL + 16))

        # Game over
        if self.caught:
            self._overlay(
                f"CAUGHT! Score: {self.score // FPS}s", (220, 60, 60)
            )

        if self.won:
            self._overlay(
                f"ESCAPED! Score: {self.score // FPS}s", (80, 220, 80)
            )

    def _overlay(self, text, color):

        surf = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 140))
        self.screen.blit(surf, (0, 0))

        msg = self.big_font.render(text, True, color)
        sub = self.font.render("Press R to Restart", True, (200, 200, 200))

        self.screen.blit(
            msg, (WIDTH // 2 - msg.get_width() // 2, ROWS * CELL // 2 - 30)
        )

        self.screen.blit(
            sub, (WIDTH // 2 - sub.get_width() // 2, ROWS * CELL // 2 + 20)
        )

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            # Push the finished frame to the window (without this the
            # window stays black, because drawing happens off-screen)
            pygame.display.flip()

            self.clock.tick(FPS)

        pygame.quit()
