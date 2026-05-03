# 用 Pyxel 製作 Pac-Man

## 事前準備

安裝 [uv](https://docs.astral.sh/uv/getting-started/installation/) 後，在專案目錄執行：

```bash
uv run python main.py
```

即可啟動遊戲。方向鍵或 WASD 控制小精靈移動，Q 鍵離開。

---

## 第一章：認識 Pyxel 與專案架構

### Pyxel 是什麼？

[Pyxel](https://github.com/kitao/pyxel) 是一個專為復古像素風格遊戲設計的 Python 遊戲引擎。它的設計哲學刻意限制資源：

| 限制 | 數值 |
|------|------|
| 最大螢幕大小 | 256 × 256 px |
| 調色盤 | 16 色（固定） |
| 音效聲道 | 4 |
| 背景音樂軌道 | 8 |

這些限制和 1980 年代的遊戲硬體相近，讓製作者能專注在遊戲設計本身，而不是無窮無盡的視覺調整。

### 專案結構

整個遊戲只有一個檔案 `main.py`，由上到下大致分為：

```
常數定義（顏色、格子、地圖）
  ↓
工具函式（位置計算、碰撞偵測、方向選擇）
  ↓
AI 函式（四隻幽靈的目標計算策略）
  ↓
Pacman 類別（玩家）
  ↓
Ghost 類別（幽靈）
  ↓
App 類別（遊戲主迴圈）
```

### Pyxel 的遊戲迴圈

Pyxel 採用固定頻率的遊戲迴圈。呼叫 `pyxel.run(update, draw)` 後，每一幀會依序執行：

1. **update**：處理輸入、更新遊戲邏輯
2. **draw**：根據目前狀態渲染畫面

```python
pyxel.init(WIDTH, HEIGHT, title="Pac-Man", fps=30)
pyxel.run(self.update, self.draw)
```

`fps=30` 代表每秒執行 30 次 update 和 draw，這也是本專案中所有「計時器」和「速度」的時間基準。

---

## 第二章：顏色、格子與地圖

### Pyxel 的 16 色調色盤

Pyxel 的顏色是用 0–15 的整數表示，對應固定的調色盤：

```python
COL_BG    = 0   # 黑色（背景）
COL_WALL  = 5   # 深藍色（牆壁）
COL_DOT   = 7   # 白色（豆子）
COL_PAC   = 10  # 黃色（小精靈）
COL_GHOST = [8, 14, 12, 15]  # 四隻幽靈各自的顏色
COL_SCARED = 6  # 藍色（受驚幽靈）
COL_TEXT  = 7   # 白色（文字）
```

> **調色盤索引**
> 顏色 8 是粉紅色（Blinky）、14 是橘黃色（Pinky）、12 是水藍色（Inky）、15 是米白色（Clyde）。Pyxel 的調色盤參考自 PICO-8，與原版 Pac-Man 街機的配色不完全相同，但足夠讓玩家辨認。

### 格子座標系統（Tile Coordinate System）

遊戲地圖是由 8×8 像素的「格子（tile）」組成。座標系統有兩層：

| 座標系統 | 單位 | 用途 |
|---------|------|------|
| **格子座標**（`tx`, `ty`）| 格子數 | 地圖邏輯、碰撞判斷 |
| **像素座標**（`px`, `py`）| 像素 | 繪圖 |

兩者之間的轉換：

```python
TS = 8          # Tile Size：每格 8 像素
MAZE_X = (WIDTH - COLS * TS) // 2   # 地圖在螢幕上的起始 x 像素
MAZE_Y = 16                          # 地圖在螢幕上的起始 y 像素

# 格子 → 像素
px = MAZE_X + tx * TS
py = MAZE_Y + ty * TS
```

### 地圖定義

地圖用一個字串陣列表示，每個字元代表一種格子類型：

```python
TILE_EMPTY      = "0"   # 空地
TILE_WALL       = "1"   # 牆壁
TILE_DOT        = "2"   # 普通豆子（+10 分）
TILE_POWER      = "3"   # 能量豆（+50 分，讓幽靈進入受驚狀態）
TILE_GHOST_SPAWN = "4"  # 幽靈出生點

MAZE = [
    "1111111111111111",
    "1222222112222221",
    "1211212112121121",
    ...
    "1111111111111111",
]
```

這種「資料即程式碼」的設計讓地圖一目了然——你可以直接看著字串想像出迷宮的形狀。地圖共 16 列 × 16 行，存取某格的函式：

```python
ROWS = len(MAZE)       # 16
COLS = len(MAZE[0])    # 16

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
```

> **邊界處理與隧道**
> 座標超出水平範圍時，`tile_at` 先檢查該列的邊緣格子是否為牆壁。若邊緣是牆（一般列），直接回傳 `TILE_WALL`，保持原有行為。若邊緣是開口（隧道列），則用 `tx % COLS` 取得對側的對應格子，讓碰撞偵測（`is_blocked`）和方向選擇（`pick_direction`）都能「看穿」隧道的另一端。垂直方向超出邊界時一律回傳 `TILE_WALL`。

### 幽靈出生點

遊戲初始化時，掃描地圖一次，把所有 `TILE_GHOST_SPAWN` 的位置收集起來：

```python
GHOST_SPAWNS = [
    (tx, ty)
    for ty in range(ROWS)
    for tx in range(COLS)
    if MAZE[ty][tx] == TILE_GHOST_SPAWN
]
```

之後建立幽靈時，`Ghost(idx)` 直接取 `GHOST_SPAWNS[idx]` 作為初始位置，不需要在類別裡寫死座標。

---

## 第三章：移動與碰撞偵測

本章是整個遊戲物理系統的核心，理解這部分才能讀懂小精靈和幽靈的移動邏輯。

### 浮點數格子座標

小精靈和幽靈的位置用**浮點數格子座標**表示（例如 `tx = 9.0`, `ty = 7.5`）。這讓角色可以在格子之間平滑移動，而不是每幀跳一整格。

每幀，角色的位置更新方式是：

```
新位置 = 舊位置 + 方向向量 × 速度
```

以小精靈為例，速度是 `0.08`（每幀移動 0.08 格）。以 30 fps 計算，每秒大約移動 2.4 格。

### near_grid：何時可以轉彎？

角色只能在「接近格子中心」時轉彎，否則可能卡在牆角或穿牆：

```python
def near_grid(v: float) -> bool:
    return abs(v - round(v)) < 0.2
```

這個函式判斷一個浮點座標是否距離最近的整數格子中心不到 0.2 格。只有當 `near_grid(tx)` 且 `near_grid(ty)` 都為 `True` 時，角色才被允許嘗試轉彎。

> **為什麼是 0.2？**
> 速度是每幀 0.08 格。如果門檻設太小（例如 0.05），角色可能在對齊格子的那幀剛好超過門檻而錯過轉彎時機。0.2 提供了足夠的「容錯空間」，讓轉彎操作感覺靈敏。

### is_blocked：角色是否撞牆？

移動前要先檢查目標位置是否和牆壁重疊。這裡用「四個角落」的方式來近似角色佔用的空間：

```python
def is_blocked(nx: float, ny: float, margin: float) -> bool:
    corners = [
        (nx + margin,     ny + margin),      # 左上
        (nx + 1 - margin, ny + margin),      # 右上
        (nx + margin,     ny + 1 - margin),  # 左下
        (nx + 1 - margin, ny + 1 - margin),  # 右下
    ]
    return any(is_wall(int(px), int(py)) for px, py in corners)
```

`margin` 參數控制角色碰撞框的大小：
- 小精靈：`margin = 0.15`（略小於半格，穿越通道較寬鬆）
- 幽靈：`margin = 0.12`（更小，幽靈比小精靈更容易通過窄道）

> **為什麼用四角而不是圓形碰撞？**
> 格子式地圖用四角近似是個務實的選擇。圓形碰撞需要計算距離，邏輯更複雜，但對於方格迷宮帶來的體驗改善有限。四角只需要整數截斷和查表，計算成本極低。

### 穿越隧道

本地圖在第 6 列和第 9 列設有隧道開口——這兩列的首尾格子是 `TILE_DOT`（`"2"`）而非 `TILE_WALL`（`"1"`）：

```
row 6: "2222212112122222"   ← 兩端為 '2'，形成左右隧道口
row 9: "2222212112122222"
```

位置更新時用取餘數（`%`）實現穿越：

```python
self.tx = nx % COLS
self.ty = ny % ROWS
```

當角色移出地圖右側（`nx >= COLS`）或左側（`nx < 0`），取餘數後會出現在對側。

但光靠 `%` 還不夠——碰撞偵測（`is_blocked`）和方向選擇（`pick_direction`）在計算時會存取地圖邊界之外的格子座標，若 `tile_at` 對任何超出範圍的座標都回傳 `TILE_WALL`，角色就會在即將離開邊緣時被牆壁擋住，或者幽靈 AI 永遠不會選擇朝出口前進。因此 `tile_at` 在超出水平邊界時會先確認該列是否有隧道開口，再決定要回傳 `TILE_WALL` 還是對側的格子。

---

## 第四章：小精靈——輸入處理與動畫

### Pacman 類別

```python
class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tx = 9.0      # 起始格子座標
        self.ty = 14.0
        self.dx = 0        # 目前移動方向
        self.dy = 0
        self.next_dx = 0   # 玩家請求的下一個方向
        self.next_dy = 0
        self.speed = 0.08
        self.anim = 0      # 動畫計時器
```

`dx`/`dy` 是**目前方向**，`next_dx`/`next_dy` 是**玩家想要轉的方向**。分開儲存是為了讓玩家可以「提前預輸入」——在還沒到格子中心前就按下方向鍵，到達中心時自動轉彎，手感更流暢。

### 輸入處理

```python
def update(self, dots):
    if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
        self.next_dx, self.next_dy = -1, 0
    elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
        self.next_dx, self.next_dy = 1, 0
    elif pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
        self.next_dx, self.next_dy = 0, -1
    elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
        self.next_dx, self.next_dy = 0, 1
```

> **`btn` vs `btnp`**
> `pyxel.btn(key)` 在按鍵**持續按住**期間每幀都回傳 `True`，適合連續移動。
> `pyxel.btnp(key)` 只在按下的**第一幀**回傳 `True`，適合選單操作或單次觸發。

### 轉彎邏輯

```python
    nx = self.tx + self.dx * self.speed
    ny = self.ty + self.dy * self.speed

    if near_grid(self.tx) and near_grid(self.ty):
        itx = int(round(self.tx))
        ity = int(round(self.ty))
        ntx = itx + self.next_dx
        nty = ity + self.next_dy
        if not is_wall(ntx, nty):
            self.dx = self.next_dx
            self.dy = self.next_dy

    if not is_blocked(nx, ny, 0.15):
        self.tx = nx % COLS
        self.ty = ny % ROWS
    else:
        self.dx = 0
        self.dy = 0
```

這段邏輯有三個步驟：

1. **計算新位置**：沿目前方向走一步
2. **嘗試轉彎**：如果接近格子中心，且玩家請求的方向不是牆壁，就轉過去
3. **套用移動**：如果新位置不被牆壁阻擋就移動，否則停下

注意步驟 2 只修改方向 (`dx`/`dy`)，不立刻移動位置。實際移動在步驟 3 用**更新後的方向**計算。

### 吃豆子

```python
    itx = int(self.tx + 0.5)
    ity = int(self.ty + 0.5)
    key = (itx, ity)
    if key in dots:
        return dots.pop(key)
    return None
```

`int(self.tx + 0.5)` 等同於四捨五入，取小精靈目前最近的格子。如果該格有豆子，就從字典中移除並回傳豆子類型（`"dot"` 或 `"power"`）。回傳值在 `App.update` 中用來加分或觸發「受驚」狀態。

### 嘴巴動畫

```python
def draw(self):
    self.anim = (self.anim + 1) % 20
    mouth = (self.anim % 10) / 10.0 * 0.45
    ...
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                ang = math.atan2(dy, dx) - angle_offset
                # 正規化角度到 [-π, π]
                while ang > math.pi:  ang -= 2 * math.pi
                while ang < -math.pi: ang += 2 * math.pi
                if abs(ang) > mouth * math.pi:
                    pyxel.pset(cx + dx, cy + dy, COL_PAC)
```

動畫原理：

- `anim` 每幀加一，`% 20` 讓它在 0–19 之間循環
- `anim % 10` 讓嘴巴在 0–9 之間來回（`% 10` 後再除以 10.0 得到 0.0–0.9 的比例）
- `mouth * math.pi` 是嘴巴張開的角度（最大約 0.45π ≈ 81°）
- 遍歷半徑 3 的圓形區域內每個像素，計算該像素相對於小精靈中心的角度
- 只有角度「不在嘴巴開口範圍內」的像素才被繪製

`angle_offset` 讓嘴巴朝向移動方向。`math.atan2(self.dy, self.dx)` 回傳方向向量的角度（弧度）。

---

## 第五章：方向選擇演算法

### pick_direction 函式

這是四隻幽靈共用的移動核心，根據目標位置選擇最佳前進方向：

```python
_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # 右、左、下、上

def pick_direction(
    itx: int, ity: int,        # 幽靈目前所在格子（整數）
    dx: int, dy: int,          # 幽靈目前移動方向
    target_x: float, target_y: float,  # 目標位置
    flee: bool = False,        # True = 逃離目標
) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_score: float | None = None
    for ddx, ddy in _DIRS:
        if ddx == -dx and ddy == -dy:
            continue            # 不允許 180° 迴轉
        ntx, nty = itx + ddx, ity + ddy
        if is_wall(ntx, nty):
            continue            # 不走進牆壁
        dist2 = (ntx - target_x) ** 2 + (nty - target_y) ** 2
        score = -dist2 if flee else dist2
        if best_score is None or score < best_score:
            best_score = score
            best = (ddx, ddy)
    return best
```

關鍵設計決策：

1. **不允許 180° 迴轉**：`if ddx == -dx and ddy == -dy: continue`。這是原版 Pac-Man 的規則——幽靈除非進入「受驚」狀態的切換時刻，否則不能原地掉頭。
2. **追逐模式**（`flee=False`）：選擇讓下一格**距離目標最遠**的方向（`score = dist2`，選最小的 score 即選最小的距離，所以用 `dist2` 取正）。
   
   > 等等，`score = dist2` 取最小，代表選距離最近的方向，這才是追逐！`flee=False` 是追逐，`flee=True` 是逃跑，此時 `score = -dist2`，取最小的 `-dist2` 即選最大的 `dist2`，也就是選離目標最遠的方向。邏輯正確。

3. **逃跑模式**（`flee=True`，受驚狀態）：選擇讓下一格**距離目標最遠**的方向。

> **為什麼用距離平方（dist²）而不是距離？**
> 比較大小不需要開根號。`dist² = dx² + dy²` 計算量只有乘法和加法，比 `sqrt(dx² + dy²)` 快很多，而且不影響排序結果。在遊戲中，能省下的計算成本都值得省。

---

## 第六章：四隻幽靈的 AI

原版 Pac-Man 的四隻幽靈各有不同的追逐策略，這也是遊戲耐玩度的關鍵。本實作還原了原版的 AI 邏輯。

### 幽靈類別

```python
class Ghost:
    def __init__(self, idx):
        self.idx = idx
        self.ai_fn = chase_ai   # 預設 AI：直接追小精靈
        self.reset()

    def reset(self):
        self.tx = float(GHOST_SPAWNS[self.idx][0])
        self.ty = float(GHOST_SPAWNS[self.idx][1])
        self.dx, self.dy = 1, 0
        self.speed = 0.06
        self.scared = False
        self.scared_timer = 0
```

幽靈透過 `ai_fn` 這個**策略函式（strategy function）**決定目標。這讓四隻幽靈可以共用同一個 `Ghost` 類別，只替換 AI 邏輯。

### 幽靈的 update 邏輯

```python
def update(self, pac_tx, pac_ty):
    # 受驚計時
    if self.scared and self.scared_timer > 0:
        self.scared_timer -= 1
        if self.scared_timer == 0:
            self.scared = False

    # 在格子中心時決定下一步方向
    if near_grid(self.tx) and near_grid(self.ty):
        itx = int(round(self.tx))
        ity = int(round(self.ty))
        target = self.ai_fn(pac_tx, pac_ty)
        best = pick_direction(itx, ity, self.dx, self.dy, *target, flee=self.scared)
        if best:
            self.dx, self.dy = best

    # 移動
    nx = self.tx + self.dx * self.speed
    ny = self.ty + self.dy * self.speed
    if not is_blocked(nx, ny, 0.12):
        self.tx = nx % COLS
        self.ty = ny % ROWS
```

幽靈的移動和小精靈最大的不同是：幽靈沒有「玩家預輸入」，方向完全由 `ai_fn` 計算得來的目標決定。每次到達格子中心，就重新詢問 AI 要往哪走。

### Blinky（直接追逐）

```python
def chase_ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
    return pac_tx, pac_ty
```

Blinky 是最簡單的幽靈——目標就是小精靈目前的位置。在所有方向都不被阻擋的情況下，他會以最短路徑直線追逐。

### Pinky（超前預測）

```python
def make_pinky_ai(pac):
    def ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
        return pac_tx + 4 * pac.dx, pac_ty + 4 * pac.dy
    return ai
```

Pinky 的目標是小精靈**前方 4 格**的位置。他不追小精靈目前在哪，而是預測小精靈接下來會去哪，試圖堵截前方。

> **工廠函式（Factory Function）**
> `make_pinky_ai(pac)` 回傳一個閉包（closure）。回傳的 `ai` 函式「記住」了 `pac` 這個物件的參考，每次呼叫時都能讀取小精靈目前的 `dx`/`dy`。這讓 AI 策略可以依賴遊戲中其他物件的狀態，同時保持介面統一（接受 `pac_tx, pac_ty`，回傳目標座標）。

### Inky（夾擊策略）

```python
def make_inky_ai(pac, blinky):
    def ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
        pivot_x = pac_tx + 2 * pac.dx
        pivot_y = pac_ty + 2 * pac.dy
        return 2 * pivot_x - blinky.tx, 2 * pivot_y - blinky.ty
    return ai
```

Inky 的目標計算分兩步：

1. 計算小精靈前方 2 格作為「中間點」（`pivot`）
2. 將 Blinky 的位置對這個中間點做**對稱反射**

幾何意義：如果把小精靈前方 2 格和 Blinky 的位置連成一條線，Inky 的目標就是這條線延伸後的另一端。這讓 Inky 和 Blinky 形成夾擊態勢。

```
Blinky ──── 中間點 ──── Inky 的目標
              ↑
          小精靈前方 2 格
```

### Clyde（近則逃、遠則追）

```python
def make_clyde_ai(clyde, corner_x: float, corner_y: float):
    def ai(pac_tx: float, pac_ty: float) -> tuple[float, float]:
        dist2 = (clyde.tx - pac_tx) ** 2 + (clyde.ty - pac_ty) ** 2
        if dist2 > 64:   # 超過 8 格距離
            return pac_tx, pac_ty
        return corner_x, corner_y
    return ai
```

Clyde 的行為最特別：

- 距離小精靈**超過 8 格**時：直接追小精靈（和 Blinky 一樣）
- 距離小精靈**8 格以內**時：逃往地圖左下角（`corner_x=1, corner_y=ROWS-2`）

這讓 Clyde 看起來「不太聰明」——明明快追到了卻突然逃跑，不斷在追逐和逃離之間循環。

> **`dist2 > 64` 為什麼等於 8 格？**
> 距離平方 `dist² = 8² = 64`。直接比較平方值省去了開根號，結果等同於判斷距離是否超過 8 格。

### 設定 AI

在 `App.reset_game` 中，為各幽靈指派對應的 AI：

```python
self.ghosts = [Ghost(i) for i in range(4)]
self.ghosts[0].ai_fn = chase_ai                               # Blinky
self.ghosts[1].ai_fn = make_pinky_ai(self.pac)                # Pinky
self.ghosts[2].ai_fn = make_inky_ai(self.pac, self.ghosts[0]) # Inky
self.ghosts[3].ai_fn = make_clyde_ai(self.ghosts[3], 1.0, float(ROWS - 2))  # Clyde
```

---

## 第七章：幽靈繪製

幽靈的形狀是用像素逐格手繪的：

```python
def draw(self):
    px = MAZE_X + int(self.tx * TS)
    py = MAZE_Y + int(self.ty * TS)
    col = COL_SCARED if self.scared else COL_GHOST[self.idx]
    for dy in range(1, 7):
        for dx in range(1, 7):
            if dy <= 3:
                # 上半部：半圓形
                if (dx - 3.5) ** 2 + (dy - 3.5) ** 2 <= 3.5**2:
                    pyxel.pset(px + dx, py + dy, col)
            else:
                # 下半部：整排（波浪裙擺）
                pyxel.pset(px + dx, py + dy, col)
    if not self.scared:
        pyxel.pset(px + 2, py + 3, 7)   # 左眼
        pyxel.pset(px + 5, py + 3, 7)   # 右眼
```

繪製邏輯：

- 上半部（`dy <= 3`）：判斷像素是否在以 (3.5, 3.5) 為圓心、半徑 3.5 的圓內，形成半圓頭頂
- 下半部（`dy > 3`）：全部填滿，形成方形裙擺（原版幽靈的波浪裙擺在這個解析度下簡化為直邊）
- 受驚時：全部換成 `COL_SCARED`（藍色），並且不繪製眼睛

---

## 第八章：遊戲狀態機

### 狀態定義

遊戲有四個狀態：

| 狀態 | 說明 |
|------|------|
| `"play"` | 正常遊玩中 |
| `"dead"` | 玩家剛死亡，等待重置 |
| `"win"` | 所有豆子吃完，顯示勝利畫面 |
| `"gameover"` | 生命歸零，顯示遊戲結束畫面 |

狀態轉移圖：

```
     reset_game()
         │
         ▼
      "play"  ──── 吃完所有豆子 ────► "win"
         │                               │ 90 幀後
    碰到幽靈                         reset_game()
         │
         ▼
      "dead"
         │
    60 幀後
    ┌────┴────┐
    │         │
lives > 0  lives = 0
    │         │
reset_pos()   ▼
    │       "gameover"
    ▼          │ 120 幀後
  "play"    reset_game()
```

### App.update 主邏輯

```python
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
                g.scared_timer = 150   # 150 幀 = 5 秒

        for g in self.ghosts:
            g.update(self.pac.tx, self.pac.ty)

        # 碰撞偵測：小精靈 vs 幽靈
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
```

### 碰撞偵測

```python
if abs(self.pac.tx - g.tx) < 0.8 and abs(self.pac.ty - g.ty) < 0.8:
```

這用的是「軸對齊邊界框（AABB）」碰撞偵測，只需比較兩個方向的座標差是否都小於門檻值。門檻 0.8 格讓碰撞判定有一定容錯，即使小精靈和幽靈沒有完全重疊也會觸發。

**碰撞結果：**
- 幽靈**受驚中**：幽靈被吃掉（`g.reset()` 回到出生點），玩家加 200 分
- 幽靈**正常狀態**：玩家死亡（`lives -= 1`，進入 `"dead"` 狀態）

### build_dots 與豆子字典

```python
def build_dots(self):
    self.dots = {}
    for ty in range(ROWS):
        for tx in range(COLS):
            c = MAZE[ty][tx]
            if c == TILE_DOT:
                self.dots[(tx, ty)] = "dot"
            elif c == TILE_POWER:
                self.dots[(tx, ty)] = "power"
```

豆子用字典存放，以格子座標 `(tx, ty)` 為 key。字典查詢的時間複雜度是 O(1)，每幀的豆子碰撞檢查只需要一次字典查詢，不需要遍歷所有豆子。吃掉豆子用 `dict.pop(key)` 同時查詢並移除。當 `self.dots` 為空時代表全部吃完，觸發勝利。

---

## 第九章：繪圖系統

### App.draw 主邏輯

```python
def draw(self):
    pyxel.cls(COL_BG)   # 清空畫面

    # UI：分數與生命
    pyxel.text(4, 4, f"SCORE:{self.score}", COL_TEXT)
    pyxel.text(110, 4, f"LIVES:{self.lives}", COL_TEXT)

    # 地圖牆壁
    for ty in range(ROWS):
        for tx in range(COLS):
            px = MAZE_X + tx * TS
            py = MAZE_Y + ty * TS
            if MAZE[ty][tx] == TILE_WALL:
                pyxel.rect(px, py, TS, TS, COL_WALL)

    # 豆子
    for (tx, ty), kind in self.dots.items():
        px = MAZE_X + tx * TS + 3
        py = MAZE_Y + ty * TS + 3
        if kind == "dot":
            pyxel.pset(px, py, COL_DOT)
        else:
            if (pyxel.frame_count // 8) % 2 == 0:
                pyxel.circ(px, py, 2, COL_PAC)

    # 幽靈和小精靈
    for g in self.ghosts:
        g.draw()

    if self.state != "dead" or self.state_timer > 30:
        self.pac.draw()

    # 覆蓋文字
    if self.state == "win":
        pyxel.text(55, 88, "YOU WIN!", COL_PAC)
    elif self.state == "gameover":
        pyxel.text(48, 88, "GAME OVER", 8)
```

幾個值得注意的細節：

**能量豆閃爍效果**

```python
if (pyxel.frame_count // 8) % 2 == 0:
    pyxel.circ(px, py, 2, COL_PAC)
```

`pyxel.frame_count` 是從遊戲開始的累積幀數。整除 8 後取餘數為 0 或 1，讓能量豆每 8 幀切換一次顯示狀態，達到閃爍效果。

**死亡動畫**

```python
if self.state != "dead" or self.state_timer > 30:
    self.pac.draw()
```

在死亡狀態的前 30 幀仍然顯示小精靈，後 30 幀隱藏，形成閃爍消失的效果。

---

## 延伸挑戰

以下挑戰可以讓你更深入了解遊戲各個系統：

### 入門

- [ ] 調整小精靈速度（`Pacman.speed`）和幽靈速度（`Ghost.speed`），觀察遊戲難度變化
- [ ] 修改能量豆讓幽靈受驚的持續時間（`g.scared_timer = 150`），改成 300 或 60
- [ ] 加入「吃驚嚇幽靈連殺加成」：第一隻 200 分、第二隻 400 分、第三隻 800 分、第四隻 1600 分

### 中階

- [ ] 實作**隧道穿越**：在地圖左右兩側設計開口（將邊緣的牆壁改為 `TILE_EMPTY`），讓小精靈和幽靈能從一側穿越到另一側
- [ ] 增加**生命顯示圖示**：在畫面底部用小小精靈圖案代替數字顯示剩餘生命
- [ ] 實作**幽靈眼睛**：被吃掉後幽靈只剩眼睛，以高速回到出生點後復活

### 進階

- [ ] 加入**關卡系統**：每過一關速度加快、受驚時間縮短
- [ ] 實作**散步模式（Scatter Mode）**：幽靈每隔一段時間切換到各自負責的角落徘徊，再切回追逐模式（原版 Pac-Man 的完整 AI 行為）
- [ ] 加入**音效**：用 `pyxel.sounds` 加入吃豆聲、死亡音效、能量豆音效

---

## 附錄：常用 Pyxel API 速查

| 函式 | 用途 |
|------|------|
| `pyxel.init(w, h, title, fps)` | 初始化視窗 |
| `pyxel.run(update, draw)` | 啟動遊戲迴圈 |
| `pyxel.cls(col)` | 清空畫面 |
| `pyxel.pset(x, y, col)` | 繪製單一像素 |
| `pyxel.rect(x, y, w, h, col)` | 繪製實心矩形 |
| `pyxel.circ(x, y, r, col)` | 繪製實心圓形 |
| `pyxel.text(x, y, s, col)` | 繪製文字 |
| `pyxel.btn(key)` | 按鍵持續按住中？ |
| `pyxel.btnp(key)` | 按鍵剛按下？ |
| `pyxel.frame_count` | 累積幀數 |
| `pyxel.quit()` | 結束遊戲 |
