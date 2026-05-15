import pyxel

WIDTH = 272
HEIGHT = 272
TS = 16

COL_BG = 0
COL_WALL = 5
COL_DOT = 7
COL_PAC = 10
COL_GHOST = [8, 14, 12, 15]
COL_SCARED = 6
COL_TEXT = 7

TILE_EMPTY = "0"
TILE_WALL = "1"
TILE_DOT = "2"
TILE_POWER = "3"
TILE_GHOST_SPAWN = "4"

MAZE = [
    "1111111111111111",
    "1222222112222221",
    "1211212112121121",
    "1211212112121121",
    "1322222222222231",
    "1211212112121121",
    "2222212112122222",
    "1111214004121111",
    "1111214004121111",
    "2222212112122222",
    "1211212112121121",
    "1322222222222231",
    "1211212112121121",
    "1211212112121121",
    "1222222112222221",
    "1111111111111111",
]

ROWS = len(MAZE)
COLS = len(MAZE[0])
MAZE_X = (WIDTH - COLS * TS) // 2
MAZE_Y = 16

# Pac-Man animation frames (16×16 sprites at y=0): 0=open, 1=half-open, 2=closed
_PAC_FRAMES = [0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1]
# Sprite bank y-coord for each ghost index (Blinky, Pinky, Inky, Clyde)
_GHOST_SPRITE_Y = [16, 64, 32, 48]

GHOST_SPAWNS = [
    (tx, ty)
    for ty in range(ROWS)
    for tx in range(COLS)
    if MAZE[ty][tx] == TILE_GHOST_SPAWN
]


def tile_at(tx, ty):
    if 0 <= ty < ROWS and 0 <= tx < COLS:
        return MAZE[ty][tx]
    if 0 <= ty < ROWS:
        edge_col = 0 if tx < 0 else COLS - 1
        if MAZE[ty][edge_col] != TILE_WALL:
            return MAZE[ty][tx % COLS]
    return TILE_WALL


def is_wall(tx, ty):
    return tile_at(tx, ty) == TILE_WALL


_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def pick_direction(
    itx: int,
    ity: int,
    dx: int,
    dy: int,
    target_x: float,
    target_y: float,
    flee: bool = False,
    allow_tunnel: bool = True,
) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_score: float | None = None
    for ddx, ddy in _DIRS:
        if ddx == -dx and ddy == -dy:
            continue
        ntx, nty = itx + ddx, ity + ddy
        if not allow_tunnel and not (0 <= ntx < COLS and 0 <= nty < ROWS):
            continue
        if is_wall(ntx, nty):
            continue
        dist2 = (ntx - target_x) ** 2 + (nty - target_y) ** 2
        score = -dist2 if flee else dist2
        if best_score is None or score < best_score:
            best_score = score
            best = (ddx, ddy)
    return best


def chase_ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
    return pac_tx, pac_ty


def make_pinky_ai(pac):
    def ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
        return pac_tx + 4 * pac.dx, pac_ty + 4 * pac.dy

    return ai


def make_inky_ai(pac, blinky):
    def ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
        pivot_x = pac_tx + 2 * pac.dx
        pivot_y = pac_ty + 2 * pac.dy
        return 2 * pivot_x - blinky.tx, 2 * pivot_y - blinky.ty

    return ai


def make_clyde_ai(clyde, corner_x: float, corner_y: float):
    def ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
        dist2 = (clyde.tx - pac_tx) ** 2 + (clyde.ty - pac_ty) ** 2
        if dist2 > 64:  # > 8 tiles
            return pac_tx, pac_ty
        return corner_x, corner_y

    return ai


class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tile_x = 9
        self.tile_y = 14
        self.dx = 0
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0
        self.progress = 0.0
        self.speed = 0.08
        self.anim = 0

    @property
    def tx(self):
        return float(self.tile_x + self.dx * self.progress)

    @property
    def ty(self):
        return float(self.tile_y + self.dy * self.progress)

    def update(self, dots):
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.next_dx, self.next_dy = -1, 0
        elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.next_dx, self.next_dy = 1, 0
        elif pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
            self.next_dx, self.next_dy = 0, -1
        elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
            self.next_dx, self.next_dy = 0, 1

        if self.dx == 0 and self.dy == 0:
            if not is_wall(self.tile_x + self.next_dx, self.tile_y + self.next_dy):
                self.dx, self.dy = self.next_dx, self.next_dy

        if self.dx != 0 or self.dy != 0:
            self.progress += self.speed
            if self.progress >= 1.0:
                self.tile_x = (self.tile_x + self.dx) % COLS
                self.tile_y = (self.tile_y + self.dy) % ROWS
                self.progress -= 1.0
                if not is_wall(self.tile_x + self.next_dx, self.tile_y + self.next_dy):
                    self.dx, self.dy = self.next_dx, self.next_dy
                elif is_wall(self.tile_x + self.dx, self.tile_y + self.dy):
                    self.dx, self.dy = 0, 0
                    self.progress = 0.0

        itx = int(self.tx + 0.5)
        ity = int(self.ty + 0.5)
        key = (itx, ity)
        if key in dots:
            return dots.pop(key)
        return None

    def draw(self):
        self.anim = (self.anim + 1) % 12
        sx = _PAC_FRAMES[self.anim] * 16
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        w = -16 if self.dx > 0 else 16
        pyxel.blt(px, py, 0, sx, 0, w, 16, 0)


class Ghost:
    def __init__(self, idx):
        self.idx = idx
        self.ai_fn = chase_ai
        self.reset()

    def reset(self):
        self.tile_x, self.tile_y = GHOST_SPAWNS[self.idx]
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if not is_wall(self.tile_x + dx, self.tile_y + dy):
                self.dx, self.dy = dx, dy
                break
        self.progress = 0.0
        self.speed = 0.06
        self.scared = False
        self.scared_timer = 0

    @property
    def tx(self):
        return float(self.tile_x + self.dx * self.progress)

    @property
    def ty(self):
        return float(self.tile_y + self.dy * self.progress)

    def update(self, pac_tx, pac_ty):
        if self.scared and self.scared_timer > 0:
            self.scared_timer -= 1
            if self.scared_timer == 0:
                self.scared = False

        self.progress += self.speed
        if self.progress >= 1.0:
            new_tx = self.tile_x + self.dx
            new_ty = self.tile_y + self.dy
            if not (0 <= new_tx < COLS and 0 <= new_ty < ROWS):
                self.dx, self.dy = -self.dx, -self.dy
                self.progress = 0.0
                return
            self.tile_x = new_tx
            self.tile_y = new_ty
            self.progress -= 1.0
            target = self.ai_fn(pac_tx, pac_ty)
            best = pick_direction(self.tile_x, self.tile_y, self.dx, self.dy, *target, flee=self.scared, allow_tunnel=False)
            if best:
                self.dx, self.dy = best

    def draw(self):
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        if self.scared:
            pyxel.blt(px, py, 0, 0, 80, 16, 16, 0)
        else:
            sx = ((pyxel.frame_count // 4) % 2) * 16
            pyxel.blt(px, py, 0, sx, _GHOST_SPRITE_Y[self.idx], 16, 16, 0)


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Pac-Man", fps=30)
        pyxel.load("main.pyxres")
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.state = "play"
        self.state_timer = 0
        self.build_dots()
        self.pac = Pacman()
        self.ghosts = [Ghost(i) for i in range(4)]
        self.ghosts[1].ai_fn = make_pinky_ai(self.pac)
        self.ghosts[2].ai_fn = make_inky_ai(self.pac, self.ghosts[0])
        self.ghosts[3].ai_fn = make_clyde_ai(self.ghosts[3], 1.0, float(ROWS - 2))

    def build_dots(self):
        self.dots = {}
        for ty in range(ROWS):
            for tx in range(COLS):
                c = MAZE[ty][tx]
                if c == TILE_DOT:
                    self.dots[(tx, ty)] = "dot"
                elif c == TILE_POWER:
                    self.dots[(tx, ty)] = "power"

    def reset_positions(self):
        self.pac.reset()
        for g in self.ghosts:
            g.reset()

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.state == "play":
            eaten = self.pac.update(self.dots)
            if eaten == "dot":
                self.score += 10
            elif eaten == "power":
                self.score += 50
                for g in self.ghosts:
                    g.scared = True
                    g.scared_timer = 150

            for g in self.ghosts:
                g.update(self.pac.tx, self.pac.ty)

            for g in self.ghosts:
                if abs(self.pac.tx - g.tx) < 0.8 and abs(self.pac.ty - g.ty) < 0.8:
                    if g.scared:
                        g.reset()
                        self.score += 200
                    else:
                        self.lives -= 1
                        self.state = "dead"
                        self.state_timer = 60
                        break

            if not self.dots:
                self.state = "win"
                self.state_timer = 90

        elif self.state == "dead":
            self.state_timer -= 1
            if self.state_timer <= 0:
                if self.lives <= 0:
                    self.state = "gameover"
                    self.state_timer = 120
                else:
                    self.reset_positions()
                    self.state = "play"

        elif self.state in ("win", "gameover"):
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.reset_game()

    def draw(self):
        pyxel.cls(COL_BG)

        pyxel.text(4, 4, f"SCORE:{self.score}", COL_TEXT)
        pyxel.text(WIDTH - 38, 4, f"LIVES:{self.lives}", COL_TEXT)

        for ty in range(ROWS):
            for tx in range(COLS):
                px = MAZE_X + tx * TS
                py = MAZE_Y + ty * TS
                if MAZE[ty][tx] == TILE_WALL:
                    pyxel.rect(px, py, TS, TS, COL_WALL)

        for (tx, ty), kind in self.dots.items():
            px = MAZE_X + tx * TS + TS // 2
            py = MAZE_Y + ty * TS + TS // 2
            if kind == "dot":
                pyxel.rect(px - 1, py - 1, 3, 3, COL_DOT)
            else:
                if (pyxel.frame_count // 8) % 2 == 0:
                    pyxel.circ(px, py, 4, COL_PAC)

        for g in self.ghosts:
            g.draw()

        if self.state != "dead" or self.state_timer > 30:
            self.pac.draw()

        if self.state == "win":
            pyxel.text(WIDTH // 2 - 20, HEIGHT // 2, "YOU WIN!", COL_PAC)
        elif self.state == "gameover":
            pyxel.text(WIDTH // 2 - 22, HEIGHT // 2, "GAME OVER", 8)


App()
