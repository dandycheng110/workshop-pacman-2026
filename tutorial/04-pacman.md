[< 上一章：移動與碰撞偵測](03-movement-and-collision.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：方向選擇演算法 >](05-direction-algorithm.md)
---

## 第四章：小精靈——輸入處理與動畫

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
    # 靜止時，若下一方向不是牆壁就開始移動
    if self.dx == 0 and self.dy == 0:
        if not is_wall(self.tile_x + self.next_dx, self.tile_y + self.next_dy):
            self.dx, self.dy = self.next_dx, self.next_dy

    if self.dx != 0 or self.dy != 0:
        self.progress += self.speed
        if self.progress >= 1.0:                          # 抵達下一格
            self.tile_x = (self.tile_x + self.dx) % COLS
            self.tile_y = (self.tile_y + self.dy) % ROWS
            self.progress -= 1.0
            # 嘗試轉彎
            if not is_wall(self.tile_x + self.next_dx, self.tile_y + self.next_dy):
                self.dx, self.dy = self.next_dx, self.next_dy
            # 前方是牆壁就停下
            elif is_wall(self.tile_x + self.dx, self.tile_y + self.dy):
                self.dx, self.dy = 0, 0
                self.progress = 0.0
```

這段邏輯有三個步驟：

1. **靜止啟動**：如果目前沒有在動（`dx == dy == 0`），嘗試用 `next_dx`/`next_dy` 開始移動
2. **推進進度**：每幀增加 `progress`；到達 1.0 代表抵達下一個格子
3. **抵達時轉彎**：如果玩家請求的方向可以走就轉過去；若連目前方向都是牆就停下

轉彎只發生在「剛抵達格子」的瞬間，確保小精靈永遠對齊格子邊界，不會卡入牆角。

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

### Sprite 動畫

小精靈的外觀來自 `main.pyxres` 的 Sprite 圖，儲存在圖片銀行（image bank）0 的 y=0 列，共三格，每格 16×16 像素：

| x 座標 | 動畫幀 |
|--------|--------|
| 0      | 嘴巴全開 |
| 16     | 嘴巴半開 |
| 32     | 嘴巴閉合 |

所有 Sprite 都面向**左方**，向右移動時用負寬度（`w = -16`）水平翻轉。

```python
# 動畫幀序列：開 → 半開 → 閉 → 半開 → 開（每個狀態持續 3 幀）
_PAC_FRAMES = [0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1]

def draw(self):
    self.anim = (self.anim + 1) % 12
    sx = _PAC_FRAMES[self.anim] * 16   # sprite 在圖片銀行中的 x 座標
    px = MAZE_X + int(self.tx * TS)
    py = MAZE_Y + int(self.ty * TS)
    w = -16 if self.dx > 0 else 16    # 向右移動時翻轉
    pyxel.blt(px, py, 0, sx, 0, w, 16, 0)
```

`pyxel.blt(x, y, img, u, v, w, h, colkey)` 的參數：

- `x, y`：螢幕上的繪製起點（格子左上角）
- `img=0`：使用圖片銀行 0
- `u, v`：Sprite 在圖片銀行中的起始座標
- `w, h`：寬高；`w` 為負數時水平翻轉
- `colkey=0`：顏色 0（黑色）視為透明，不繪製

---
[< 上一章：移動與碰撞偵測](03-movement-and-collision.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：方向選擇演算法 >](05-direction-algorithm.md)
