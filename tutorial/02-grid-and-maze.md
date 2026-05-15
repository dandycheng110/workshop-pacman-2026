[< 上一章：事前準備與專案架構](01-getting-started.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：移動與碰撞偵測 >](03-movement-and-collision.md)
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

> **💡 Python 技巧：List Comprehension**
> 上面的程式碼用一行就完成了「建立空清單、迴圈遍歷、條件判斷、加入清單」四個動作。這是 Python 最受歡迎的特徵之一，讓程式碼更簡潔易讀。

之後建立幽靈時，`Ghost(idx)` 直接取 `GHOST_SPAWNS[idx]` 作為初始位置，不需要在類別裡寫死座標。

---
[< 上一章：事前準備與專案架構](01-getting-started.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：移動與碰撞偵測 >](03-movement-and-collision.md)
