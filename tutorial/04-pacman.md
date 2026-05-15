[< 上一章：移動與碰撞偵測](03-movement-and-collision.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：方向選擇演算法 >](05-direction-algorithm.md)
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
    px = MAZE_X + int(self.tx * TS)
    py = MAZE_Y + int(self.ty * TS)
    cx, cy, r = px + 4, py + 4, 3
    angle_offset = math.atan2(self.dy, self.dx) if (self.dx != 0 or self.dy != 0) else 0

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
[< 上一章：移動與碰撞偵測](03-movement-and-collision.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：方向選擇演算法 >](05-direction-algorithm.md)
