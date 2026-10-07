import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy


COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50
FPS = 60

FREEZE_DURATION = 300


class GameEngine:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont(
            "monospace",
            38,
            bold=True
        )

        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)

        # Player
        self.player = Player(0, 0)

        # Task 1: Three enemies starting at different corners
        self.enemies = [
            Enemy(ROWS - 1, COLS - 1),
            Enemy(ROWS - 1, 0),
            Enemy(0, COLS - 1)
        ]

        self.exit_rect = pygame.Rect(
            (COLS // 2) * CELL + 5,
            (ROWS // 2) * CELL + 5,
            CELL - 10,
            CELL - 10
        )

        # Task 3: Power pellet
        self.power_pellet_cell = (ROWS // 2, 1)

        pellet_r, pellet_c = self.power_pellet_cell

        self.power_pellet_rect = pygame.Rect(
            pellet_c * CELL + CELL // 2 - 8,
            pellet_r * CELL + CELL // 2 - 8,
            16,
            16
        )

        self.power_pellet_active = True
        self.freeze_timer = 0

        # Task 2: Difficulty ramp
        self.start_time = pygame.time.get_ticks()
        self.speed_tier = 0

        # Task 4: Survival score
        self.score = 0

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

    def update(self):
        if self.caught or self.won:
            return

        keys = pygame.key.get_pressed()

        self.player.move(
            keys,
            self.walls,
            ROWS,
            COLS
        )

        # Task 4: Survival score
        # The game runs at 60 FPS, so score roughly represents frames alive.
        self.score += 1

        # Task 2: Increase difficulty every 15 seconds
        elapsed_time = pygame.time.get_ticks() - self.start_time

        new_speed_tier = elapsed_time // 15000

        if new_speed_tier != self.speed_tier:
            self.speed_tier = new_speed_tier

            new_interval = max(
                5,
                20 - (self.speed_tier * 2)
            )

            for enemy in self.enemies:
                enemy.move_interval = new_interval

        # Task 3: Power pellet freeze timer
        if self.freeze_timer > 0:
            self.freeze_timer -= 1

            if self.freeze_timer <= 0:
                for enemy in self.enemies:
                    enemy.frozen = False

        # Collect power pellet
        if (
            self.power_pellet_active
            and self.player.rect.colliderect(self.power_pellet_rect)
        ):
            self.power_pellet_active = False

            # Freeze all enemies for 300 frames = 5 seconds at 60 FPS
            self.freeze_timer = FREEZE_DURATION

            for enemy in self.enemies:
                enemy.frozen = True

        # Task 1: Update every enemy independently
        for enemy in self.enemies:
            enemy.update(
                self.walls,
                self.player,
                ROWS,
                COLS
            )

        # Check collision with every enemy
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.caught = True
                break

        # Check exit
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def draw(self):
        self.screen.fill((230, 220, 210))

        wc = (50, 40, 60)

        # Draw maze
        for r in range(ROWS):
            for c in range(COLS):

                x, y = c * CELL, r * CELL
                w = self.walls[r][c]

                if w[0]:
                    pygame.draw.line(
                        self.screen,
                        wc,
                        (x, y),
                        (x + CELL, y),
                        3
                    )

                if w[1]:
                    pygame.draw.line(
                        self.screen,
                        wc,
                        (x, y + CELL),
                        (x + CELL, y + CELL),
                        3
                    )

                if w[2]:
                    pygame.draw.line(
                        self.screen,
                        wc,
                        (x + CELL, y),
                        (x + CELL, y + CELL),
                        3
                    )

                if w[3]:
                    pygame.draw.line(
                        self.screen,
                        wc,
                        (x, y),
                        (x, y + CELL),
                        3
                    )

        # Exit
        pygame.draw.rect(
            self.screen,
            (80, 200, 80),
            self.exit_rect,
            border_radius=4
        )

        lbl = self.font.render(
            "EXIT",
            True,
            (20, 80, 20)
        )

        self.screen.blit(
            lbl,
            (self.exit_rect.x + 2, self.exit_rect.y + 6)
        )

        # Task 3: Draw power pellet
        if self.power_pellet_active:
            pygame.draw.circle(
                self.screen,
                (255, 220, 40),
                self.power_pellet_rect.center,
                8
            )

        # Player
        self.player.draw(self.screen)

        # All enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HUD
        hud = pygame.Rect(
            0,
            ROWS * CELL,
            WIDTH,
            50
        )

        pygame.draw.rect(
            self.screen,
            (30, 30, 50),
            hud
        )

        # Task 2 + Task 4 HUD
        survived_seconds = self.score // FPS

        info = self.font.render(
            f"Survived: {survived_seconds}s   "
            f"Speed Tier: {self.speed_tier}   "
            f"R=Restart",
            True,
            (200, 200, 200)
        )

        self.screen.blit(
            info,
            (8, ROWS * CELL + 14)
        )

        # Game overlays
        if self.caught:
            self._overlay(
                f"CAUGHT!  Score: {self.score // FPS}s",
                (220, 60, 60)
            )

        if self.won:
            self._overlay(
                f"ESCAPED!  Score: {self.score // FPS}s",
                (80, 220, 80)
            )

        pygame.display.flip()

    def _overlay(self, text, color):
        surf = pygame.Surface(
            (WIDTH, ROWS * CELL),
            pygame.SRCALPHA
        )

        surf.fill((0, 0, 0, 140))

        self.screen.blit(
            surf,
            (0, 0)
        )

        msg = self.big_font.render(
            text,
            True,
            color
        )

        sub = self.font.render(
            "Press R to Restart",
            True,
            (200, 200, 200)
        )

        self.screen.blit(
            msg,
            (
                WIDTH // 2 - msg.get_width() // 2,
                ROWS * CELL // 2 - 30
            )
        )

        self.screen.blit(
            sub,
            (
                WIDTH // 2 - sub.get_width() // 2,
                ROWS * CELL // 2 + 20
            )
        )

    def run(self):
        running = True

        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()