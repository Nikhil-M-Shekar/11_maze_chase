import pygame
from game.maze import CELL

SPEED = 2


class Player:
    def __init__(self, r, c):
        self.r, self.c = r, c

        cx = c * CELL + CELL // 2
        cy = r * CELL + CELL // 2

        self.rect = pygame.Rect(
            cx - 10,
            cy - 10,
            20,
            20
        )

        self.color = (60, 120, 220)

    @property
    def hitbox(self):
        # Slightly smaller than the sprite, so near-misses don't count
        return self.rect.inflate(-6, -6)

    def move(self, keys, walls, rows, cols):
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -SPEED

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -SPEED

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = SPEED

        # Move horizontally
        if dx != 0:
            new_rect = self.rect.move(dx, 0)

            if self._can_move(
                new_rect,
                walls,
                rows,
                cols,
                dx,
                0
            ):
                self.rect = new_rect

        # Move vertically
        if dy != 0:
            new_rect = self.rect.move(0, dy)

            if self._can_move(
                new_rect,
                walls,
                rows,
                cols,
                0,
                dy
            ):
                self.rect = new_rect

    def _can_move(self, rect, walls, rows, cols, dx, dy):

        # Don't allow the player outside the maze
        if rect.left < 0:
            return False

        if rect.right > cols * CELL:
            return False

        if rect.top < 0:
            return False

        if rect.bottom > rows * CELL:
            return False

        # Current cell
        current_r = self.rect.centery // CELL
        current_c = self.rect.centerx // CELL

        # New cell
        new_r = rect.centery // CELL
        new_c = rect.centerx // CELL

        # Moving vertically into another cell
        if new_r != current_r:

            if new_r > current_r:
                # Moving DOWN
                if walls[current_r][current_c][1]:
                    return False

            else:
                # Moving UP
                if walls[current_r][current_c][0]:
                    return False

        # Moving horizontally into another cell
        if new_c != current_c:

            if new_c > current_c:
                # Moving RIGHT
                if walls[current_r][current_c][2]:
                    return False

            else:
                # Moving LEFT
                if walls[current_r][current_c][3]:
                    return False

        return True

    def draw(self, screen):
        pygame.draw.ellipse(
            screen,
            self.color,
            self.rect
        )


class Enemy:
    def __init__(self, r, c):
        self.r, self.c = r, c

        cx = c * CELL + CELL // 2
        cy = r * CELL + CELL // 2

        self.rect = pygame.Rect(
            cx - 12,
            cy - 12,
            24,
            24
        )

        self.color = (220, 60, 60)

        # Enemy movement timer
        self.timer = 0

        # Lower value = faster enemy
        self.move_interval = 20

        # Used by power pellet
        self.frozen = False

        # True whenever the enemy can't hurt the player
        # (frozen, or in the grace period right after a freeze)
        self.harmless = False

    @property
    def hitbox(self):
        # Much smaller than the sprite: the enemy has to really touch you
        return self.rect.inflate(-12, -12)

    def update(self, walls, player, rows, cols):
        from game.maze import bfs

        # Frozen enemies don't move
        if self.frozen:
            return

        self.timer += 1

        if self.timer >= self.move_interval:
            self.timer = 0

            # Player's current cell
            pr = player.rect.centery // CELL
            pc = player.rect.centerx // CELL

            # BFS finds the next direction toward player
            step = bfs(
                walls,
                (self.r, self.c),
                (pr, pc),
                rows,
                cols
            )

            if step:
                dr, dc = step

                self.r += dr
                self.c += dc

                cx = self.c * CELL + CELL // 2
                cy = self.r * CELL + CELL // 2

                self.rect.center = (cx, cy)

    def draw(self, screen):

        # Frozen enemies become blue; enemies in the post-freeze grace
        # period blink light blue/red to show they are still harmless
        if self.frozen:
            color = (100, 180, 255)
        elif self.harmless:
            if (pygame.time.get_ticks() // 150) % 2 == 0:
                color = (150, 190, 240)
            else:
                color = self.color
        else:
            color = self.color

        pygame.draw.rect(
            screen,
            color,
            self.rect,
            border_radius=5
        )

        # Eyes
        for ex in [
            self.rect.x + 4,
            self.rect.x + 14
        ]:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (ex, self.rect.y + 8),
                4
            )

            pygame.draw.circle(
                screen,
                (0, 0, 0),
                (ex + 1, self.rect.y + 8),
                2
            )

        # Frozen indicator
        if self.frozen:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                self.rect.center,
                4
            )