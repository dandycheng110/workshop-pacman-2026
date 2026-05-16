"""Pac-Man 2026 進階版 — 在原版工作坊基礎上加入：
1) 關卡系統與難度遞增（速度、能量豆時間、水果分數）
2) 經典 Scatter / Chase 模式切換（含強制反向、四角散開）
3) 水果道具與連吃幽靈 200 / 400 / 800 / 1600 連擊分數
4) 音效、開始選單、暫停、READY!/GAME OVER 動畫
"""

import math

import pyxel

# ============================================================
#   常數設定
# ============================================================

WIDTH = 272
HEIGHT = 304  # 多出空間給上下 HUD（分數、關卡、生命、吃過的水果）
TS = 16
FPS = 30

# Pyxel 內建 16 色調色盤索引
COL_BG = 0
COL_WALL = 5
COL_DOT = 7
COL_PAC = 10
COL_GHOST = [8, 14, 12, 15]  # Blinky 紅、Pinky 粉、Inky 藍、Clyde 橘
COL_SCARED = 1  # 受驚（深藍）
COL_SCARED_FLASH = 7  # 快結束時白色閃爍
COL_EYES = 7
COL_TEXT = 7
COL_READY = 11  # READY! 黃綠
COL_GAMEOVER = 8  # GAME OVER 紅
COL_LEVEL = 11

# 地圖字元
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
MAZE_Y = 24  # 上方留 24px 給 HUD

# 動畫
_PAC_FRAMES = [0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1]
_GHOST_SPRITE_Y = [16, 64, 32, 48]

GHOST_SPAWNS = [
    (tx, ty)
    for ty in range(ROWS)
    for tx in range(COLS)
    if MAZE[ty][tx] == TILE_GHOST_SPAWN
]

# Ghost 散開角落（Scatter 模式各自跑去的格子座標）
SCATTER_TARGETS = [
    (COLS - 2, 1),         # Blinky → 右上
    (1, 1),                # Pinky  → 左上
    (COLS - 2, ROWS - 2),  # Inky   → 右下
    (1, ROWS - 2),         # Clyde  → 左下
]

# Scatter / Chase 排程（秒）— 經典街機 Level 1 配置
SCATTER_CHASE_SCHEDULE = [
    ("scatter", 7 * FPS),
    ("chase", 20 * FPS),
    ("scatter", 7 * FPS),
    ("chase", 20 * FPS),
    ("scatter", 5 * FPS),
    ("chase", 20 * FPS),
    ("scatter", 5 * FPS),
    ("chase", -1),  # 之後永遠追逐
]

# 水果出現位置（中央偏下的豆子點）— 不影響原有豆子收集
FRUIT_TILE = (7, 11)
FRUIT_DURATION = 9 * FPS
FRUIT_SPAWN_THRESHOLDS = [70, 170]  # 吃到第 N 顆豆子時出現

# 連吃幽靈分數
GHOST_COMBO = [200, 400, 800, 1600]

# 全域最高分（簡易記憶於程式執行期間）
HIGH_SCORE = 0


def level_cfg(level: int) -> dict:
    """根據關卡編號回傳難度參數。8 關以後維持最高難度。"""
    L = max(1, min(level, 8))
    fruit_table = ["cherry", "strawberry", "orange", "apple", "melon", "galaxian", "bell", "key"]
    fruit_score = [100, 300, 500, 700, 1000, 2000, 3000, 5000]
    return {
        "pac_speed": min(0.12, 0.08 + (L - 1) * 0.005),
        "ghost_speed": min(0.11, 0.06 + (L - 1) * 0.006),
        "scared_time": max(30, 180 - (L - 1) * 22),
        "fruit": fruit_table[L - 1],
        "fruit_score": fruit_score[L - 1],
        "flash_frames": 60,  # scared 剩餘 X 幀時開始閃爍
    }


# ============================================================
#   工具函式
# ============================================================


def tile_at(tx, ty):
    if 0 <= ty < ROWS and 0 <= tx < COLS:
        return MAZE[ty][tx]
    # 隧道：邊緣若不是牆，視為穿越
    if 0 <= ty < ROWS:
        edge_col = 0 if tx < 0 else COLS - 1
        if MAZE[ty][edge_col] != TILE_WALL:
            return MAZE[ty][tx % COLS]
    return TILE_WALL


def is_wall(tx, ty):
    return tile_at(tx, ty) == TILE_WALL


_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def pick_direction(itx, ity, dx, dy, target_x, target_y, flee=False, allow_tunnel=True):
    """選下一格：追逐取最近、逃跑取最遠；禁止 180° 迴轉。"""
    best = None
    best_score = None
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


# ============================================================
#   幽靈 AI（chase 目標生成器）
# ============================================================


def chase_ai(pac_tx, pac_ty):
    return pac_tx, pac_ty


def make_pinky_ai(pac):
    def ai(pac_tx, pac_ty):
        return pac_tx + 4 * pac.dx, pac_ty + 4 * pac.dy
    return ai


def make_inky_ai(pac, blinky):
    def ai(pac_tx, pac_ty):
        pivot_x = pac_tx + 2 * pac.dx
        pivot_y = pac_ty + 2 * pac.dy
        return 2 * pivot_x - blinky.tx, 2 * pivot_y - blinky.ty
    return ai


def make_clyde_ai(clyde, corner_x, corner_y):
    def ai(pac_tx, pac_ty):
        dist2 = (clyde.tx - pac_tx) ** 2 + (clyde.ty - pac_ty) ** 2
        if dist2 > 64:
            return pac_tx, pac_ty
        return corner_x, corner_y
    return ai


# ============================================================
#   Pacman
# ============================================================


class Pacman:
    def __init__(self):
        self.speed = 0.08
        self.reset()

    def reset(self):
        self.tile_x = 9
        self.tile_y = 14
        self.dx = 0
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0
        self.progress = 0.0
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

    def draw_death(self, t):
        """死亡動畫：先閉合嘴巴，再放出星爆。t 從 0 開始增加。"""
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        if t < 24:
            frame = min(2, t // 8)
            pyxel.blt(px, py, 0, frame * 16, 0, 16, 16, 0)
        else:
            cx, cy = px + 8, py + 8
            r = (t - 24) // 2
            if r < 14:
                for i in range(8):
                    ang = i * math.pi / 4
                    dx_ = int(math.cos(ang) * r)
                    dy_ = int(math.sin(ang) * r)
                    pyxel.pset(cx + dx_, cy + dy_, COL_PAC)
                    pyxel.pset(cx + dx_ + 1, cy + dy_, COL_PAC)


# ============================================================
#   Ghost
# ============================================================


class Ghost:
    def __init__(self, idx):
        self.idx = idx
        self.ai_fn = chase_ai
        self.scatter_target = SCATTER_TARGETS[idx]
        self.speed = 0.06
        self.reset()

    def reset(self):
        self.tile_x, self.tile_y = GHOST_SPAWNS[self.idx]
        for dx, dy in [(0, -1), (1, 0), (-1, 0), (0, 1)]:
            if not is_wall(self.tile_x + dx, self.tile_y + dy):
                self.dx, self.dy = dx, dy
                break
        self.progress = 0.0
        self.scared = False
        self.scared_timer = 0
        self.eaten = False  # 被吃後變眼睛回家
        self.mode = "chase"

    @property
    def tx(self):
        return float(self.tile_x + self.dx * self.progress)

    @property
    def ty(self):
        return float(self.tile_y + self.dy * self.progress)

    def force_reverse(self):
        if not self.eaten:
            self.dx, self.dy = -self.dx, -self.dy

    def set_scared(self, frames):
        if not self.eaten:
            self.scared = True
            self.scared_timer = frames
            # 看到能量豆要倒退（經典規則）
            self.dx, self.dy = -self.dx, -self.dy

    def get_target(self, pac_tx, pac_ty):
        if self.eaten:
            return float(GHOST_SPAWNS[self.idx][0]), float(GHOST_SPAWNS[self.idx][1])
        if self.scared:
            return float(pac_tx), float(pac_ty)
        if self.mode == "scatter":
            return float(self.scatter_target[0]), float(self.scatter_target[1])
        return self.ai_fn(pac_tx, pac_ty)

    def current_speed(self):
        if self.eaten:
            return self.speed * 2.0
        if self.scared:
            return self.speed * 0.6
        return self.speed

    def update(self, pac_tx, pac_ty):
        if self.scared and self.scared_timer > 0:
            self.scared_timer -= 1
            if self.scared_timer == 0:
                self.scared = False

        self.progress += self.current_speed()
        if self.progress >= 1.0:
            new_tx = (self.tile_x + self.dx) % COLS
            new_ty = (self.tile_y + self.dy) % ROWS
            self.tile_x = new_tx
            self.tile_y = new_ty
            self.progress -= 1.0

            if self.eaten and (self.tile_x, self.tile_y) == GHOST_SPAWNS[self.idx]:
                self.eaten = False

            target = self.get_target(pac_tx, pac_ty)
            best = pick_direction(
                self.tile_x,
                self.tile_y,
                self.dx,
                self.dy,
                target[0],
                target[1],
                flee=self.scared and not self.eaten,
                allow_tunnel=True,
            )
            if best:
                self.dx, self.dy = best

    def draw(self):
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)

        if self.eaten:
            # 只畫眼睛
            pyxel.rect(px + 4, py + 6, 3, 4, COL_EYES)
            pyxel.rect(px + 10, py + 6, 3, 4, COL_EYES)
            pyxel.pset(px + 5, py + 8, 0)
            pyxel.pset(px + 11, py + 8, 0)
            return

        if self.scared:
            flashing = self.scared_timer <= 60 and (self.scared_timer // 7) % 2 == 0
            if flashing:
                pyxel.rect(px + 1, py + 3, 14, 12, COL_SCARED_FLASH)
                pyxel.tri(px + 1, py + 14, px + 4, py + 12, px + 7, py + 14, COL_SCARED_FLASH)
                pyxel.tri(px + 7, py + 14, px + 11, py + 12, px + 14, py + 14, COL_SCARED_FLASH)
                pyxel.pset(px + 5, py + 7, COL_GAMEOVER)
                pyxel.pset(px + 10, py + 7, COL_GAMEOVER)
                pyxel.line(px + 4, py + 11, px + 11, py + 11, COL_GAMEOVER)
            else:
                pyxel.blt(px, py, 0, 0, 80, 16, 16, 0)
            return

        sx = ((pyxel.frame_count // 4) % 2) * 16
        pyxel.blt(px, py, 0, sx, _GHOST_SPRITE_Y[self.idx], 16, 16, 0)


# ============================================================
#   Fruit
# ============================================================


class Fruit:
    """水果道具：每關吃豆達門檻時出現於固定點，限時收集。"""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.kind = "cherry"
        self.score = 100
        self.spawn_idx = 0
        self.eaten_pos = None
        self.eaten_timer = 0

    def reset_for_level(self, kind, score):
        self.active = False
        self.timer = 0
        self.kind = kind
        self.score = score
        self.spawn_idx = 0
        self.eaten_pos = None
        self.eaten_timer = 0

    def maybe_spawn(self, dots_eaten):
        if self.spawn_idx < len(FRUIT_SPAWN_THRESHOLDS) and \
                dots_eaten >= FRUIT_SPAWN_THRESHOLDS[self.spawn_idx]:
            self.active = True
            self.timer = FRUIT_DURATION
            self.spawn_idx += 1

    def update(self, pac_tile):
        eaten = False
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False
            elif pac_tile == FRUIT_TILE:
                self.active = False
                self.eaten_pos = pac_tile
                self.eaten_timer = 30
                eaten = True
        if self.eaten_timer > 0:
            self.eaten_timer -= 1
        return eaten

    def draw(self):
        if self.active:
            tx, ty = FRUIT_TILE
            px = MAZE_X + tx * TS + TS // 2
            py = MAZE_Y + ty * TS + TS // 2
            self._draw_fruit(px, py, self.kind)
        if self.eaten_timer > 0 and self.eaten_pos:
            tx, ty = self.eaten_pos
            px = MAZE_X + tx * TS
            py = MAZE_Y + ty * TS - (30 - self.eaten_timer) // 3
            pyxel.text(px, py, f"+{self.score}", COL_READY)

    @staticmethod
    def _draw_fruit(cx, cy, kind):
        """像素風水果圖示。每種水果不同配色與形狀。"""
        if kind == "cherry":
            pyxel.circ(cx - 3, cy + 2, 3, 8)
            pyxel.circ(cx + 3, cy + 3, 3, 8)
            pyxel.line(cx - 3, cy - 1, cx, cy - 4, 11)
            pyxel.line(cx + 3, cy, cx, cy - 4, 11)
        elif kind == "strawberry":
            pyxel.circ(cx, cy + 1, 4, 8)
            pyxel.tri(cx - 4, cy - 2, cx + 4, cy - 2, cx, cy + 2, 8)
            pyxel.rect(cx - 2, cy - 4, 4, 2, 11)
            pyxel.pset(cx - 1, cy, 7)
            pyxel.pset(cx + 1, cy + 2, 7)
        elif kind == "orange":
            pyxel.circ(cx, cy + 1, 4, 9)
            pyxel.line(cx, cy - 4, cx, cy - 2, 11)
            pyxel.line(cx - 1, cy - 3, cx + 1, cy - 3, 11)
        elif kind == "apple":
            pyxel.circ(cx, cy + 1, 4, 8)
            pyxel.line(cx, cy - 4, cx, cy - 2, 4)
            pyxel.pset(cx + 1, cy - 4, 11)
        elif kind == "melon":
            pyxel.circ(cx, cy + 1, 4, 11)
            pyxel.line(cx - 3, cy, cx + 3, cy, 3)
            pyxel.line(cx - 2, cy + 2, cx + 2, cy + 2, 3)
            pyxel.line(cx, cy - 4, cx + 1, cy - 3, 4)
        elif kind == "galaxian":
            pyxel.line(cx, cy - 4, cx, cy + 4, 12)
            pyxel.line(cx - 3, cy, cx + 3, cy, 12)
            pyxel.line(cx - 2, cy - 2, cx + 2, cy + 2, 7)
            pyxel.line(cx + 2, cy - 2, cx - 2, cy + 2, 7)
        elif kind == "bell":
            pyxel.rect(cx - 3, cy - 2, 7, 5, 10)
            pyxel.rect(cx - 4, cy + 3, 9, 1, 10)
            pyxel.rect(cx - 1, cy + 4, 3, 1, 10)
            pyxel.pset(cx, cy - 3, 9)
        elif kind == "key":
            pyxel.circ(cx - 2, cy - 1, 2, 10)
            pyxel.pset(cx - 2, cy - 1, 0)
            pyxel.rect(cx, cy - 1, 5, 2, 10)
            pyxel.pset(cx + 3, cy + 1, 10)
            pyxel.pset(cx + 5, cy + 1, 10)


# ============================================================
#   App（主程式 / 狀態機）
# ============================================================


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Pac-Man 2026", fps=FPS)
        pyxel.load("main.pyxres")
        self._init_sounds()
        self.fruit = Fruit()
        self.pac = Pacman()
        self.ghosts = [Ghost(i) for i in range(4)]
        # 為每隻幽靈指定專屬 chase 目標 AI
        self.ghosts[1].ai_fn = make_pinky_ai(self.pac)
        self.ghosts[2].ai_fn = make_inky_ai(self.pac, self.ghosts[0])
        self.ghosts[3].ai_fn = make_clyde_ai(self.ghosts[3], 1.0, float(ROWS - 2))
        self.state = "menu"
        self.state_timer = 0
        self.level = 1
        self.score = 0
        self.lives = 3
        self.fruit_history = []  # 已過關卡的水果，顯示於下方 HUD
        self.dots = {}
        self.dots_eaten = 0
        self.total_dots = 0
        self.scared_time = 180
        self.flash_frames = 60
        self.ghost_combo = 0
        self.combo_popup = None
        self.combo_popup_timer = 0
        self.mode_idx = 0
        self.mode_timer = SCATTER_CHASE_SCHEDULE[0][1]
        self.current_mode = "scatter"
        pyxel.run(self.update, self.draw)

    # -------- 音效 --------
    def _init_sounds(self):
        pyxel.sounds[0].set("c2", "p", "5", "n", 14)         # 吃豆子（短促）
        pyxel.sounds[1].set("c2g2c3", "p", "6", "n", 8)      # 吃能量豆
        pyxel.sounds[2].set("c1g1c2g2c3", "s", "7", "n", 6)  # 吃幽靈
        pyxel.sounds[3].set("c3a2g2f2e2d2c2g1e1", "p", "6", "f", 10)  # 死亡
        pyxel.sounds[4].set("e2g2c3e3", "s", "6", "n", 7)    # 吃水果
        pyxel.sounds[5].set("c2e2g2c3e3g3c4", "s", "6", "n", 6)  # 過關
        pyxel.sounds[6].set("c3e3g3", "p", "5", "n", 12)     # READY 起音

    def _play(self, ch, snd):
        pyxel.play(ch, snd)

    # -------- 關卡管理 --------
    def start_new_game(self):
        global HIGH_SCORE
        if self.score > HIGH_SCORE:
            HIGH_SCORE = self.score
        self.level = 1
        self.score = 0
        self.lives = 3
        self.fruit_history = []
        self.begin_level()

    def begin_level(self):
        cfg = level_cfg(self.level)
        self.pac.speed = cfg["pac_speed"]
        for g in self.ghosts:
            g.speed = cfg["ghost_speed"]
        self.scared_time = cfg["scared_time"]
        self.flash_frames = cfg["flash_frames"]
        self.fruit.reset_for_level(cfg["fruit"], cfg["fruit_score"])
        self.build_dots()
        self.dots_eaten = 0
        self.ghost_combo = 0
        self.combo_popup = None
        self.combo_popup_timer = 0
        self.reset_positions()
        self.mode_idx = 0
        self.mode_timer = SCATTER_CHASE_SCHEDULE[0][1]
        self.current_mode = SCATTER_CHASE_SCHEDULE[0][0]
        self._apply_mode_to_ghosts()
        self.state = "ready"
        self.state_timer = 60
        self._play(3, 6)

    def build_dots(self):
        self.dots = {}
        self.total_dots = 0
        for ty in range(ROWS):
            for tx in range(COLS):
                c = MAZE[ty][tx]
                if c == TILE_DOT:
                    self.dots[(tx, ty)] = "dot"
                    self.total_dots += 1
                elif c == TILE_POWER:
                    self.dots[(tx, ty)] = "power"
                    self.total_dots += 1

    def reset_positions(self):
        self.pac.reset()
        for g in self.ghosts:
            g.reset()
        self._apply_mode_to_ghosts()

    def _apply_mode_to_ghosts(self):
        for g in self.ghosts:
            if not g.scared and not g.eaten:
                g.mode = self.current_mode

    def _advance_mode(self):
        nxt = self.mode_idx + 1
        if nxt >= len(SCATTER_CHASE_SCHEDULE):
            return
        self.mode_idx = nxt
        name, dur = SCATTER_CHASE_SCHEDULE[nxt]
        self.current_mode = name
        self.mode_timer = dur
        for g in self.ghosts:
            if not g.scared and not g.eaten:
                g.mode = name
                g.force_reverse()

    # -------- 主迴圈 --------
    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.state == "menu":
            self._update_menu()
        elif self.state == "ready":
            self._update_ready()
        elif self.state == "play":
            self._update_play()
        elif self.state == "pause":
            self._update_pause()
        elif self.state == "dead":
            self._update_dead()
        elif self.state == "win":
            self._update_win()
        elif self.state == "levelup":
            self._update_levelup()
        elif self.state == "gameover":
            self._update_gameover()

    def _update_menu(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.start_new_game()

    def _update_ready(self):
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.state = "play"

    def _update_pause(self):
        if pyxel.btnp(pyxel.KEY_P):
            self.state = "play"

    def _update_play(self):
        if pyxel.btnp(pyxel.KEY_P):
            self.state = "pause"
            return

        # Scatter/Chase 排程：scared 期間暫停推進
        any_scared = any(g.scared for g in self.ghosts)
        if not any_scared and self.mode_timer > 0:
            self.mode_timer -= 1
            if self.mode_timer == 0:
                self._advance_mode()

        # Pacman 移動 + 吃豆/能量豆
        eaten = self.pac.update(self.dots)
        if eaten == "dot":
            self.score += 10
            self.dots_eaten += 1
            self._play(0, 0)
        elif eaten == "power":
            self.score += 50
            self.dots_eaten += 1
            self.ghost_combo = 0
            for g in self.ghosts:
                g.set_scared(self.scared_time)
            self._play(0, 1)

        # 水果
        self.fruit.maybe_spawn(self.dots_eaten)
        pac_tile = (int(self.pac.tx + 0.5), int(self.pac.ty + 0.5))
        if self.fruit.update(pac_tile):
            self.score += self.fruit.score
            if not self.fruit_history or self.fruit_history[-1][1] != self.level:
                self.fruit_history.append((self.fruit.kind, self.level))
            self._play(2, 4)

        # 幽靈
        for g in self.ghosts:
            g.update(self.pac.tx, self.pac.ty)

        # 碰撞偵測
        for g in self.ghosts:
            if g.eaten:
                continue
            if abs(self.pac.tx - g.tx) < 0.8 and abs(self.pac.ty - g.ty) < 0.8:
                if g.scared:
                    pts = GHOST_COMBO[min(self.ghost_combo, 3)]
                    self.score += pts
                    self.ghost_combo += 1
                    g.scared = False
                    g.scared_timer = 0
                    g.eaten = True
                    self.combo_popup = (pts, g.tx, g.ty)
                    self.combo_popup_timer = 30
                    self._play(2, 2)
                else:
                    self.lives -= 1
                    self.state = "dead"
                    self.state_timer = 90
                    self._play(3, 3)
                    return

        if self.combo_popup_timer > 0:
            self.combo_popup_timer -= 1

        # 過關
        if not self.dots:
            self.state = "win"
            self.state_timer = 90
            self._play(3, 5)

    def _update_dead(self):
        self.state_timer -= 1
        if self.state_timer <= 0:
            global HIGH_SCORE
            if self.lives <= 0:
                self.state = "gameover"
                self.state_timer = 150
                if self.score > HIGH_SCORE:
                    HIGH_SCORE = self.score
            else:
                self.reset_positions()
                self.state = "ready"
                self.state_timer = 60
                self._play(3, 6)

    def _update_win(self):
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.level += 1
            self.state = "levelup"
            self.state_timer = 45

    def _update_levelup(self):
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.begin_level()

    def _update_gameover(self):
        self.state_timer -= 1
        if self.state_timer <= 0 or pyxel.btnp(pyxel.KEY_SPACE):
            self.state = "menu"

    # -------- 繪製 --------
    def draw(self):
        pyxel.cls(COL_BG)

        if self.state == "menu":
            self._draw_menu()
            return

        self._draw_hud_top()
        self._draw_maze()
        self._draw_dots()
        self.fruit.draw()

        for g in self.ghosts:
            g.draw()

        if self.state == "dead":
            self.pac.draw_death(90 - self.state_timer)
        else:
            self.pac.draw()

        self._draw_hud_bottom()

        # 連擊浮分
        if self.combo_popup and self.combo_popup_timer > 0:
            pts, tx, ty = self.combo_popup
            px = MAZE_X + int(tx * TS)
            py = MAZE_Y + int(ty * TS) - (30 - self.combo_popup_timer) // 3
            pyxel.text(px, py, f"+{pts}", COL_READY)

        # 狀態覆蓋
        if self.state == "ready":
            self._center_text(MAZE_Y + 11 * TS, "READY!", COL_READY)
        elif self.state == "pause":
            self._center_text(HEIGHT // 2 - 4, "PAUSED", COL_TEXT)
            self._center_text(HEIGHT // 2 + 6, "PRESS P", COL_TEXT)
        elif self.state == "win":
            self._center_text(HEIGHT // 2 - 4, f"LEVEL {self.level} CLEAR!", COL_PAC)
        elif self.state == "levelup":
            self._center_text(HEIGHT // 2 - 4, f"LEVEL {self.level}", COL_LEVEL)
        elif self.state == "gameover":
            self._center_text(HEIGHT // 2 - 8, "GAME OVER", COL_GAMEOVER)
            self._center_text(HEIGHT // 2 + 4, f"SCORE {self.score}", COL_TEXT)
            if (pyxel.frame_count // 15) % 2 == 0:
                self._center_text(HEIGHT // 2 + 16, "PRESS SPACE", COL_TEXT)

    def _draw_menu(self):
        title = "PAC-MAN 2026"
        self._center_text(40, title, COL_PAC)
        self._center_text(56, "Advanced Edition", COL_LEVEL)

        cy = 100
        bx = (WIDTH - 5 * 16) // 2
        pyxel.blt(bx, cy, 0, 0, 0, 16, 16, 0)
        sx = ((pyxel.frame_count // 4) % 2) * 16
        for i in range(4):
            pyxel.blt(bx + (i + 1) * 16, cy, 0, sx, _GHOST_SPRITE_Y[i], 16, 16, 0)

        instructions = [
            ("ARROWS/WASD", "Move"),
            ("P", "Pause"),
            ("Q", "Quit"),
            ("SPACE", "Start"),
        ]
        y = 150
        for k, v in instructions:
            t = f"{k:<12}{v}"
            self._center_text(y, t, COL_TEXT)
            y += 10

        if HIGH_SCORE > 0:
            self._center_text(y + 8, f"HIGH SCORE: {HIGH_SCORE}", COL_READY)

        if (pyxel.frame_count // 15) % 2 == 0:
            self._center_text(HEIGHT - 24, "- PRESS SPACE -", COL_PAC)

    def _draw_hud_top(self):
        pyxel.text(4, 4, "SCORE", COL_LEVEL)
        pyxel.text(4, 12, f"{self.score:>6}", COL_TEXT)
        pyxel.text(WIDTH // 2 - 16, 4, "HIGH", COL_LEVEL)
        pyxel.text(WIDTH // 2 - 16, 12, f"{max(HIGH_SCORE, self.score):>6}", COL_TEXT)
        pyxel.text(WIDTH - 44, 4, "LEVEL", COL_LEVEL)
        pyxel.text(WIDTH - 44, 12, f"{self.level:>3}", COL_TEXT)

    def _draw_hud_bottom(self):
        y = MAZE_Y + ROWS * TS + 2
        # 生命：左下
        for i in range(self.lives):
            pyxel.blt(4 + i * 14, y, 0, 0, 0, 12, 12, 0)
        # 水果歷史：右下
        recent = self.fruit_history[-7:]
        for i, (kind, _lv) in enumerate(recent):
            cx = WIDTH - 8 - (len(recent) - i) * 14
            Fruit._draw_fruit(cx, y + 6, kind)
        # 模式指示
        mode_label = self.current_mode.upper()
        col = COL_GAMEOVER if mode_label == "CHASE" else COL_LEVEL
        pyxel.text(WIDTH // 2 - 14, y + 4, mode_label, col)

    def _draw_maze(self):
        for ty in range(ROWS):
            for tx in range(COLS):
                if MAZE[ty][tx] == TILE_WALL:
                    px = MAZE_X + tx * TS
                    py = MAZE_Y + ty * TS
                    pyxel.rect(px, py, TS, TS, COL_WALL)

    def _draw_dots(self):
        for (tx, ty), kind in self.dots.items():
            px = MAZE_X + tx * TS + TS // 2
            py = MAZE_Y + ty * TS + TS // 2
            if kind == "dot":
                pyxel.rect(px - 1, py - 1, 3, 3, COL_DOT)
            else:
                if (pyxel.frame_count // 8) % 2 == 0:
                    pyxel.circ(px, py, 4, COL_PAC)

    @staticmethod
    def _center_text(y, s, col):
        x = (WIDTH - len(s) * pyxel.FONT_WIDTH) // 2
        pyxel.text(x, y, s, col)


App()
