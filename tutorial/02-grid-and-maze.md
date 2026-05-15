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
COL_TEXT  = 7   # 白色（文字）
```

### 格子座標系統（Tile Coordinate System）

遊戲地圖是由 16×16 像素的「格子（tile）」組成。座標系統有兩層：

| 座標系統 | 單位 | 用途 |
|---------|------|------|
| **格子座標**（`tx`, `ty`）| 格子數 | 地圖邏輯、碰撞判斷 |
| **像素座標**（`px`, `py`）| 像素 | 繪圖 |

兩者之間的轉換：

```python
TS = 16         # Tile Size：每格 16 像素
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

這種「資料即程式碼」的設計讓地圖一目了然——你可以直接看著字串想像出迷宮的形狀。

### 幽靈出生點

遊戲需要知道每隻幽靈的出生格子。做法是在初始化時掃描整張地圖一次，把所有 `TILE_GHOST_SPAWN`（`"4"`）的格子座標收集成一個清單 `GHOST_SPAWNS`。之後建立幽靈時直接用 `GHOST_SPAWNS[idx]` 取得對應幽靈的出生位置，不需要寫死座標。

> **💡 Python 技巧：List Comprehension**
> Python 的 List Comprehension 可以用一行完成「建立空清單、迴圈遍歷、條件判斷、加入清單」四個動作，是 Python 最常用的語法之一。

### tile_at 需要處理的三種情況

存取某格的函式 `tile_at(tx, ty)` 必須依序考慮三種情況：

1. **正常範圍**：座標在地圖內 → 直接查 `MAZE`
2. **超出左右邊界**（`ty` 合法）→ 先確認該列邊緣格子是否為開口；若是（隧道列），回傳對側對應格子；否則視為牆壁
3. **完全超出邊界** → 視為牆壁

> **為何需要隧道邏輯？**
> 本地圖第 6 列和第 9 列兩端是 `"2"`（豆子），形成左右貫通的隧道。
> 當 Pac-Man 走出左側邊界，`tile_at` 應看穿隧道、回傳右側對應格子；
> 一般列（兩端為 `"1"`）則不應穿透，直接視為牆壁。

---

## 🖊️ 練習一：實作 tile_at() 與 is_wall()

打開 `student_scaffold.py`，找到 `tile_at()` 裡的 `return TILE_WALL  # ← 完成…` 這行，
在它**之前**插入隧道邏輯，並完整替換函式體。`is_wall()` 已經為你實作好了，它會直接呼叫 `tile_at`：

```python
def tile_at(tx, ty):
    # 情況一：座標在地圖範圍內，直接查表
    if 0 <= ty < ___ and 0 <= tx < ___:
        return MAZE[___][___]
    # 情況二：ty 合法但 tx 超出水平邊界（可能是隧道列）
    if 0 <= ty < ROWS:
        edge_col = ___ if tx < 0 else ___    # 左側超出 → 取最左欄；右側 → 最右欄
        if MAZE[___][edge_col] != TILE_WALL:  # 邊緣是開口（隧道）才能穿透
            return MAZE[ty][tx % ___]
    # 情況三：完全超出邊界，視為牆壁
    return ___

def is_wall(tx, ty):
    return tile_at(tx, ty) == TILE_WALL
```

完成後執行遊戲，確認 Pac-Man 能順利穿越左右隧道（從左側消失、右側出現）。

---

## 🖊️ 練習二：繪製牆壁與豆子

打開 `student_scaffold.py`，找到 `App.draw()` 裡的 `pass`，用以下框架取代它，再補完空格：

```python
        # 步驟 1：畫牆壁
        # 用兩層 for 迴圈遍歷每個格子，把格子座標轉換成像素座標後畫矩形
        for ty in range(___):
            for tx in range(___):
                px = MAZE_X + tx * ___
                py = MAZE_Y + ty * ___
                if MAZE[___][___] == TILE_WALL:
                    pyxel.rect(px, py, TS, TS, ___)   # 顏色填 COL_WALL

        # 步驟 2：畫豆子
        # self.dots 是字典，key=(tx, ty)，value="dot" 或 "power"
        # 豆子的像素中心在格子左上角往右/下偏移 TS // 2
        for (tx, ty), kind in self.dots.items():
            px = MAZE_X + tx * TS + ___
            py = MAZE_Y + ty * TS + ___
            if kind == "dot":
                pyxel.rect(px - 1, py - 1, 3, 3, ___)   # 3×3 白色小方塊
            else:
                if (pyxel.frame_count // 8) % 2 == 0:    # 每 8 幀閃爍一次
                    pyxel.circ(px, py, 4, ___)            # 半徑 4 的圓
```

完成後執行遊戲，確認迷宮牆壁與豆子都正確顯示。

---

## 🖊️ 練習三：設定起始位置

執行遊戲，你會看到小精靈從畫面中央往左跑、幽靈則完全不見——兩件事都需要在這章修正。

**小精靈**：觀察 MAZE 陣列，找到小精靈的正確起始格子。打開 `student_scaffold.py`，找到 `Pacman.reset()` 裡的佔位值，改成正確的：

```python
self.tile_x = ___   # 提示：MAZE[14] = "1222222112222221"，從左數第幾欄是通道？
self.tile_y = ___   # 小精靈起始列
self.dx = ___       # 起始時靜止，方向設為 0
```

**幽靈出生點清單**：找到 `GHOST_SPAWNS = []`，用 list comprehension 替換它，掃描 MAZE 收集所有 `TILE_GHOST_SPAWN` 的座標：

```python
GHOST_SPAWNS = [
    (tx, ty)
    for ty in range(___)
    for tx in range(___)
    if MAZE[___][___] == ___
]
```

**幽靈初始位置**：找到 `Ghost.reset()`，把暫時佔位座標換成正確的出生點，並加回方向初始化邏輯：

```python
self.tile_x, self.tile_y = GHOST_SPAWNS[___]   # 用幽靈自身的索引取出生座標

# 找第一個可走方向作為初始移動方向（利用剛寫好的 is_wall）
for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
    if not is_wall(self.tile_x + ___, self.tile_y + ___):
        self.dx, self.dy = ___, ___
        break
```

完成後執行遊戲，確認小精靈出現在迷宮通道中，四隻幽靈也出現在中央鬼屋。

---
[< 上一章：事前準備與專案架構](01-getting-started.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：移動與碰撞偵測 >](03-movement-and-collision.md)
