[< 上一章：方向選擇演算法](05-direction-algorithm.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：幽靈繪製 >](07-ghost-rendering.md)
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
[< 上一章：方向選擇演算法](05-direction-algorithm.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：幽靈繪製 >](07-ghost-rendering.md)
