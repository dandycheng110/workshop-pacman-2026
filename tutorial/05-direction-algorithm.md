[< 上一章：小精靈——吃豆子與動畫](04-pacman.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：四隻幽靈的 AI >](06-ghost-ai.md)
---

## 第五章：方向選擇演算法

### 問題描述

每次幽靈抵達一個新格子，都需要從周圍最多三個可走方向中選出「最佳」的一個：

- **追逐模式**：選讓下一格**最接近**目標的方向
- **受驚模式**：選讓下一格**最遠離**目標的方向

這個邏輯封裝在 `pick_direction()` 函式中，四隻幽靈共用：

```python
_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # 右、左、下、上

def pick_direction(
    itx: int, ity: int,        # 幽靈目前所在格子（整數）
    dx: int, dy: int,          # 幽靈目前移動方向
    target_x: float, target_y: float,  # 目標位置
    flee: bool = False,        # True = 逃離目標
    allow_tunnel: bool = True, # False = 不允許選擇隧道方向
) -> tuple[int, int] | None:
```

### 四個設計規則

1. **不允許 180° 迴轉**：`if ddx == -dx and ddy == -dy: continue`
   原版 Pac-Man 規則——幽靈不能原地掉頭。

2. **幽靈不走隧道**：`allow_tunnel=False` 時，排除超出地圖邊界的方向。
   *為什麼需要這個？* 因為 `is_wall` 為了讓小精靈通過，會把隧道口判定為「可通行」。若不特別排除，幽靈會試圖進入隧道，直到撞到地圖邊界才被迫掉頭。加上此規則能讓幽靈在路徑搜尋時就主動選擇繞道（例如轉向上或向下）。

3. **用距離平方（dist²）取代距離**：`dist2 = (ntx - tx)² + (nty - ty)²`
   比較大小不需要開根號，只用乘法和加法，效能更佳。

4. **score 的符號設計**：
   - 追逐模式（`flee=False`）：`score = dist2`，選最小 score = 最近格子
   - 逃跑模式（`flee=True`）：`score = -dist2`，選最小 score = 最大距離的格子

---

## 🖊️ 練習一：演算法核心邏輯

在實作 `pick_direction` 之前，我們先梳理迴圈內的核心邏輯。請根據註解提示，填入正確的判斷與計算式：

```python
for ddx, ddy in _DIRS:
    # 1. 規則：不允許 180° 迴轉（不可原地掉頭）
    # 提示：新方向 ddx 是否為舊方向 dx 的相反方向？
    if ddx == ___ and ddy == ___:
        continue

    ntx, nty = itx + ddx, ity + ddy

    # 2. 牆壁判斷
    if is_wall(ntx, nty):
        continue

    # 3. 計算下一格到目標的距離平方
    dist2 = (ntx - target_x) ** 2 + (nty - target_y) ** 2

    # 4. 分數設計（追逐選最小 dist2，逃跑選最大 dist2）
    # 提示：為了統一使用「選取最小 score」的程式邏輯，
    # 逃跑（flee=True）時，我們將 dist2 取負號，讓「最大距離」變成「最小分數」。
    score = ___ if flee else ___

    if best_score is None or score < best_score:
        best_score = score
        best = (ddx, ddy)
        ```

        ---

        ## 🖊️ 練習二：實作 pick_direction()

打開 `student_scaffold.py`，找到 `pick_direction()` 裡的 `pass`，用以下框架取代：

```python
def pick_direction(itx, ity, dx, dy, target_x, target_y, flee=False, allow_tunnel=True):
    best = None
    best_score = None
    for ddx, ddy in _DIRS:
        # 規則 1：不允許 180° 迴轉
        if ddx == ___ and ddy == ___:
            continue
        ntx, nty = itx + ddx, ity + ddy
        # 規則 2：幽靈不走隧道
        if not allow_tunnel and not (0 <= ntx < ___ and 0 <= nty < ___):
            continue
        if is_wall(ntx, nty):
            continue
        dist2 = (ntx - target_x) ** 2 + (nty - target_y) ** 2
        # 規則 4：追逐選最近，逃跑選最遠
        score = ___ if flee else ___
        if best_score is None or score < best_score:
            best_score = score
            best = (ddx, ddy)
    return best
```

---

## 🖊️ 練習三：實作 Ghost.update()

你剛學會了 `pick_direction`。現在把它用起來——實作幽靈的移動邏輯。

> **`self.ai_fn` 是什麼？**
> 每隻幽靈都有一個「策略函式」`ai_fn`，呼叫 `self.ai_fn(pac_tx, pac_ty)` 會回傳一個目標格子座標 `(target_x, target_y)`。不同幽靈有不同的追逐策略，詳見第六章；這裡只需知道它的輸入是小精靈的格子座標，輸出是目標位置。

打開 `student_scaffold.py`，找到 `Ghost.update()` 裡的 `pass`，用以下框架取代：

```python
    def update(self, pac_tx, pac_ty):
        # 步驟 1：受驚倒數計時，歸零後恢復正常
        if self.scared and self.scared_timer > 0:
            self.scared_timer -= ___
            if self.scared_timer == ___:
                self.scared = ___

        # 步驟 2：推進格子進度（與 Pacman 相同）
        self.progress += self.speed
        if self.progress >= 1.0:
            new_tx = self.tile_x + self.dx
            new_ty = self.tile_y + self.dy

            # 步驟 3：抵達地圖邊界（隧道口）→ 原地掉頭
            if not (0 <= new_tx < COLS and 0 <= new_ty < ROWS):
                self.dx, self.dy = ___, ___   # 提示：方向取反
                self.progress = 0.0
                return

            # 步驟 4：更新格子座標
            self.tile_x = new_tx
            self.tile_y = new_ty
            self.progress -= 1.0

            # 步驟 5：呼叫 AI 取得目標，再用 pick_direction 選方向
            target = self.ai_fn(___, ___)   # 傳入小精靈的格子座標
            best = pick_direction(
                self.tile_x, self.tile_y, self.dx, self.dy,
                *target, flee=___, allow_tunnel=False
            )
            if best:
                self.dx, self.dy = best
```

完成後執行遊戲，確認幽靈會移動，且吃到能量豆後幽靈會逃離 Pac-Man。

---
[< 上一章：小精靈——吃豆子與動畫](04-pacman.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：四隻幽靈的 AI >](06-ghost-ai.md)
