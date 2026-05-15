[< 上一章：顏色、格子與地圖](02-grid-and-maze.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：小精靈——吃豆子與動畫 >](04-pacman.md)
---

## 第三章：移動與碰撞偵測

本章是整個遊戲物理系統的核心，理解這部分才能讀懂小精靈和幽靈的移動邏輯。

### 格子進度模型（Tile-Progress Model）

小精靈和幽靈的位置用**格子進度模型**表示：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `tile_x`, `tile_y` | `int` | 目前所在格子（已到達的整數格子） |
| `dx`, `dy` | `int` | 目前移動方向（-1、0 或 1） |
| `progress` | `float` | 朝下一格已走的比例（0.0 = 剛出發，1.0 = 抵達） |

這三個欄位合成**浮點數格子座標**屬性（`tx`、`ty`），供繪圖使用。以小精靈為例，速度是 `0.08`（每幀進度增加 0.08）。以 30 fps 計算，每秒大約移動 2.4 格。

### 抵達格子時的邏輯

每幀角色的 `progress` 增加 `speed`。當 `progress >= 1.0` 時，代表角色抵達了下一格：

```python
self.progress += self.speed
if self.progress >= 1.0:
    self.tile_x = (self.tile_x + self.dx) % COLS   # 更新整數格子（含隧道穿越）
    self.tile_y = (self.tile_y + self.dy) % ROWS
    self.progress -= 1.0                             # 保留多餘進度，確保平滑
    # ── 此時嘗試轉彎或判斷下一格是否為牆壁 ──
```

方向的切換只發生在「剛到達格子」這個精確時間點，不需要用模糊的容錯區間（`near_grid`）。

### 穿越隧道

本地圖在第 6 列和第 9 列設有隧道開口——這兩列的首尾格子是 `TILE_DOT`（`"2"`）而非 `TILE_WALL`（`"1"`）：

```
row 6: "2222212112122222"   ← 兩端為 '2'，形成左右隧道口
row 9: "2222212112122222"
```

抵達下一格時用取餘數（`%`）實現穿越（小精靈適用）：

```python
self.tile_x = (self.tile_x + self.dx) % COLS
```

當格子座標超出地圖左右邊界，取餘數後會出現在對側，完成穿越。

幽靈的方向選擇傳入 `allow_tunnel=False`，讓幽靈不會主動選擇進入隧道：

```python
best = pick_direction(..., allow_tunnel=False)
```

`tile_at` 在超出水平邊界時會先確認該列是否有隧道開口，再決定要回傳 `TILE_WALL` 還是對側的格子。

這套邏輯的主要目的是：
1. **讓小精靈能穿過隧道**：對小精靈來說，隧道口是可通行的（不是牆）。
2. **讓幽靈「看見」隧道但選擇避開**：我們會在第五章透過參數，讓幽靈在路徑搜尋時主動無視這些超出邊界的出口。

### Pacman 類別

```python
class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tile_x = 9    # 起始格子座標（整數）
        self.tile_y = 14
        self.dx = 0        # 目前移動方向
        self.dy = 0
        self.next_dx = 0   # 玩家請求的下一個方向
        self.next_dy = 0
        self.progress = 0.0  # 朝下一格已走的比例
        self.speed = 0.08
        self.anim = 0      # 動畫計時器
```

> **💡 Python 技巧：類別 (Class) 與 self**
> 在 Python 中，`self` 代表物件實體本身。當我們在類別裡面定義變數（例如 `self.tx`）時，這個變數會跟著這個物件跑。這讓小精靈可以「記得」自己的位置和速度，而不會跟幽靈的資料搞混。

`dx`/`dy` 是**目前方向**，`next_dx`/`next_dy` 是**玩家想要轉的方向**。分開儲存是為了讓玩家可以「提前預輸入」——在還沒到格子中心前就按下方向鍵，到達中心時自動轉彎，手感更流暢。

### 輸入處理

小精靈的移動需要處理鍵盤輸入。我們使用 `next_dx` 與 `next_dy` 來儲存玩家「想要轉的方向」。

> **`btn` vs `btnp`**
> - `pyxel.btn(key)`：按鍵**持續按住**期間每幀都回傳 `True`（適合移動）。
> - `pyxel.btnp(key)`：只在按下的**第一幀**回傳 `True`（適合選單）。

### 轉彎邏輯

小精靈的 `update` 邏輯可以拆解為三個判斷步驟：

1. **靜止啟動**：如果目前方向為 0（沒在動），但玩家有預輸入方向（`next`），且該方向不是牆，就立刻出發。
2. **推進進度**：如果正在移動，則增加 `progress`。當 `progress >= 1.0` 代表抵達了下一個格子。
3. **抵達時轉彎**：這是最關鍵的一步——抵達格子中心點時：
   - 如果玩家請求的 `next` 方向可以走，就轉過去。
   - 否則，如果原本的方向撞牆了，就停下來。

轉彎只發生在「剛抵達格子」的瞬間，確保小精靈永遠對齊格子中心，不會卡進牆角。

---

## 🖊️ 練習一：浮點格子座標（tx / ty）

`Pacman` 和 `Ghost` 都有 `@property tx` 和 `@property ty`，負責將整數格子座標（`tile_x`）加上移動中的插值偏移量，得到供繪圖使用的浮點位置。找到兩個類別裡的這兩個屬性，補完公式：

```python
@property
def tx(self):
    return float(self.___ + self.___ * self.___)  # tile_x + 移動方向 × 進度

@property
def ty(self):
    return float(self.___ + self.___ * self.___)
```

> 三個欄位的意義：`tile_x`/`tile_y` 是目前所在的整數格子；`dx`/`dy` 是移動方向（-1、0 或 1）；`progress` 是朝下一格已走的比例（0.0 到 1.0）。

完成後移動就會變成平滑插值而非跳格。

---

## 🖊️ 練習二：移動邏輯

打開 `student_scaffold.py`，找到 `Pacman.update(self, dots)` 裡的暫時實作，將整個函式體替換成以下框架，再補完每個步驟的程式碼：

```python
def update(self, dots):
    # 步驟 1：讀取鍵盤，更新 next_dx / next_dy
    if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
        self.next_dx, self.next_dy = -1, 0
    elif ___:   # 右鍵條件
        self.next_dx, self.next_dy = ___, ___
    elif ___:   # 上鍵條件
        self.next_dx, self.next_dy = ___, ___
    elif ___:   # 下鍵條件
        self.next_dx, self.next_dy = ___, ___

    # 步驟 2：靜止時，若 next 方向可走就出發
    if self.dx == 0 and self.dy == 0:
        if not is_wall(self.tile_x + ___, self.tile_y + ___):
            self.dx, self.dy = ___, ___

    # 步驟 3：推進格子進度
    if self.dx != 0 or self.dy != 0:
        self.progress += self.speed
        if self.progress >= 1.0:
            self.tile_x = (self.tile_x + self.dx) % ___   # 隧道穿越
            self.tile_y = (self.tile_y + self.dy) % ___
            self.progress -= 1.0
            # 嘗試轉彎，或若前方是牆就停下
            if not is_wall(self.tile_x + ___, self.tile_y + ___):
                self.dx, self.dy = ___, ___
            elif is_wall(self.tile_x + ___, self.tile_y + ___):
                self.dx, self.dy = 0, 0
                self.progress = ___

    # 步驟 4：留給第四章填入
    return None
```

完成後執行遊戲，確認 Pac-Man 可以四方向移動並在牆壁前停下。

---
[< 上一章：顏色、格子與地圖](02-grid-and-maze.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：小精靈——吃豆子與動畫 >](04-pacman.md)
