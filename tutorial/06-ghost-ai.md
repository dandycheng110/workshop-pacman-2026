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
        self.tile_x, self.tile_y = GHOST_SPAWNS[self.idx]
        # 掃描四個方向，找到第一個不是牆壁的方向作為初始方向
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if not is_wall(self.tile_x + dx, self.tile_y + dy):
                self.dx, self.dy = dx, dy
                break
        self.progress = 0.0
        self.speed = 0.06
        self.scared = False
        self.scared_timer = 0
```

幽靈透過 `ai_fn` 這個**策略函式（strategy function）**決定目標。這讓四隻幽靈可以共用同一個 `Ghost` 類別，只替換 AI 邏輯。

### 幽靈的 update 邏輯

```python
def update(self, pac_tx, pac_ty):
    # 受驚倒數計時
    if self.scared and self.scared_timer > 0:
        self.scared_timer -= 1
        if self.scared_timer == 0:
            self.scared = False

    self.progress += self.speed
    if self.progress >= 1.0:                          # 抵達下一格
        new_tx = self.tile_x + self.dx
        new_ty = self.tile_y + self.dy
        if not (0 <= new_tx < COLS and 0 <= new_ty < ROWS):
            # 抵達地圖邊界（隧道口）→ 原地掉頭
            self.dx, self.dy = -self.dx, -self.dy
            self.progress = 0.0
            return
        self.tile_x, self.tile_y = new_tx, new_ty
        self.progress -= 1.0
        # 詢問 AI 下一步要往哪走
        target = self.ai_fn(pac_tx, pac_ty)
        best = pick_direction(
            self.tile_x, self.tile_y, self.dx, self.dy,
            *target, flee=self.scared, allow_tunnel=False
        )
        if best:
            self.dx, self.dy = best
```

幽靈的移動和小精靈最大的不同是：幽靈沒有「玩家預輸入」，方向完全由 `ai_fn` 計算得來的目標決定。每次抵達格子，就重新詢問 AI 要往哪走。幽靈也不會穿越隧道（`allow_tunnel=False`）——抵達隧道口（地圖邊界）時直接掉頭。

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

> **💡 Python 技巧：閉包 (Closure) 與工廠函式**
> `make_pinky_ai(pac)` 會回傳一個新的函式。這個內層的 `ai` 函式會「捕捉」並「記住」外層傳進來的 `pac` 物件。這種讓函式擁有「記憶」的技巧在實作不同的 AI 策略時非常強大。

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
# ghost[0] (Blinky) 使用 Ghost.__init__ 預設的 chase_ai，不需額外指派
self.ghosts[1].ai_fn = make_pinky_ai(self.pac)                # Pinky
self.ghosts[2].ai_fn = make_inky_ai(self.pac, self.ghosts[0]) # Inky
self.ghosts[3].ai_fn = make_clyde_ai(self.ghosts[3], 1.0, float(ROWS - 2))  # Clyde
```

---

## 🖊️ 練習：PRIMM 觀察

### [P] 預測

閱讀本章的 `Ghost.update()` 程式碼，回答以下問題，**先不要執行遊戲**：

1. `scared_timer` 從 150 開始，每幀減 1，遊戲以 30 FPS 執行——受驚狀態持續幾秒？
2. 若把 `g.scared_timer = 150` 改成 `300`，玩家體驗有何不同？

### [R] 執行

```bash
uv run python student_scaffold.py
```

吃下地圖四個角的閃爍圓圈（能量豆），觀察幽靈變藍的持續時間，與你的預測比對。

### [I] 研究

對照你在**第五章**寫好的 `Ghost.update()` 實作，回答以下問題：

1. `scared_timer -= 1` 在哪個 `if` 條件的內部？如果把這個條件拿掉，會發生什麼事？
2. 你在步驟 5 傳入了 `flee=self.scared`。當 `self.scared` 為 `True` 時，`pick_direction` 裡的 `score` 公式會變成什麼？為什麼這樣能讓幽靈「逃離」而非「追逐」？
3. `eat_dot()` 回傳字串 `"power"` 而不是直接修改幽靈狀態——從類別設計的角度，這樣做的好處是什麼？

---

## 🖊️ 練習二：實作四隻幽靈的 AI

打開 `student_scaffold.py`，找到四個 AI 函式中的 `# ← 完成第六章練習後...` 行，依照下方框架替換成你的實作：

```python
def chase_ai(pac_tx, pac_ty):
    # Blinky：目標就是小精靈目前的位置
    return ___, ___


def make_pinky_ai(pac):
    def ai(pac_tx, pac_ty):
        # Pinky：目標是小精靈前方 4 格
        return pac_tx + ___ * pac.dx, pac_ty + ___ * pac.dy
    return ai


def make_inky_ai(pac, blinky):
    def ai(pac_tx, pac_ty):
        pivot_x = pac_tx + ___ * pac.dx   # 中間點：小精靈前方 2 格
        pivot_y = pac_ty + ___ * pac.dy
        return 2 * pivot_x - blinky.___, 2 * pivot_y - blinky.___  # 對稱反射
    return ai


def make_clyde_ai(clyde, corner_x, corner_y):
    def ai(pac_tx, pac_ty):
        dist2 = (clyde.___ - pac_tx) ** 2 + (clyde.___ - pac_ty) ** 2
        if dist2 > ___:   # 超過 8 格距離
            return pac_tx, pac_ty
        return ___, ___   # 逃往角落
    return ai
```

完成後執行遊戲，觀察各幽靈的追逐行為是否符合本章說明。

---
[< 上一章：方向選擇演算法](05-direction-algorithm.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：幽靈繪製 >](07-ghost-rendering.md)
