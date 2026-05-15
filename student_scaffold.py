"""
Pac-Man 學生練習腳本
依照 tutorial/ 各章節的「練習」說明，逐步把 pass 替換成你的實作。
執行方式（在專案根目錄）：uv run python student_scaffold.py
"""

import pyxel

# ── Constants 常數定義（顏色、格子、地圖） ───────────────────────────────

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

_GHOST_SPRITE_Y = [16, 64, 32, 48]

GHOST_SPAWNS = []  # 第二章練習：用 list comprehension 從 MAZE 掃描 TILE_GHOST_SPAWN


# ── Utilities 工具函式（位置計算、碰撞偵測、方向選擇） ───────────────────


def tile_at(tx, ty):
    # 第二章練習：格子查詢與隧道邏輯
    if 0 <= ty < ROWS and 0 <= tx < COLS:
        return MAZE[ty][tx]
    return TILE_WALL  # ← 完成第二章練習後，在這行之前加入隧道邏輯


def is_wall(tx, ty):
    return tile_at(tx, ty) == TILE_WALL


_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def pick_direction(itx, ity, dx, dy, target_x, target_y, flee=False, allow_tunnel=True):
    # 第五章練習：方向選擇演算法
    pass  # ← 完成第五章練習後，把這行 pass 替換成你的實作


# ── AI Functions 四隻幽靈的目標計算策略 ──────────────────────────────────


def chase_ai(pac_tx, pac_ty):
    # 第六章練習：Blinky——回傳小精靈目前位置
    return pac_tx, pac_ty  # ← 完成第六章練習後，把這行替換成你的實作


def make_pinky_ai(pac):
    # 第六章練習：Pinky——超前預測
    def ai(pac_tx, pac_ty):
        return pac_tx, pac_ty  # ← 完成第六章練習後，把這行替換成你的實作

    return ai


def make_inky_ai(pac, blinky):
    # 第六章練習：Inky——夾擊策略
    def ai(pac_tx, pac_ty):
        return pac_tx, pac_ty  # ← 完成第六章練習後，把這行替換成你的實作

    return ai


def make_clyde_ai(clyde, corner_x, corner_y):
    # 第六章練習：Clyde——近則逃、遠則追
    def ai(pac_tx, pac_ty):
        return pac_tx, pac_ty  # ← 完成第六章練習後，把這行替換成你的實作

    return ai


# ── Ghost Class 幽靈類別 ─────────────────────────────────────────────────


class Ghost:
    def __init__(self, idx):
        self.idx = idx
        self.ai_fn = chase_ai
        self.reset()

    def reset(self):
        self.tile_x, self.tile_y = -2, -2  # 第二章練習
        self.dx, self.dy = 1, 0  # 第二章練習
        self.progress = 0.0
        self.speed = 0.06
        self.scared = False
        self.scared_timer = 0

    @property
    def tx(self):
        return float(self.tile_x)  # 第三章練習

    @property
    def ty(self):
        return float(self.tile_y)  # 第三章練習

    def update(self, pac_tx, pac_ty):
        # 第五章練習：幽靈移動邏輯
        pass  # ← 完成第五章練習後，把這行 pass 替換成你的實作

    def draw(self):
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        # 第七章練習：加入動畫與受驚狀態，目前先靜態顯示第一幀
        pyxel.blt(px, py, 0, 0, _GHOST_SPRITE_Y[self.idx], 16, 16, 0)


# ── Pacman Class 玩家類別 ────────────────────────────────────────────────


class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tile_x = COLS // 2  # 第二章練習
        self.tile_y = ROWS // 2  # 第二章練習
        self.dx = -1  # 第二章練習
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0
        self.progress = 0.0
        self.speed = 0.08
        self.anim = 0

    @property
    def tx(self):
        # 第三章練習
        return float(self.tile_x)

    @property
    def ty(self):
        # 第三章練習
        return float(self.tile_y)

    def update(self, dots):
        # 第三章練習：把整個函式體替換成鍵盤控制與牆壁碰撞邏輯
        # 第四章練習：在 return None 前加入吃豆子邏輯

        # 暫時：無視牆壁，依初始方向移動（完成第三章後請整個替換）
        self.progress += self.speed
        if self.progress >= 1.0:
            self.tile_x = (self.tile_x + self.dx) % COLS
            self.progress -= 1.0
        return None

    def draw(self):
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        # 第四章練習：加入動畫與方向翻轉，目前先靜態顯示第一幀
        pyxel.blt(px, py, 0, 0, 0, 16, 16, 0)


# ── App Class 遊戲主迴圈 ─────────────────────────────────────────────────


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Pac-Man", fps=30)
        # 第一章練習：畫好 Sprite 後，在這裡加入 pyxel.load("main.pyxres")
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.state = "play"
        self.state_timer = 0
        self.ghost_combo = 0
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

            # 第八章練習：計分與觸發受驚
            pass  # ← 完成第八章練習後，把這行 pass 替換成你的實作

            for g in self.ghosts:
                g.update(self.pac.tx, self.pac.ty)

            for g in self.ghosts:
                if abs(self.pac.tx - g.tx) < 0.8 and abs(self.pac.ty - g.ty) < 0.8:
                    if g.scared:
                        g.reset()
                        self.score += 200  # 第十章練習：改成連鎖計分公式
                        self.ghost_combo += 1
                    else:
                        # 第八章練習：碰撞後切換到 dead 狀態
                        pass  # ← 完成第八章練習後，把這行 pass 替換成你的實作

            # 第八章練習：吃完所有豆子後切換到 win 狀態
            pass  # ← 完成第八章練習後，把這行 pass 替換成你的實作

        elif self.state == "dead":
            # 第八章練習：dead 狀態計時與轉移
            pass  # ← 完成第八章練習後，把這行 pass 替換成你的實作

        elif self.state in ("win", "gameover"):
            # 第八章練習：win / gameover 狀態計時與重置
            pass  # ← 完成第八章練習後，把這行 pass 替換成你的實作

    def draw(self):
        pyxel.cls(COL_BG)
        # UI：分數與生命
        pyxel.text(4, 4, f"SCORE:{self.score}", COL_TEXT)
        pyxel.text(WIDTH - 38, 4, f"LIVES:{self.lives}", COL_TEXT)

        # 初始提示：讓學生第一次執行時看到畫面有東西
        if self.state == "play" and self.score == 0:
            pyxel.text(WIDTH // 2 - 32, HEIGHT // 2 - 15, "PAC-MAN START!", pyxel.frame_count % 16)
            pyxel.text(WIDTH // 2 - 45, HEIGHT // 2, "Follow the tutorial!", COL_TEXT)
            pyxel.text(WIDTH // 2 - 75, HEIGHT // 2 + 15, "NYCU GDC 20 Games Workshop | Pac-Man", 5)

        # 第二章練習：繪製牆壁與豆子
        pass  # ← 完成第二章練習後，把這行 pass 替換成你的實作

        for g in self.ghosts:
            g.draw()

        if self.state != "dead" or self.state_timer > 30:
            self.pac.draw()

        if self.state == "win":
            pyxel.text(WIDTH // 2 - 20, HEIGHT // 2, "YOU WIN!", COL_PAC)
        elif self.state == "gameover":
            pyxel.text(WIDTH // 2 - 22, HEIGHT // 2, "GAME OVER", 8)


App()
